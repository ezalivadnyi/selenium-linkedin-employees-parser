# -*- coding: utf-8 -*-
import os
import json
import logging
import random
import argparse

import sys
from time import sleep
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

# parse.py —company-url “https://www.linkedin.com/company/mail-ru/“ --selectors selectors.json —out result.json —log out.log
arguments_parser = argparse.ArgumentParser(description='Parse LinkedIn companies employees')
arguments_parser.add_argument('-company-url', type=str, help='Company on profile URL', default='', required=True)
arguments_parser.add_argument('-selectors', type=str, help='Config filename', default='selectors.json', required=True)
arguments_parser.add_argument('-out', type=str, help='Filename for errors, not founded selectors, parsing errors etc', default='result.json', required=True)
arguments_parser.add_argument('-log', type=str, help='Log output file', default='out.log', required=True)
arguments_parser.add_argument('-headless', type=int, choices=[0, 1], help='Show (0) or hide (1) browser window', default=1)
arguments_parser.add_argument('-page', type=int, default=0, help='Start Pagination Page')
args = arguments_parser.parse_args()

logging.basicConfig(filename=args.log, level=logging.DEBUG)


def logging_info(msg):
    print(msg)
    logging.info(msg)


if args.company_url == '':
    logging.debug('-company-url parameter required and cannot be empty!')
    sys.exit('-company-url required and cannot be empty!')

logging_info(f'Reading selectors from {args.selectors}')
selectors_json = open(args.selectors, 'r')
selectors = json.load(selectors_json)
selectors_json.close()


def random_sleep():
    sleep_time = random.randint(selectors['random_sleep_seconds_start'], selectors['random_sleep_seconds_stop'])
    logging.info(f'Sleep random {sleep_time} seconds...')
    sleep(sleep_time)


def send_keys_slowly(element: WebElement, keys: str):
    logging_info(f'Simulate human entering keys speed into WebElement: {element}')
    for key in keys:
        element.send_keys(key)
        sleep(0.3)
    sleep(1)


def scroll_to_element(element: WebElement, element_description: str):
    logging.debug(f"Scrolling to {element_description}")
    # 116 - header height
    browser.execute_script(f"window.scrollTo(0, {element.location['y']} - window.innerHeight/2 + 116)")


def ctrl_plus_tab():
    logging_info('Performing CTRL+TAB')
    actions = ActionChains(browser)
    actions.key_down(Keys.CONTROL).key_down(Keys.TAB).key_up(Keys.TAB).key_up(Keys.CONTROL).perform()


def read_credentials_json():
    logging_info(f'Reading login and password from credentials.json')
    with open('credentials.json') as json_file:
        return json.load(json_file)


def enter_login_and_password():
    credentials = read_credentials_json()
    try:
        logging_info('Trying to find auth form login input')
        input_login = browser.find_element_by_xpath(selectors['auth_input_username'])
        send_keys_slowly(input_login, credentials['login'])
    except NoSuchElementException as e:
        logging.debug(f"Cant' find login input {e}")
        print(f"Cant' find login input")
        sys.exit(f"Cant' find login input {e}")
    except Exception as e:
        logging.debug(f"Unknown Exception {e}")

    try:
        logging_info('Trying to find auth form password input')
        input_password = browser.find_element_by_xpath(selectors['auth_input_password'])
        send_keys_slowly(input_password, credentials['password'])
    except NoSuchElementException as e:
        logging.debug(f"Cant' find password input {e}")
        print(f"Cant' find password input")
        sys.exit(f"Cant' find password input {e}")
    except Exception as e:
        logging.debug(f"Unknown Exception {e}")

    logging_info(f'Login and password entered')


def read_json():
    with open(args.out) as json_file:
        return json.load(json_file)


def write_json(data):
    with open(args.out, 'w') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def parse_location(experience_row: WebElement) -> str:
    try:
        return experience_row.find_element_by_xpath(selectors['profile_position_location']).text
    except NoSuchElementException as e:
        logging.debug(f"Can't find profile_position_location {e}")
        return ''
    except Exception as e:
        logging.debug(f"Unknown Exception {e}")
        return ''


