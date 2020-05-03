# -*- coding: utf-8 -*-
import json
import argparse

arguments_parser = argparse.ArgumentParser(description='Parse results from LinkedIn company -> employees parser with '
                                                       'many job positions only for parsed company')
arguments_parser.add_argument('-i', type=str, default='result.json', help='Input json file')
arguments_parser.add_argument('-o', type=str, default='positions_switch_durations.json', help='Output json file')
args = arguments_parser.parse_args()


def read_json():
    with open(args.i) as json_file:
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

with open(args.o, 'w') as file:
    json.dump(data_to_write, file, indent=4, ensure_ascii=False)
