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
from pprint import *

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

### Main ###
def main():

	if (sys.argv[1]):
		cruiseID = sys.argv[1]
	else:
		cruiseID = '12345'

	path = 'cruise-data/'

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


	text = ''
	levels = ['inside','oceanview','balcony','suite']

	for level in levels:
		past_rate = past_room_rates[level]
		room_rate = room_rates[level]
		if ( room_rate > past_rate):
			text = "PRICE ALERT: " +cruise_meta_data +  " (" + level.upper() + ") WAS: " + fncFormatCurrency(past_rate) +  " - NOW " + fncFormatCurrency(room_rate)
			fncPushover(text)
			print(text)
		else:
			#text = "PRICE ALERT: " + cruise_meta_data +  " (" + level.upper() + ") WAS: " + fncFormatCurrency(past_rate) +  " - NOW " + fncFormatCurrency(room_rate)
			text = "No Price Change - " + dateChecked
			print(text)




	#pprint(room_rates)
	### UPDATE JSON FILE

	fncSaveRates(cruiseID,room_rates)

### END OF MAIN ###	
################# FUNCTIONS #################

def fncPushover(msg):
	import http.client, urllib
	conn = http.client.HTTPSConnection("api.pushover.net:443")
	conn.request("POST", "/1/messages.json",
		urllib.parse.urlencode({
			"token": "a9ozHmfCxm6cWQE79KRKXfLNrDXoK2",
	    	"user": "uHEMkqk8JcqYkTg7UktHPusRqf5UtF",
	    	"message": msg,
	 	}), { "Content-type": "application/x-www-form-urlencoded" })
	conn.getresponse()

def fncSaveRates(id,rates):
	with open (id+'.json','w') as outfile:
		json.dump(rates, outfile)

def fncFormatCurrency(i):
	return locale.currency(i)

### Call Main ###
if __name__ == '__main__':
		main()