def parse_description(experience_row: WebElement) -> str:
    try:
        description_show_more = experience_row.find_element_by_xpath(selectors['profile_position_description_show_more'])
        scroll_to_element(description_show_more, 'profile_position_description_show_more')
        description_show_more.click()
    except NoSuchElementException as e:
        logging.debug(f"Can't find profile_position_description_show_more (it's normal if description is short) {e}")
    except Exception as e:
        logging.debug(f"Unknown Exception {e}")

    try:
        description_element = experience_row.find_element_by_xpath(selectors['profile_position_description'])
        description_text = description_element.text

        if description_text[-10:] in ['.\nСвернуть', '.\nsee less']:
            description_text = description_text[:-10]

        return description_text
    except NoSuchElementException as e:
        logging.debug(f"Can't find profile_position_description (it's normal) {e}")
        return ''
    except Exception as e:
        logging.debug(f"Unknown Exception {e}")
        return ''


def parse_dates_from_to(experience_row: WebElement) -> {str, str}:
    try:
        date_range = experience_row.find_element_by_xpath(selectors['profile_date_range']).text
        date_range_array = date_range.split('–')
        if len(date_range_array) == 2:
            return {'from': date_range_array[0].strip(), 'to': date_range_array[1].strip()}
        return {'from': '', 'to': ''}
    except NoSuchElementException as e:
        logging.debug(f"Can't find profile_date_range {e}")
        print(f"Can't find profile_date_range")
        return {'from': '', 'to': ''}
    except Exception as e:
        logging.debug(f"Unknown Exception {e}")
        return {'from': '', 'to': ''}


def parse_duration(experience_row: WebElement) -> str:
    try:
        return experience_row.find_element_by_xpath(selectors['profile_date_duration']).text
    except NoSuchElementException as e:
        logging.debug(f"Can't find profile_date_duration {e}")
        print(f"Can't find profile_date_duration")
        return ''
    except Exception as e:
        logging.debug(f"Unknown Exception {e}")
        return ''


def parse_many_position_name(experience_row):
    try:
        return experience_row.find_element_by_xpath(selectors['profile_position_name_for_many_positions']).text
    except NoSuchElementException as e:
        logging.debug(f"Can't find profile_position_name_for_many_positions {e}")
        print(f"Can't find profile_position_name_for_many_positions")
        return ''
    except Exception as e:
        logging.debug(f"Unknown Exception {e}")
        return ''


def parse_one_position_name(experience_row):
    try:
        return experience_row.find_element_by_xpath(selectors['profile_position_name_for_one_position']).text
    except NoSuchElementException as e:
        logging.debug(f"Can't find profile_position_name_for_one_position {e}")
        print(f"Can't find profile_position_name_for_one_position")
        return ''
    except Exception as e:
        logging.debug(f"Unknown Exception {e}")
        return ''


def clean_company_name(name: str) -> str:
    if name[-10:] == ' Full-time':
        return name[:-10]
    return name


