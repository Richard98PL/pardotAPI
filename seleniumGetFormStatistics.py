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
    URL += 'username=u'
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
                 'Pardot-Business-Unit-Id' : ''}

    r = requests.get(url=queryUrl,headers=sfheaders)

    json_response = r.json()
    count = json_response['result']['total_results']
    print(count)
    return json_response['result']['form']

def getRows(driver, whichTable):
    soup = BeautifulSoup(driver.page_source, 'lxml')
    tables = soup.find_all('table', class_='table-bordered')
    table = tables[whichTable]
    keys = table.find_all('td', class_='key')
    values = table.find_all('td', class_='value')

    i = 0
    results = []
    while i < len(keys):
        dict = {}
        key = keys[i]
        key = str(key).replace('<td class="key">', '')
        key = str(key).replace('</td>', '')

        value = values[i]
        value = str(value).replace('<td class="value">', '')
        value = str(value).replace('</td>', '')

        value = re.sub(CLEANR, '', value)

        if whichTable == 0:
            key = key.strip()
            value = value.strip()
        dict[str(key)] = str(value)
        results.append(dict)
        i = i + 1

    #print(results)
    return results  


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

driver.implicitly_wait(5)
try:
    driver.find_element(By.CLASS_NAME, "key").click()
except Exception as e:
    pass

driver.implicitly_wait(5)
results = []

j = 0

file = open('forms.csv', 'w')
writer = csv.writer(file)
headers = ['Action Name', 'Action Value', 'Form Name', 'Form Id', 'URL', 'PI_URL', 'REPORT_URL', "Total Submissions"]
writer.writerow(headers)

for form in forms:
    name = form['name']
    id = form['id']
    url = auth_dict['endpoint'] + '/lightning/page/pardot/form%252forms?pardot__path=%2Fform%2Fread%2Fid%2F' + str(id)
    pardot_url = 'https://pi.pardot.com/form/read/id/' + str(id)

    report_url = 'https://pi.pardot.com/form/readReport/id/' + str(id)
    createdDate = form['created_at']
    result = {
        "name" : name,
        "id" : id,
        "pardot_url" : pardot_url,
        "report_url" : report_url,
        "sf_url" : url,
        "createdDate" : createdDate,
        "completionActions" : [],
        "statistics" : []
    }

    driver.get(pardot_url)
    driver.implicitly_wait(4)
    try:
        driver.find_element(By.CLASS_NAME, "key").click()
    except Exception as e:
        pass
        
    completionActions = getRows(driver, 1)
    result["completionActions"] = completionActions


    driver.get(report_url)
    driver.implicitly_wait(2)
    try:
        driver.find_element(By.CLASS_NAME, "key").click()
    except Exception as e:
        pass

    getReportStatistics = getRows(driver, 0)
    result["statistics"] = getReportStatistics


    output = json.dumps(result, indent = 4)
    # print(result)
    results.append(result)
    row = []
    for completionAction in completionActions:
        for key in completionAction:
            row = []
            key = key.replace(',', ' ')
            print(key)
            row.append(key)
            value = completionAction[key].replace(',', ' ')
            row.append(value)
            if len(completionActions) > 0:
                row.append(name)
                row.append(id)
                row.append(url)
                row.append(pardot_url)
                row.append(report_url)
                
                for reportStatistic in getReportStatistics:
                    for key in reportStatistic:
                        if key == 'Total Submissions':
                            row.append(reportStatistic[key].replace(',', ' '))

            print(row)
            writer.writerow(row)    

    print(j)
    j = j + 1
    if j > 15:
        break

file.close()
json_object = json.dumps(results, indent=4)
with open("forms.json", "w") as outfile:
    outfile.write(json_object)

driver.quit()


