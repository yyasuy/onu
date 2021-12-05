from selenium import webdriver
from selenium.webdriver.chrome.options import Options as Chrome_Options
from selenium.webdriver.chrome import service as Chrome_Service
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import datetime
import re
from pprint import pprint
import time
import subprocess
import requests

#DRIVER_PATH = '/opt/homebrew/bin/chromedriver'
DRIVER_PATH = '/usr/local/bin/chromedriver'
chrome_service = Chrome_Service.Service( DRIVER_PATH )
chrome_options = Chrome_Options()
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--proxy-server="direct://"')
chrome_options.add_argument('--proxy-bypass-list=*')
chrome_options.add_argument('--start-maximized')

def init_browser():
	browser = webdriver.Chrome( service = chrome_service, options = chrome_options )
	url = 'http://192.168.1.1'
	browser.get( url )
	browser.implicitly_wait(5)
	return browser

def access_onu():
	file = open( '.password', 'r' )
	password = file.readline().strip()
	file.close()
	el = browser.find_element( By.CSS_SELECTOR, '#txt_Username' )
	el.send_keys( 'admin' )
	el = browser.find_element( By.CSS_SELECTOR, '#txt_Password' )
	el.send_keys( password )
	el = browser.find_element( By.CSS_SELECTOR, '#button' )
	el.click()

def find_received_value():
	el = browser.find_element( By.CSS_SELECTOR, '#nav > ul > li:nth-child(5) > div' )
	el.click()
	iframe = browser.find_element( By.CSS_SELECTOR, '#frameContent' )
	browser.switch_to.frame( iframe )
	el = browser.find_element( By.CSS_SELECTOR, '#optic_status_table > tbody > tr:nth-child(4) > td:nth-child(2)' )
	return el.text

def is_connected_to_internet():
	result = subprocess.run( [ "ping", "ping-toyama.sinet.ad.jp", "-c", "1", "-W", "300" ], stdout=subprocess.PIPE)
	if result.returncode == 0:
		return True
	else:
		return False

def log( _message ):
	file = open( 'error.log', 'a')
	dt_now = datetime.datetime.now()
	file.write( dt_now.strftime('%Y/%m/%d %H:%M:%S') + " " + _message + "\n" )
	file.close()

def send_to_line( _message ):
	url = "https://notify-api.line.me/api/notify"
	file = open( '.access_token', 'r' )
	access_token = file.readline().strip()
	file.close
	headers = {'Authorization': 'Bearer ' + access_token}
	message = _message
	payload = {'message': message}
	if is_connected_to_internet() == True:
		r = requests.post(url, headers=headers, params=payload,)

browser = init_browser()
access_onu()

MIN_DBM = -22.00
MAX_ALERT = 100
INTERVAL = 60
MAX_COUNT = 10080 # 1 week
count = 0
alert = 0
while count < MAX_COUNT:
	try:
		text = find_received_value()
	
	except:
		browser.close()
		time.sleep( 10 )
		browser = init_browser()
		access_onu()

		text = find_received_value()
	
	dt_now = datetime.datetime.now()
	print( dt_now.strftime('%Y/%m/%d %H:%M:%S') + " " + text )

	match = re.search( '[-\d\.]+', text )
	text_value = match.group( 0 )

	if( '--' in text_value ):
		try:
			log( text )
			send_to_line( text )
			alert += 1
		except:
			continue
	elif ( float( text_value ) < MIN_DBM ):
		try:
			log( text )
			send_to_line( text )
			alert += 1
		except:
			continue
	else:
		alert = 0

	if ( alert == MAX_ALERT ):
		break

	browser.switch_to.default_content()
	time.sleep( INTERVAL )
	count += 1

browser.close()