def parse_experience_row(experience_row: WebElement) -> dict:
    experience = {'positions': []}

    # ONE POSITION
    try:
        experience['company'] = clean_company_name(experience_row.find_element_by_xpath(
            selectors['profile_company_name_with_one_position']).text)

        experience['duration_summary'] = parse_duration(experience_row)
        position = {
            'name': parse_one_position_name(experience_row),
            'location': parse_location(experience_row),
            'description': parse_description(experience_row),
            'dates': parse_dates_from_to(experience_row)
        }
        position['dates']['duration'] = experience['duration_summary']
        experience['positions'].append(position)
    except NoSuchElementException as e:
        experience['company'] = ''
        logging.debug(f"profile_company_name_with_one_position not found (maybe because it's many positions?) {e}")
    except Exception as e:
        experience['company'] = ''
        logging.debug(f"Unknown Exception {e}")

    # MANY POSITIONS
    try:
        experience['company'] = clean_company_name(experience_row.find_element_by_xpath(
            selectors['profile_company_name_with_many_positions']).text)

        try:
            experience['duration_summary'] = experience_row.find_element_by_xpath(selectors['profile_company_summary_duration_with_many_positions']).text
        except NoSuchElementException as e:
            experience['duration_summary'] = ''
            logging.debug(f"Can't find profile_company_summary_duration_with_many_positions {e}")
            print(f"Can't find profile_company_summary_duration_with_many_positions")
        except Exception as e:
            experience['duration_summary'] = ''
            logging.debug(f"Unknown Exception {e}")

        try:
            for role in experience_row.find_elements_by_xpath(selectors['profile_experience_role_for_many_positions']):
                scroll_to_element(role, 'profile_experience_role_for_many_positions role')
                position = {
                    'name': parse_many_position_name(role),
                    'description': parse_description(role),
                    'dates': parse_dates_from_to(role),
                    'location': parse_location(role)
                }
                position['dates']['duration'] = parse_duration(role)
                experience['positions'].append(position)
        except NoSuchElementException as e:
            experience['positions'].append({
                'name': '', 'location': '', 'description': '',
                'dates': {'from': '', 'to': '', 'duration': ''}
            })
            logging.debug(f"Can't find profile_experience_role_for_many_positions {e}")
        except Exception as e:
            logging.debug(f"Unknown Exception {e}")
            experience['positions'].append({
                'name': '', 'location': '', 'description': '',
                'dates': {'from': '', 'to': '', 'duration': ''}
            })

    except NoSuchElementException as e:
        logging.debug(f'profile_company_name_with_many_positions not found (its normal!) {e}')
    except Exception as e:
        logging.debug(f"Unknown Exception {e}")

    return experience


def parse_profile():
    employee = {'experience': []}
    try:
        employee['name'] = browser.find_element_by_xpath(selectors['profile_name']).text
    except NoSuchElementException as e:
        employee['name'] = ''
        logging.debug(f"Can't find profile_name {e}")
        print(f"Can't find profile_name")
    except Exception as e:
        employee['name'] = ''
        logging.debug(f"Unknown Exception {e}")

    try:
        profile_about_show_more_button = browser.find_element_by_xpath(selectors['profile_about_show_more_button'])
        scroll_to_element(profile_about_show_more_button, 'profile_about_show_more_button')
        profile_about_show_more_button.click()
    except NoSuchElementException as e:
        logging.debug(f"profile_about_show_more_button not found (it's normal if not about or about is short) {e}")
    except Exception as e:
        logging.debug(f"Unknown Exception {e}")

    try:
        employee['position'] = browser.find_element_by_xpath(selectors['profile_position']).text
    except NoSuchElementException as e:
        employee['position'] = ''
        logging.debug(f"Can't find profile_position {e}")
        print(f"Can't find profile_position")
    except Exception as e:
        employee['position'] = ''
        logging.debug(f"Unknown Exception {e}")

    try:
        employee['about'] = browser.find_element_by_xpath(selectors['profile_about']).text
    except NoSuchElementException as e:
        employee['about'] = ''
        logging.debug(f"Can't find profile_about (it may be empty and not exist) {e}")
    except Exception as e:
        employee['about'] = ''
        logging.debug(f"Unknown Exception {e}")

    try:
        show_more_experience_button = browser.find_element_by_xpath(selectors['profile_show_more_experience_button'])
        scroll_to_element(show_more_experience_button, 'profile_show_more_experience_button')
        show_more_experience_button.click()
    except NoSuchElementException as e:
        logging.debug(f"profile_show_more_experience_button not found (it's normal if little positions) {e}")
    except Exception as e:
        logging.debug(f"Unknown Exception {e}")

    try:
        experience_rows = browser.find_elements_by_xpath(selectors['profile_experience_rows'])
        for experience_row in experience_rows:

            scroll_to_element(experience_row, 'profile_experience_rows row')
            try:
                show_more_role_button = experience_row.find_element_by_xpath(selectors['profile_show_more_role_button'])
                scroll_to_element(show_more_role_button, 'profile_show_more_role_button')
                show_more_role_button.click()
                scroll_to_element(experience_row, 'profile_experience_rows row')
            except NoSuchElementException as e:
                logging.debug(f"profile_show_more_role_button not found (it's normal) {e}")
            except Exception as e:
                logging.debug(f"Unknown Exception {e}")

            parsed_experience = parse_experience_row(experience_row)

            employee['experience'].append(parsed_experience)
    except NoSuchElementException as e:
        logging.debug(f"Can't find profile_experience_rows {e}")
        print(f"Can't find profile_experience_rows")
    except Exception as e:
        logging.debug(f"Unknown Exception {e}")

    return employee


