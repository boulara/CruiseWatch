"""
Rick Boulanger

01/30/2015

* Call script with the cruse ID as an arg
* script checks for json file of same ID
* script checked V2G price
* script matches up V2G price vs historical price
* IF newer price is lower, send pushover
* IF price is newer, update json file

"""

import mechanicalsoup
import time
import sys
import json
import os.path
import locale
import configparser
import string
from pprint import *

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

### Main ###
def main():

	### Reterieve config data for Pushover & Email
	config = configparser.ConfigParser()
	config.read('../Config-Data/config.ini')
	cruises = sys.argv[1:]

	if not cruises:
		print('No Cruises found!')
		sys.exit()
	for cruiseID in cruises:
		print('########## Running Data for ' + cruiseID + ' ##########')
		fncCheckRates(cruiseID,config)	

	

### END OF MAIN ###	
################# FUNCTIONS #################

def fncSendPushover(msg,config):
	import http.client, urllib
	conn = http.client.HTTPSConnection("api.pushover.net:443")
	conn.request("POST", "/1/messages.json",
		urllib.parse.urlencode({
			"token": config['pushover']['token'],
	    	"user": config['pushover']['key'],
	    	"message": msg,
	 	}), { "Content-type": "application/x-www-form-urlencoded" })
	conn.getresponse()

def fncSendEmail(msg, config):
	import smtplib
	from_addr = config['email']['username']
	to_addrs = 'boulara@me.com, llinzee@gmail.com'

	username = config['email']['username']
	pwd = config['email']['password']

	session = smtplib.SMTP('smtp.gmail.com', 587)
	session.ehlo()
	session.starttls()
	session.login(username, pwd)

	headers = "\r\n".join(["from: " + from_addr,
                       "subject: " + msg,
                       "to: " + to_addrs,
                       "mime-version: 1.0",
                       "content-type: text/html"])

	# body_of_email can be plaintext or html!                    
	content = headers + "\r\n\r\n" + "Rick Rocks "
	session.sendmail(username, to_addrs, content)

def fncSaveRates(id,rates):
	with open (id+'.json','w') as outfile:
		json.dump(rates, outfile)

def fncFormatCurrency(i):
	return locale.currency(i)

def fncCheckRates(cruiseID,config):

	fileName = cruiseID + '.json'

	if not os.path.isfile(fileName): #Create File
		print('No json file exists')
		past_room_rates = {
		    'inside': 0,
		    'oceanview': 0,
		    'balcony': 0,
		    'suite': 0
		}
	else: # read file
		with open(fileName) as past_rates_file:
			past_room_rates = json.load(past_rates_file)
			#pprint(past_room_rates)

	browser = mechanicalsoup.Browser()
	baseUrl = "http://www.vacationstogo.com/login.cfm?deal=" 

	fullUrl = baseUrl + cruiseID

	login_page = browser.get(fullUrl)
	login_form = login_page.soup.select("#login")[0].select("form")[0]
	login_form.select("#login-logemail")[0]['value'] = "munky878@gmail.com"
	page2 = browser.submit(login_form, login_page.url)
	soup = page2.soup

	dateChecked = (time.strftime("%m/%d/%Y %H:%M:%S"))

	room_rates = {}
	room_rates['inside'] = int((soup.find("span", {"id":"rate-room1"}).text).replace("$",'').replace(",",''))
	room_rates['oceanview'] = int((soup.find("span", {"id":"rate-room2"}).text).replace("$",'').replace(",",''))
	room_rates['balcony'] = int((soup.find("span", {"id":"rate-room3"}).text).replace("$",'').replace(",",''))
	room_rates['suite'] = int((soup.find("span", {"id":"rate-room4"}).text).replace("$",'').replace(",",''))
	room_rates['date_last_checked'] = dateChecked


	cruise_meta_data = soup.find("span", {"class":"vtgfont16"}).text.replace("departing","").replace("on","").replace("  "," ")
	print(cruise_meta_data)

	#Get Config Data
	token = config['pushover']['token']
	key = config['pushover']['key']
	email_addr = config['email']['username']
	pwd = config['email']['password']

	msg = ''
	levels = ['inside','oceanview','balcony','suite']

	for level in levels:
		past_rate = past_room_rates[level]
		room_rate = room_rates[level]
		if ( room_rate < past_rate):
			msg = "PRICE ALERT: " +cruise_meta_data +  " (" + level.upper() + ") WAS: " + fncFormatCurrency(past_rate) +  " - NOW " + fncFormatCurrency(room_rate)
			fncSendPushover(msg,config)
			fncSendEmail(msg,config)
			print(msg)
		else:
			#text = "PRICE ALERT: " + cruise_meta_data +  " (" + level.upper() + ") WAS: " + fncFormatCurrency(past_rate) +  " - NOW " + fncFormatCurrency(room_rate)
			msg = "No Price Change - " + dateChecked
			print(msg)

	#pprint(room_rates)
	### UPDATE JSON FILE

	fncSaveRates(cruiseID,room_rates)	


### Call Main ###
if __name__ == '__main__':
		main()

