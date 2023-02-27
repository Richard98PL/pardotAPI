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
    URL += 'client_secret='
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

auth_dict = getSalesorceAuthDict()
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
print(url)
driver.get(url)
driver.get('https://pi.pardot.com/')
print('Selenium opened')


driver.find_element(By.ID, "logInWithSalesforceButton").click()

driver.implicitly_wait(5)
try:
    driver.find_element(By.CLASS_NAME, "key").click()
except Exception as e:
    pass

driver.implicitly_wait(1)

j = 0
errors = []
deleted = []
deletedArr = ['10375', '2973', '10360', '10362', '11572', '3825', '11574', '10988', '2605', '10121', '2527', '11092', '2591', '12252', '3187', '3167', '5318', '5502', '10938', '1620', '2252', '2529', '6177', '11098', '2214', '2310', '2312', '2314', '2374', '2403', '2495', '2513', '2517', '2777', '3073', '3161', '3417', '3441', '3519', '3603', '3904', '3930', '7529', '10771', '9732', '10409', '7544', '13357']
errorArr = ['10717', '9714', '2971', '2859', '11783', '12250', '3823', '2607', '6097', '1664', '1924', '3101', '3159', '13773']
print(len(deletedArr))
print(len(errorArr))
with open('formsProduction.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
        if row[0] in deletedArr:
            continue
        
        if j == 0:
            j = j + 1
        else:
            formUrl = row[2]
            action = row[4]
            queue = row[5]
            name = row[1]

            sfUrl = row[3]
        
            if action == 'Delete':
                print(action)
                print(name)
                driver.get(formUrl)
                driver.implicitly_wait(2)


                try:
                    driver.find_element(By.XPATH, "//*[contains(text(), 'Page Not Found')]").click()
                except Exception as e:
                    if "inter" in str(e):
                        print('next')
                        deleted.append(row[0])
                        continue
                # x = input('wait...')
                # if x == 'e':
                #     errors.append(row[0])

                # print(x)

                errors.append(row[0])

                try:
                    driver.find_element(By.CSS_SELECTOR, "a[class='btn btn-default dropdown-toggle']").click()
                    driver.implicitly_wait(1)
                    try:
                        driver.find_element(By.XPATH, "//*[contains(text(), 'Delete')]").click()
                        driver.implicitly_wait(1)
                        driver.switch_to.alert.accept()
                    except Exception as e:
                        print(e)
                        driver.implicitly_wait(1)
                        driver.switch_to.alert.accept()
                except Exception as e:
                    print(e)


driver.quit()
print(errors)
print(deleted)