chrome_options = Options()
chrome_options.add_argument("--user-data-dir=chrome-data")
chrome_options.add_argument('--no-sandbox')
if args.headless == 1:
    chrome_options.add_argument("--headless")
browser = webdriver.Chrome(
    executable_path=os.getenv('CHROME_DRIVER', os.path.join(os.path.dirname(__file__), 'chromedriver')),
    options=chrome_options
)
browser.set_window_size(1280, 1024)
logging_info(f'GET {args.company_url}')
browser.get(args.company_url)
random_sleep()

# Modal auth (page visible)
# Company page shown but "view all employees" wants sign up (auth modal show at the right bottom)
skip_sign_up_form_sign_in_link = True
try:
    logging_info('Trying to find MODAL with sign up/in links and click on sign in link')
    modal_sign_in_button = browser.find_element_by_xpath(selectors['modal_sign_in_button'])
    scroll_to_element(modal_sign_in_button, 'modal_sign_in_button')
    modal_sign_in_button.click()
    random_sleep()
    enter_login_and_password()
    try:
        modal_sign_in_button = browser.find_element_by_xpath('//button[@type="submit"]')
        scroll_to_element(modal_sign_in_button, 'modal_sign_in_button')
        modal_sign_in_button.click()
    except NoSuchElementException as e:
        print('//button[@type="submit"] not found')
        try:
            logging_info('Trying click on auth_submit_button')
            auth_submit_button = browser.find_element_by_xpath(selectors['auth_submit_button'])
            scroll_to_element(auth_submit_button, 'auth_submit_button')
            auth_submit_button.click()
        except NoSuchElementException as e:
            logging_info(f"Can't find auth_submit_button {e}")
            sys.exit(f"Can't find auth_submit_button {e}")
        except Exception as e:
            logging.debug(f"Unknown Exception {e}")

    except Exception as e:
        logging.debug(f"Unknown Exception {e}")

except NoSuchElementException as e:
    skip_sign_up_form_sign_in_link = False
    logging.debug(f'Modal sign-in not found. Already authenticated? {e}')
except Exception as e:
    logging.debug(f"Unknown Exception {e}")

if not skip_sign_up_form_sign_in_link:
    # SIGN UP PAGE (Company not visible, page nothing shown and want auth from start)
    try:
        logging_info('Trying to find SIGN UP FORM with sign in link')
        sign_up_form_sign_in_link = browser.find_element_by_xpath(selectors['sign_up_form_sign_in_link'])
        scroll_to_element(sign_up_form_sign_in_link, 'sign_up_form_sign_in_link')
        sign_up_form_sign_in_link.click()
        random_sleep()
        enter_login_and_password()
        try:
            logging_info('Click on auth submit button')
            input_submit_sign_in = browser.find_element_by_xpath(selectors['input_submit_sign_in'])
            scroll_to_element(input_submit_sign_in, 'input_submit_sign_in')
            input_submit_sign_in.click()
        except NoSuchElementException as e:
            logging.debug(f"input_submit_sign_in not found! Can't sign in! {e}")
            sys.exit(f"Can't find input_submit_sign_in {e}")
        except Exception as e:
            logging.debug(f"Unknown Exception {e}")
    except NoSuchElementException as e:
        logging.debug(f'Sign up form with sign in link not found. {e}')

logging_info('Signed In (or already authorized with cookies) successfully')
random_sleep()

