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
arguments_parser.add_argument('-company-url', type=str, help='Company URL', default='')
arguments_parser.add_argument('-selectors', type=str, help='Config filename', default='selectors.json')
arguments_parser.add_argument('-out', type=str, help='Filename for errors, not founded selectors, parsing errors etc', default='result.json')
arguments_parser.add_argument('-log', type=str, help='Company URL', default='out.log')
arguments_parser.add_argument('-login', type=str, help='LinkedIn Login', default='', required=True)
arguments_parser.add_argument('-password', type=str, help='LinkedIn Password', default='', required=True)
args = arguments_parser.parse_args()

logging.basicConfig(filename=args.log, level=logging.DEBUG)

if args.company_url == '':
    logging.debug('-company-url parameter required and cannot be empty!')
    sys.exit('-company-url required and cannot be empty!')

logging.info(f'Reading selectors from {args.selectors}')
selectors_json = open(args.selectors, 'r')
selectors = json.load(selectors_json)
selectors_json.close()


def random_sleep():
    sleep_time = random.randint(selectors['random_sleep_seconds_start'], selectors['random_sleep_seconds_stop'])
    logging.info(f'Sleep {sleep_time} seconds...')
    print(f'Sleep {sleep_time} seconds...')
    sleep(sleep_time)


def send_keys_slowly(element: WebElement, keys: str):
    logging.info(f'Simulate human entering keys speed into WebElement: {element}')
    for key in keys:
        element.send_keys(key)
        sleep(0.3)
    sleep(1)


def scroll_to_element(element: WebElement):
    logging.info(f"Scrolling to WebElement {element} \ntag_name: {element.tag_name} text: {element.text}")
    actions = ActionChains(browser)
    actions.move_to_element(element).perform()


def ctrl_plus_tab():
    actions = ActionChains(browser)
    actions.key_down(Keys.CONTROL).key_down(Keys.TAB).key_up(Keys.TAB).key_up(Keys.CONTROL).perform()


def enter_login_and_password():
    try:
        logging.info('Trying to find auth form login input')
        input_login = browser.find_element_by_xpath(selectors['auth_input_username'])
        send_keys_slowly(input_login, args.login)
    except NoSuchElementException as e:
        logging.debug(f"Cant' find login input {e}")
        sys.exit(f"Cant' find login input {e}")

    try:
        logging.info('Trying to find auth form password input')
        input_password = browser.find_element_by_xpath(selectors['auth_input_password'])
        send_keys_slowly(input_password, args.password)
    except NoSuchElementException as e:
        logging.debug(f"Cant' find password input {e}")
        sys.exit(f"Cant' find password input {e}")

    print(f'Login and password entered')
    logging.info(f'Login and password entered')


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


def parse_description(experience_row: WebElement) -> str:
    try:
        description_element = experience_row.find_element_by_xpath(selectors['profile_position_description'])
        scroll_to_element(description_element)
        description_text = description_element.text

        try:
            description_element.find_element_by_xpath(selectors['profile_position_description_show_more']).click()
            description_text = description_text[:-10]
        except NoSuchElementException as e:
            logging.debug(f"Can't find profile_position_description_show_more (it's normal if description is short) {e}")

        return description_text
    except NoSuchElementException as e:
        logging.debug(f"Can't find profile_position_description (it's normal) {e}")
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
        return {'from': '', 'to': ''}


def parse_duration(experience_row: WebElement) -> str:
    try:
        return experience_row.find_element_by_xpath(selectors['profile_date_duration']).text
    except NoSuchElementException as e:
        logging.debug(f"Can't find profile_date_duration {e}")
        return ''


def parse_many_position_name(experience_row):
    try:
        return experience_row.find_element_by_xpath(selectors['profile_position_name_for_many_positions']).text
    except NoSuchElementException as e:
        logging.debug(f"Can't find profile_position_name_for_many_positions {e}")
        return ''


def parse_one_position_name(experience_row):
    try:
        return experience_row.find_element_by_xpath(selectors['profile_position_name_for_one_position']).text
    except NoSuchElementException as e:
        logging.debug(f"Can't find profile_position_name_for_one_position {e}")
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
        logging.info(f"profile_company_name_with_one_position not found {e}")

    # MANY POSITIONS
    try:
        experience['company'] = clean_company_name(experience_row.find_element_by_xpath(
            selectors['profile_company_name_with_many_positions']).text)

        try:
            experience['duration_summary'] = experience_row.find_element_by_xpath(selectors['profile_company_summary_duration_with_many_positions']).text
        except NoSuchElementException as e:
            experience['duration_summary'] = ''
            logging.debug(f"Can't find profile_company_summary_duration_with_many_positions {e}")

        try:
            for role in experience_row.find_elements_by_xpath(selectors['profile_experience_role_for_many_positions']):
                scroll_to_element(role)
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

    except NoSuchElementException as e:
        logging.info(f'profile_company_name_with_many_positions not found {e}')

    return experience


