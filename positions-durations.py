# -*- coding: utf-8 -*-
import json


def read_json():
    with open('result.json') as json_file:
        return json.load(json_file)


def duration_to_months(date: str) -> int or str:
    date = date.split(' ')
    if len(date) == 4:
        years = int(date[0])
        months = int(date[2])
        return years * 12 + months
    elif len(date) == 2:
        if date[1] in ['yr', 'yrs']:
            return int(date[0]) * 12
        if date[1] in ['mo', 'mos']:
            return int(date[0])
    else:
        return 'No duration'


data = read_json()

employees = [{'experience': employee['experience'], 'url': employee['url']} for employee in data['employees'] if employee['experience']]

data_to_write = []

for employee in employees:
    for company in employee['experience']:
        if company['company'] == data['company'] and len(company['positions']) > 1:
            for index, position in enumerate(company['positions']):
                if index == 0:
                    continue
                item = {
                    'from': {
                        'name': position['name'],
                        'duration': duration_to_months(position['dates']['duration'])
                    },
                    'to': {
                        'name': company['positions'][index-1]['name'],
                        'duration': duration_to_months(company['positions'][index-1]['dates']['duration'])
                    },
                    'url': employee['url']
                }
                data_to_write.append(item)

with open('positions_switch_durations.json', 'w') as file:
    json.dump(data_to_write, file, indent=4, ensure_ascii=False)