try:
    input__email_verification_pin = browser.find_element_by_xpath(selectors['input__email_verification_pin'])
    pin = input(f"Founded input__email_verification_pin! Let's do a quick verification. The login attempt seems "
                f"suspicious. To finish signing in please enter the verification code we sent to your email address:")
    send_keys_slowly(input__email_verification_pin, pin)
    try:
        email_pin_submit_button = browser.find_element_by_xpath(selectors['email-pin-submit-button'])
        scroll_to_element(email_pin_submit_button, 'email-pin-submit-button')
        email_pin_submit_button.click()
        logging_info(f"Clicked on email-pin-submit-button")
        random_sleep()
    except NoSuchElementException as e:
        logging.debug(f"email-pin-submit-button not found. Can't enter pin. Fix selectors.json {e}")
        sys.exit(f"email-pin-submit-button not found! Can't enter pin. Fix selectors.json")
    except Exception as e:
        logging.debug(f"Unknown Exception {e}")
except NoSuchElementException as e:
    logging.debug(f"Can't find input__email_verification_pin (maybe it's normal)")

try:
    messaging_modal_expanded = browser.find_element_by_xpath(selectors['messaging_modal_expanded'])
    scroll_to_element(messaging_modal_expanded, 'messaging_modal_expanded')
    messaging_modal_expanded.click()
    logging_info(f"Messaging modal was closed")
except NoSuchElementException as e:
    logging.debug(f"messaging_modal_expanded not found (it's normal, maybe it was already closed)")
except Exception as e:
    logging.debug(f"Unknown Exception {e}")

try:
    for conversation_window in browser.find_elements_by_xpath(selectors['close_conversation_window']):
        scroll_to_element(conversation_window, 'conversation_window')
        conversation_window.click()
        logging_info(f"{conversation_window.text} closed")
except NoSuchElementException as e:
    logging.debug(f"close_conversation_window not found (it's normal, maybe they not exists)")
except Exception as e:
    logging.debug(f"Unknown Exception {e}")