def parse_profile():
    employee = {'experience': []}
    try:
        employee['name'] = browser.find_element_by_xpath(selectors['profile_name']).text
    except NoSuchElementException as e:
        employee['name'] = ''
        logging.debug(f"Can't find profile_name {e}")

    try:
        profile_about_show_more_button = browser.find_element_by_xpath(selectors['profile_about_show_more_button'])
        scroll_to_element(profile_about_show_more_button)
        profile_about_show_more_button.click()
    except NoSuchElementException as e:
        logging.info(f"profile_about_show_more_button not found (it's normal if not about or about is short) {e}")

    try:
        employee['position'] = browser.find_element_by_xpath(selectors['profile_position']).text
    except NoSuchElementException as e:
        employee['position'] = ''
        logging.debug(f"Can't find profile_position {e}")

    try:
        employee['about'] = browser.find_element_by_xpath(selectors['profile_about']).text
    except NoSuchElementException as e:
        employee['about'] = ''
        logging.debug(f"Can't find profile_about (it may be empty and not exist) {e}")

    try:
        show_more_experience_button = browser.find_element_by_xpath(selectors['profile_show_more_experience_button'])
        scroll_to_element(show_more_experience_button)
        show_more_experience_button.click()
    except NoSuchElementException as e:
        logging.info(f"profile_show_more_experience_button not found (it's normal if little positions) {e}")

    try:
        experience_rows = browser.find_elements_by_xpath(selectors['profile_experience_rows'])
        for experience_row in experience_rows:

            scroll_to_element(experience_row)
            try:
                show_more_role_button = experience_row.find_element_by_xpath(selectors['profile_show_more_role_button'])
                scroll_to_element(show_more_role_button)
                show_more_role_button.click()
                scroll_to_element(experience_row)
            except NoSuchElementException as e:
                logging.info(f"profile_show_more_role_button not found (it's normal) {e}")

            parsed_experience = parse_experience_row(experience_row)

            employee['experience'].append(parsed_experience)
    except NoSuchElementException as e:
        logging.debug(f"Can't find profile_experience_rows s {e}")

    return employee


chrome_options = Options()
chrome_options.add_argument("--user-data-dir=chrome-data")
#chrome_options.add_argument("--headless")
browser = webdriver.Chrome(
    executable_path=os.getenv('CHROME_DRIVER', os.path.join(os.path.dirname(__file__), 'chromedriver')),
    options=chrome_options
)
browser.set_window_size(1280, 1024)
logging.info(f'Get request to company url: {args.company_url}')
browser.get(args.company_url)
random_sleep()

# Modal auth (page visible)
# Company page shown but "view all employees" wants sign up (auth modal show at the right bottom)
try:
    logging.info('Trying to find MODAL with sign up/in links and click on sign in link')
    browser.find_element_by_xpath(selectors['modal_sign_in_button']).click()
    random_sleep()
    enter_login_and_password()
    try:
        logging.info('Click on auth submit button')
        browser.find_element_by_xpath(selectors['auth_submit_button']).click()
    except NoSuchElementException as e:
        logging.info(f"Can't find auth_submit_button {e}")
        sys.exit(f"Can't find auth_submit_button {e}")
except NoSuchElementException as e:
    logging.debug(f'Modal sign-in not found. {e}')

# SIGN UP PAGE (Company not visible, page nothing shown and want auth from start)
try:
    logging.info('Trying to find SIGN UP FORM with sign in link')
    browser.find_element_by_xpath(selectors['sign_up_form_sign_in_link']).click()
    random_sleep()
    enter_login_and_password()
    try:
        logging.info('Click on auth submit button')
        browser.find_element_by_xpath(selectors['input_submit_sign_in']).click()
    except NoSuchElementException as e:
        logging.debug(f"input_submit_sign_in not found! Can't sign in! {e}")
        sys.exit(f"Can't find input_submit_sign_in {e}")
except NoSuchElementException as e:
    logging.debug(f'Sign up form with sign in link not found. {e}')

logging.info('Signed In (or already authorized with cookies) successfully')
random_sleep()

try:
    logging.info(f'Get company name')
    company_name = browser.find_element_by_xpath(selectors['company_name']).text
    logging.info(f'Extracted company name {company_name}')
