import requests
import json
from datetime import datetime

how_many_records = 0

tokenRequest = requests.post("https://login.salesforce.com/services/oauth2/token", data={
   'password': 'yitBritenet12338axkJGP7dGa3ZF2u4kajjJ8p',
   'username' : 'ryszard@genus.one',
   'client_id' : '3MVG9WtWSKUDG.x43uSMGY0NnVzFhu6MpNNQjMc6.fxwz..xD..whoGuS2VkCr0zHbxZCHFBxCieHxcp5WuMR',
   'client_secret' : '1D7E75BDC843D3452F1351B1E2AEA468BD8848BEBF3ABA76F9327F36C02F71A7',
   'grant_type' : 'password'}
   )

auth_token_salesforce = json.loads(tokenRequest.text)['access_token']
print('salesforce token obtained succesfully')

session = requests.Session()
headers_dict = {"Authorization": "Bearer " + auth_token_salesforce,
                "Pardot-Business-Unit-Id" : "0Uv2p000000CaVdCAK",
                "Accept" : "*/*",
                'Content-Type': 'application/json; charset=utf-8'}
session.headers.update(headers_dict)
file1 = open("activities.csv", "w") 
file2 = open("activities.txt", "w") 

columns = '"prospect_id","type_name","details","created_at","updated_at","campaign.id","campaign.name","activity_id","offset","link"'
file1.write(columns)
file2.write(columns)
i = 0
endpoint = 'https://pi.pardot.com/api/visitorActivity/version/3/do/query?sort_by=prospect_id&sort_order=descending&format=json&offset=0'

url = endpoint + str(i)
r = requests.get(url, headers = session.headers)
json_data = json.loads(r.text)
how_many_records = json_data['result']['total_results']
print('there are '+str(how_many_records)+' records')

def parser(key,dict):
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


while i < how_many_records:
  url = endpoint + str(i)
  r = requests.get(url, headers = session.headers)
  json_data = json.loads(r.text)
  
  for activity in json_data['result']['visitor_activity']:
    line = ',\n' + str(parser('prospect_id',activity))
    line += ',' + str(parser('type_name',activity))
    line += ',' + str(parser('details',activity))
    line += ',' + str(parser('created_at',activity))
    line += ',' + str(parser('updated_at',activity))
    line += ',' + str(parser('campaign_id',activity))
    line += ',' + str(parser('campaign_name',activity))
    line += ',' + str(parser('id',activity))
    line += ',' + str(i) 
    line += ',' + str(parser('link_prospect_id',activity))
    
    file1.write(line)
    file2.write(line)
  
  now = datetime.now()
  current_time = now.strftime("%H:%M:%S")
  print( str(current_time) + ' current_offset=' + str(i) )
  file1.close() 
  file2.close() 
  

  file1 = open("activities.csv", "a") 
  file2 = open("activities.txt", "a") 

  i = i + 200

file1.close() 
file2.close() 
