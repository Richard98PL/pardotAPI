import requests
import json
import concurrent.futures
from datetime import datetime

tokenRequest = requests.post("https://login.salesforce.com/services/oauth2/token", data={
    'password': '',
    'username': '',
    'client_id': '',
    'client_secret': '',
    'grant_type': 'password'}
                             )

auth_token_salesforce = json.loads(tokenRequest.text)['access_token']
print('salesforce token obtained succesfully')

how_many_records = 0
session = requests.Session()
headers_dict = {"Authorization": "Bearer " + str(auth_token_salesforce),
                "Pardot-Business-Unit-Id" : "",
                "Accept" : "*/*",
                'Content-Type': 'application/json; charset=utf-8'}
session.headers.update(headers_dict)
file1 = open("prospects.csv", "w") 
file2 = open("prospects.txt", "w") 
global_offset = 0

columns = '"prospect_id","email","score","offset"'
file1.write(columns)
file2.write(columns)

endpoint = 'https://pi.pardot.com/api/prospect/version/3/do/query?fields=score,email&format=json&offset='
url = endpoint + str(global_offset)
r = requests.get(url, headers = session.headers)
json_data = json.loads(r.text)
how_many_records = json_data['result']['total_results']

def parser(str):
  return '"' + str + '"'

def logic(worker_number):
  global endpoint
  global file1
  global url
  global session
  offset = global_offset + 200 * worker_number

  while offset < how_many_records:
    url = endpoint + str(offset)
    r = requests.get(url, headers = session.headers)
    json_data = json.loads(r.text)
    for prospect in json_data['result']['prospect']:
      if prospect['score'] > 0:
        line = ',\n' + parser(str(prospect['id']))
        line += ',' + parser(str(prospect['email']))
        line += ',' + parser(str(prospect['score']))
        line += ',"' + str(offset) + '"'

        file1.write(line)
        file2.write(line)

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print(str(current_time) + ' current_offset=' + str(offset))
    offset = offset + 200 * how_many_workers

how_many_workers = 5
with concurrent.futures.ThreadPoolExecutor() as ex:
    for i in range(how_many_workers):
        try:
          ex.submit(logic, worker_number=i)
        except Exception as exc:
          print(exc)

file1.close() 
file2.close() 