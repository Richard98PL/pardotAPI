import requests
import json
import concurrent.futures
from datetime import datetime

how_many_records = 0

tokenRequest = requests.post("https://login.salesforce.com/services/oauth2/token", data={
    'password': '',
    'username': '',
    'client_id': '',
    'client_secret': '',
    'grant_type': 'password'}
                             )

auth_token_salesforce = json.loads(tokenRequest.text)['access_token']
print('salesforce token obtained succesfully')

session = requests.Session()
headers_dict = {"Authorization": "Bearer " + auth_token_salesforce,
                "Pardot-Business-Unit-Id": "",
                "Accept": "*/*",
                'Content-Type': 'application/json; charset=utf-8'}
session.headers.update(headers_dict)
file1 = open("activities.csv", "w")
file2 = open("activities.txt", "w")

columns = '"prospect_id","type_name","details","created_at","updated_at","campaign.id","campaign.name","activity_id","offset","link"'
file1.write(columns)
file2.write(columns)
offset = 0
endpoint = 'https://pi.pardot.com/api/visitorActivity/version/3/do/query?sort_by=prospect_id&sort_order=descending&format=json&offset=0'

url = endpoint + str(offset)
r = requests.get(url, headers=session.headers)
json_data = json.loads(r.text)
# how_many_records = json_data['result']['total_results']
how_many_records = 1600
print('there are ' + str(how_many_records) + ' records')


def parser(key, dict):
    if key == 'campaign_id':
        if 'campaign' in dict:
            if 'id' in dict['campaign']:
                return '"' + str(dict['campaign']['id']) + '"'
            else:
                return '""'
        else:
            return '""'
    elif key == 'campaign_name':
        if 'campaign' in dict:
            if 'name' in dict['campaign']:
                return '"' + str(dict['campaign']['name']) + '"'
            else:
                return '""'
        else:
            return '""'
    elif key == 'link_prospect_id':
        if 'prospect_id' in dict:
            return '"https://pi.pardot.com/visitorActivity/index/prospect_id/' + str(dict['prospect_id']) + '"'
    else:
        if key in dict:
            return '"' + str(dict[key]) + '"'
        else:
            return '""'


how_many_workers = 15


def logic(worker_number):
    global endpoint
    global file1
    global file2
    global url
    global session
    global offset_dict
    global how_many_workers

    while offset_dict[worker_number] < how_many_records:
        url = endpoint + str(offset_dict[worker_number])
        r = requests.get(url, headers=session.headers)
        json_data = json.loads(r.text)

        for activity in json_data['result']['visitor_activity']:
            line = ',\n' + str(parser('prospect_id', activity))
            line += ',' + str(parser('type_name', activity))
            line += ',' + str(parser('details', activity))
            line += ',' + str(parser('created_at', activity))
            line += ',' + str(parser('updated_at', activity))
            line += ',' + str(parser('campaign_id', activity))
            line += ',' + str(parser('campaign_name', activity))
            line += ',' + str(parser('id', activity))
            line += ',' + str(offset_dict[worker_number])
            line += ',' + str(parser('link_prospect_id', activity))

            file1.write(line)
            file2.write(line)

        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        print(str(current_time) + ' current_offset=' + str(offset_dict[worker_number]))

        offset_dict[worker_number] = offset_dict[worker_number] + 200 * how_many_workers


offset_dict = {}
for i in range(how_many_workers):
    offset_dict[i] = 200 * i

with concurrent.futures.ThreadPoolExecutor() as ex:
    for i in range(how_many_workers):
        ex.submit(logic, worker_number=i)

file1.close()
file2.close() 