if '/company/' in args.company_url:
    logging_info(f"Founded /company/ in url, assume this is company url")
    try:
        company_name = browser.find_element_by_xpath(selectors['company_name']).text
        logging_info(f'Extracted company name {company_name}')
    except NoSuchElementException as e:
        logging.debug(f"Can't find company_name {e}")
        sys.exit(f"Can't find company_name {e}")
    except Exception as e:
        logging.debug(f"Unknown Exception {e}")

    if not os.path.exists(f'{os.getcwd()}/{args.out}'):
        write_json({
            'company': company_name,
            'employees': []
        })

    try:
        link_to_all_employees = browser.find_element_by_xpath(selectors['link_to_all_employees'])
        scroll_to_element(link_to_all_employees, 'link_to_all_employees')
        logging_info(f'Click on link "See all employees"\n')
        link_to_all_employees.click()
        random_sleep()
    except NoSuchElementException as e:
        logging.debug(f"Can't find link_to_all_employees {e}")
        sys.exit(f"Can't find link_to_all_employees {e}")
    except Exception as e:
        logging.debug(f"Unknown Exception {e}")

    if args.page != 0:
        custom_pagination_link = f"{browser.current_url}&page={args.page}"
        logging_info(f"Received argument pagination page {args.page}.\nOpening custom link: {custom_pagination_link}")
        browser.get(custom_pagination_link)

    last_page = False
    while not last_page:
        # SEE ALL EMPLOYEES.
        try:
            global_footer = browser.find_element_by_xpath(selectors['global_footer'])
            scroll_to_element(global_footer, 'global_footer')
        except NoSuchElementException as e:
            logging.debug(f"Can't find global_footer")
            sys.exit(f"Can't find global_footer")
        except Exception as e:
            logging.debug(f"Unknown Exception {e}")

        try:
            page_number = browser.find_elements_by_xpath(selectors['employees_pagination_current'])[0].text
            logging_info(f"Current pagination page: {page_number}\n")
        except NoSuchElementException as e:
            logging.debug(f"Can't find employees_pagination_current!")
        except Exception as e:
            logging.debug(f"Unknown Exception {e}")

        try:
            profiles = browser.find_elements_by_xpath(selectors['profiles_list'])
            for profile in profiles:
                # Profile links added to html only when visible on screen
                scroll_to_element(profile, f'next profiles_list profile')
                try:
                    profile_link = profile.find_element_by_xpath(selectors['profile_link'])

                    try:
                        actor_name = profile_link.find_element_by_xpath(selectors['profile_link_actor_name']).text
                    except NoSuchElementException as e:
                        logging.debug(f"Can't find profile_link_actor_name!")
                        sys.exit(f"Can't find profile_link_actor_name!")
                    except Exception as e:
                        logging.debug(f"Unknown Exception {e}")

                    try:
                        profile_link_position_name = profile.find_element_by_xpath(selectors['profile_link_position_name']).text
                    except NoSuchElementException as e:
                        profile_link_position_name = ''
                        logging.debug(f"Can't find profile_link_position_name!")
                        print(f"Can't find profile_link_position_name!")
                    except Exception as e:
                        logging.debug(f"Unknown Exception {e}")

                    if actor_name == 'LinkedIn Member' or actor_name == 'Участник LinkedIn':
                        logging_info(f"x profile {profile_link_position_name} has limited visibility. Skip iteration.")
                        continue
                    else:
                        profile_link_href = profile_link.get_attribute('href')
                        json_data = read_json()
                        if not any(employee['url'] == profile_link_href for employee in json_data['employees']):
                            logging_info(f'\n-> Parsing {profile_link_href}')
                            profile_link.send_keys(Keys.CONTROL + Keys.RETURN)
                            browser.switch_to.window(browser.window_handles[-1])
                            random_sleep()

                            # TODO: NEED CHECK FOR CAPTCHA IN NEW PROFILE TAB
                            employee = parse_profile()
                            employee['url'] = profile_link_href
                            json_data['employees'].append(employee)
                            write_json(json_data)
                            logging_info(f'{actor_name} [{employee["position"]}] appended to {args.out}')

                            browser.close()
                            browser.switch_to.window(browser.window_handles[0])
                            sleep(1)
                        else:
                            logging_info(f'x Skip {profile_link_href} ({actor_name}) - already exist in {args.out}.')
                except NoSuchElementException as e:
                    logging.debug(f"Can't find profile_link. Maybe it is because show empty+'try free trial propose' {e}")
                    print(f"Can't find profile_link. Maybe it is because show empty+'try free trial propose'")
                except Exception as e:
                    logging.debug(f"Unknown Exception {e}")

        except NoSuchElementException as e:
            logging.debug(f"Can't find profiles_list {e}")
            sys.exit(f"Can't find profiles_list {e}")
        except Exception as e:
            logging.debug(f"Unknown Exception {e}")

        try:
            # TODO: NEED CHECK FOR CAPTCHA IN NEW SEARCH PAGINATION PAGE
            pagination_next_button = browser.find_element_by_xpath(selectors['employees_pagination_next'])
            scroll_to_element(pagination_next_button, 'employees_pagination_next')
            if pagination_next_button.is_enabled():
                logging_info('\nClick on next pagination button')
                pagination_next_button.click()
                random_sleep()
            else:
                logging_info('Pagination next button not found. Assume this is the last page.')
                last_page = True

        except NoSuchElementException as e:
            logging.debug(f"Can't find employees_pagination_next. Exit.")
            sys.exit(f"Can't find employees_pagination_next. Exit.")
        except Exception as e:
            logging.debug(f"Unknown Exception {e}")

elif '/in/' in args.company_url:
    logging_info(f"Founded /in/ in url, assume this is single profile")
    employee = parse_profile()
    employee['url'] = args.company_url
    logging_info(f'CHECK IF PROFILE {args.company_url} EXIST IN {args.out}')
    logging_info(f'Reading data from {args.out}')
    json_data = read_json()
    if not any(emp['url'] == args.company_url for emp in json_data['employees']):
        json_data['employees'].append(employee)
        write_json(json_data)
        logging_info(f"{employee['name']} not founded in {args.out} and appended as new")
    else:
        logging_info(f"{employee['name']} founded in {args.out} and rewrite existed employee data")
        for index, emp in enumerate(json_data['employees']):
            if emp['url'] == args.company_url:
                json_data['employees'][index] = employee
        write_json(json_data)
browser.close()
browser.quit()
