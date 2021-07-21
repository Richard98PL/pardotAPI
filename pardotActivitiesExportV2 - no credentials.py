import requests
import json
import concurrent.futures
from datetime import datetime
import csv

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
file1 = open("activitiesV2.csv", "w")
file2 = open("activitiesV2.txt", "w")
file3 = open("errors.csv", "w")
file4 = open("logger.csv", "w")

file3.write('"info",\n')
file4.write('"propsect_id",\n')

columns = '"prospect_id","score","prospect_email_address","type_name","details","created_at","updated_at","campaign.id","campaign.name","activity_id","link"'
file1.write(columns)
file2.write(columns)
endpoint = 'https://pi.pardot.com/api/visitorActivity/version/3/do/query?format=json&prospect_id='

prospects = []
with open('prospects.csv', mode='r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    linenumber = 0
    for row in csv_reader:  
        if linenumber > 0:
            id = row[0]
            email = row[1]
            score = row[2]
            tmpJson = {'id':'','email':'','score':''}
            tmpJson['id'] = id
            tmpJson['email'] = email
            tmpJson['score']= score
            # print(tmpJson)
            prospects.append(tmpJson)
        linenumber = linenumber + 1
print(len(prospects))
# prospects = prospects[1:800]

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

exit = False
lines = {}
errors = []
logger = {}
def logic(worker_number):
    global endpoint
    global session
    global how_many_workers
    global prospects
    global exit
    global lines
    global errors
    global logger
    global file1
    global file2

    prospectNumber = worker_number
    worker_line_array = []
    logger_array = []

    while ((prospectNumber < len(prospects) - 1) and exit == False):
        logger_array.append('"' + str(prospects[prospectNumber]['id']) + '"' + str(',\n'))
        prospect = prospects[prospectNumber]
        
        # print(prospect)
        url = endpoint + str(prospect['id'])
        r = requests.get(url, headers=session.headers)
        if r.status_code == 200:
            json_data = json.loads(r.text)
            if 'result' in json_data:
                if 'total_results' in json_data['result']:
                    how_many_results_left = json_data['result']['total_results']
                else:
                    how_many_results_left = 0
            else:
                how_many_results_left = 0

            print('this prospect has ' + str(how_many_results_left) + ' activities')
            if 'result' in json_data:
                if 'visitor_activity' in json_data['result']:
                    for activity in json_data['result']['visitor_activity']:
                        line = ',\n' + str(parser('prospect_id', activity))
                        line += ',"' + str(prospect['score']) + '"'
                        line += ',"' + str(prospect['email']) + '"'
                        line += ',' + str(parser('type_name', activity))
                        line += ',' + str(parser('details', activity))
                        line += ',' + str(parser('created_at', activity))
                        line += ',' + str(parser('updated_at', activity))
                        line += ',' + str(parser('campaign_id', activity))
                        line += ',' + str(parser('campaign_name', activity))
                        line += ',' + str(parser('id', activity))
                        line += ',' + str(parser('link_prospect_id', activity))
                        worker_line_array.append(line)
                        file1.write(line)
                        file2.write(line)


                    whichIteration = 1
                    while (how_many_results_left - 200 > 0):
                        url = endpoint + str(prospect['id']) + str('&offset=') + str(whichIteration * 200)
                        print('this has more than 200 results -> entering loop with offset ' + str(whichIteration * 200))
                        r = requests.get(url, headers=session.headers)
                        if r.status_code == 200:
                            json_data = json.loads(r.text)
                            for activity in json_data['result']['visitor_activity']:
                                if 'result' in json_data:
                                    if 'visitor_activity' in json_data['result']:
                                        line = ',\n' + str(parser('prospect_id', activity))
                                        line += ',"' + str(prospect['score']) + '"'
                                        line += ',"' + str(prospect['email']) + '"'
                                        line += ',' + str(parser('type_name', activity))
                                        line += ',' + str(parser('details', activity))
                                        line += ',' + str(parser('created_at', activity))
                                        line += ',' + str(parser('updated_at', activity))
                                        line += ',' + str(parser('campaign_id', activity))
                                        line += ',' + str(parser('campaign_name', activity))
                                        line += ',' + str(parser('id', activity))
                                        line += ',' + str(parser('link_prospect_id', activity))
                                        worker_line_array.append(line)
                                        file1.write(line)
                                        file2.write(line)

                                    how_many_results_left = how_many_results_left - 200
                                    whichIteration = whichIteration + 1
                        else:
                            print('error!' + str(r.status_code))
                            #  exit = True
                            errors.append('"server responded with code: ' + str(r.status_code) + ' for a prospect with id ' + prospect['id'] + '",\n')
                            break
                else:
                    print('error!' + str(r.status_code))
                    # exit = True
                    errors.append('"server responded with code: ' + str(r.status_code) + ' for a prospect with id ' + prospect['id'] + '",\n')
                    break
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        print(str(current_time) + ' current_prospect_number = ' + str(prospectNumber))
        prospectNumber = prospectNumber + how_many_workers

    logger[worker_number] = logger_array
    lines[worker_number] = worker_line_array
    

how_many_workers = 10
for worker_number in range( how_many_workers ):
    lines[worker_number] = []
    logger[worker_number] = []

with concurrent.futures.ThreadPoolExecutor() as ex:
    for i in range(how_many_workers):
        ex.submit(logic, worker_number=i)
# logic(worker_number=1)

# for worker_number in range( how_many_workers ):
#     print(len(lines[worker_number]))
#     for line in lines[worker_number]:
#         file1.write(line)
#         file2.write(line)
#     for log in logger[worker_number]:
#         file4.write(log)

for error in errors:
    file3.write(error)


file1.close()
file2.close() 
file3.close()
file4.close()
