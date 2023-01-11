import requests
import json
import csv
from simple_salesforce import Salesforce
from requests_html import HTMLSession
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import re
from time import sleep

CLEANR = re.compile('<.*?>') 
sf = Salesforce(username='',password='', security_token='')

def getSalesorceAuthDict():
    print('Salesforce authorization...')
    URL = 'https://login.salesforce.com/services/oauth2/token?'
    URL += 'grant_type=password'
    URL += '&'
    URL += 'client_id='
    URL += '&'
    URL += 'client_secret=F'
    URL += '&'
    URL += 'username='
    URL += '&'
    URL += 'password='

    r = requests.post(url = URL)
    data = r.json()
    token = ''
    sfendpoint = ''

    if 'access_token' in data.keys():
        sfendpoint = data['instance_url']
        token = data['access_token']
    else:
        print('error')
    
    return {'token' : token, 'endpoint' : sfendpoint}

def getForms(auth_dict):
    token = auth_dict['token']
    queryUrl = 'https://pi.pardot.com/api/form/version/3/do/query?offset=0&format=json'
    sfheaders = {'User-Agent' : 'Python', 
                 'Authorization' : 'Bearer ' + token,
                 'Content-Type' : 'application/json',
                 'Pardot-Business-Unit-Id' : '0Uv2p000000CaVdCAK'}

    r = requests.get(url=queryUrl,headers=sfheaders)

    json_response = r.json()
    count = json_response['result']['total_results']
    print(count)
    return json_response['result']['form']

def getRows(driver, whichTable):
    soup = BeautifulSoup(driver.page_source, 'lxml')
    tables = soup.find_all('table', class_='table-bordered')
    table = tables[whichTable]

    outputs = []
    for element in table:
        for subelement in element:
            if "<b>" in str(subelement):
                for next in subelement:
                    for another in next:
                        if "<b>" in str(another):
                            print("another")
                            strings = str(another).split("</b>")
                            
                            anotherStrings = []
                            for string in strings:
                                tmpString = str(string).split("]")
                                for x in tmpString:
                                    anotherStrings.append(str(x))

                            for string in anotherStrings:
                                string = re.sub('\s+','',string)
                                print(string)
                                if "nolabel" not in string :
                                    string = re.sub(CLEANR, '', string)
                                else:
                                    string = "HIDDEN_FIELD"

                                if len(string) > 0:
                                    string = string.replace('(r)', '')
                                    string = string.replace('[', '')
                                    string = string.replace('(a)', '')
                                    string = string.replace('(d)', '')
                                    outputs.append(string)
                            print(outputs)

    return outputs  


auth_dict = getSalesorceAuthDict()
forms = getForms(auth_dict)






url = auth_dict['endpoint'] + '/secur/frontdoor.jsp?sid=' + sf.session_id

capabilities = DesiredCapabilities().CHROME
options = Options()
options.headless = False
options.add_argument("--enable-javascript")
options.add_argument("--window-size=1200,1200")

prefs = {
    'profile.default_content_setting_values':
    {
        'notifications': 1,
        'geolocation': 1
    },

    'profile.managed_default_content_settings':
    {
        'geolocation': 1
    },
}

options.add_experimental_option('prefs', prefs)
capabilities.update(options.to_capabilities())

driver = webdriver.Chrome(options=options)
driver.implicitly_wait(25)
driver.get(url)
driver.get('https://pi.pardot.com/')
print('Selenium opened')


driver.find_element(By.ID, "logInWithSalesforceButton").click()

driver.implicitly_wait(2)
try:
    driver.find_element(By.CLASS_NAME, "key").click()
except Exception as e:
    pass

driver.implicitly_wait(2)
results = []

j = 0

file = open('fields.csv', 'w')
writer = csv.writer(file)
headers = ['Form Field', "Prospect Field Type", 'Prospect Field', 'Form Name', 'Form Id', 'URL', 'PI_URL']
writer.writerow(headers)

forms.reverse()

for form in forms:
    name = form['name']
    id = form['id']
    url = auth_dict['endpoint'] + '/lightning/page/pardot/form%252forms?pardot__path=%2Fform%2Fread%2Fid%2F' + str(id)
    pardot_url = 'https://pi.pardot.com/form/read/id/' + str(id)

    createdDate = form['created_at']

    driver.get(pardot_url)
    # driver.implicitly_wait(1)
    try:
        driver.find_element(By.CLASS_NAME, "key").click()
    except Exception as e:
        sleep(7)
        pass
        
    fields = getRows(driver, 0)
    
    t = 0
    formFields = []
    prospectFields = []
    print('fields')
    print(fields)
    for element in fields:
        if t % 2 == 0:
            formFields.append(element)
        else:
            prospectFields.append(element)
        t = t + 1


    k = 0
    while k < len(formFields):
        row = []
        row.append(formFields[k].replace(',', ' '))
        try:
            for subword in prospectFields[k].split(':', 1):
                row.append(subword.replace(',', ' '))
        except Exception as e:
            sleep(100)
            print(e)


        row.append(name.replace(',', ' '))
        row.append(id)
        row.append(url)
        row.append(pardot_url)

        print(row)
        writer.writerow(row)    
        k = k + 1

    print(j)
    j = j + 1
    if j > 150:
        break

file.close()

driver.quit()