except NoSuchElementException as e:
    logging.debug(f"Can't find company_name {e}")
    sys.exit(f"Can't find company_name {e}")

try:
    browser.find_element_by_xpath(selectors['messaging_modal_expanded']).click()
    logging.info(f"Messaging modal was closed")
except NoSuchElementException as e:
    logging.info(f"messaging_modal_expanded not found (it's normal, maybe it was already closed)")

try:
    for conversation_window in browser.find_elements_by_xpath(selectors['close_conversation_window']):
        logging.info(f"{conversation_window.text} closed")
        conversation_window.click()
except NoSuchElementException as e:
    logging.info(f"close_conversation_window not found (it's normal, maybe they not exists)")

try:
    logging.info(f'Click on link "See all N employees"')
    browser.find_element_by_xpath(selectors['link_to_all_employees']).click()
    random_sleep()
except NoSuchElementException as e:
    logging.debug(f"Can't find link_to_all_employees {e}")
    sys.exit(f"Can't find link_to_all_employees {e}")

if not os.path.exists(f'{os.getcwd()}/{args.out}'):
    write_json({
        'company': company_name,
        'employees': []
    })

last_page = False
while not last_page:
    # SEE ALL EMPLOYEES.
    try:
        # First scroll to footer to make all elements visible.
        global_footer = browser.find_element_by_xpath(selectors['global_footer'])
        scroll_to_element(global_footer)
    except NoSuchElementException as e:
        logging.debug(f"Can't find global_footer")
        sys.exit(f"Can't find global_footer")
    try:
        page_number = browser.find_elements_by_xpath(selectors['employees_pagination_current'])[0].text
        logging.info(f"Parsing page number {page_number}")
        print(f"Parsing page number {page_number}")
    except NoSuchElementException as e:
        logging.debug(f"Can't find employees_pagination_current!")
        sys.exit(f"Can't find employees_pagination_current!")
    try:
        profiles = browser.find_elements_by_xpath(selectors['profiles_list'])
        for profile in profiles:
            # Profile links added to html only when visible on screen
            scroll_to_element(profile)
            try:
                profile_link = profile.find_element_by_xpath(selectors['profile_link'])

                try:
                    actor_name = profile_link.find_element_by_xpath(selectors['profile_link_actor_name']).text
                except NoSuchElementException as e:
                    logging.debug(f"Can't find profile_link_actor_name!")
                    sys.exit(f"Can't find profile_link_actor_name!")

                try:
                    profile_link_position_name = profile.find_element_by_xpath(selectors['profile_link_position_name']).text
                except NoSuchElementException as e:
                    profile_link_position_name = ''
                    logging.debug(f"Can't find profile_link_position_name!")

                if actor_name == 'LinkedIn Member' or actor_name == 'Участник LinkedIn':
                    logging.info(f"Profile {profile_link_position_name} has limited visibility. Skip iteration.")
                    continue
                else:
                    profile_link_href = profile_link.get_attribute('href')
                    # TODO: CHECK IF PROFILE URL EXIST IN RESULT.JSON
                    json_data = read_json()
                    if not any(employee['url'] == profile_link_href for employee in json_data['employees']):
                        logging.info(f"Opening profile {profile_link.text} {profile_link_href} in new tab.")
                        # Open the link in a new tab by sending key strokes on the element
                        profile_link.send_keys(Keys.CONTROL + Keys.RETURN)
                        # Switch to last opened tab
                        browser.switch_to.window(browser.window_handles[-1])
                        random_sleep()

                        # TODO: NEED CHECK FOR CAPTCHA IN NEW PROFILE TAB
                        employee = parse_profile()
                        employee['url'] = profile_link_href
                        json_data['employees'].append(employee)
                        write_json(json_data)

                        # Close profile tab
                        browser.close()
                        # Put focus on current window which will be the window opener
                        browser.switch_to.window(browser.window_handles[0])
                        sleep(1)
            except NoSuchElementException as e:
                logging.debug(f"Can't find profile_link. Maybe it is because show empty+'try free trial propose' {e}")

    except NoSuchElementException as e:
        logging.debug(f"Can't find profiles_list {e}")
        sys.exit(f"Can't find profiles_list {e}")

    try:
        # TODO: NEED CHECK FOR CAPTCHA IN NEW SEARCH PAGINATION PAGE
        pagination_next_button = browser.find_element_by_xpath(selectors['employees_pagination_next'])
        scroll_to_element(pagination_next_button)
        if pagination_next_button.is_enabled():
            pagination_next_button.click()
            random_sleep()
        else:
            last_page = True

    except NoSuchElementException as e:
        logging.debug(f"Can't find employees_pagination_next")


browser.close()
browser.quit()
