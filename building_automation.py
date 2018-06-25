#!/usr/bin/python
# TODO : Test for needed dependcies and versions
# Write tests for different conversion factors
from __future__ import division
import requests
import math
import pyrebase
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import json
import urllib3
from urllib.parse import quote
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Search path strings
googleSearchPathPrefix = "https://maps.googleapis.com/maps/api/geocode/json?address="
googleKey = '&key='
googleAPIKey = 'AIzaSyDVhYdk_BnsNg1Tl4n_Bw1UOaXnTykUFzY'
latandlng = "/query"
openSearchPathPrefix = "https://www.openstreetmap.org"
openSearchPathAPI = "/api/0.6"
openStreetSearch = "/search?query="
openSearchPathSuffix = "&xhr=1"
EXPONENTIAL_MODIFIER = 1000
R_EARTH = 6371
R_EARTH_M = 6378137
FOOT_CONVERSION_FACTOR = 10.7639
level = 1
latlist = []
lnglist = []

# Convert the address to qurey form
# @param address the address space separated
# @return String with + concatenated address
def convert_address(address) :
	return address.replace(" ","+")

# Get REST for json response from url
# @param url the HTTP GET points at
# @return JHTTP response from url
def simple_get(url):
	try:
		with closing(get(url, stream=True)) as resp:
			if is_good_response(resp):
				return resp.contentgoogle-site-verification.google219c7f98bff31211.html
			else:
				return None
	except RequestException as e:
		log_error('Error during requests to {0} : {1}'.format(url,str(e)))
		return None


# Checks the status of the JSON response
# @param resp to evaluate
# @return Bool for correct header
def is_good_response(resp):
	content_type = resp.headers['Content-Type'].lower()
	return (resp.status_code == 200
		and content_type is not None
		and content_type.find('html') > -1)

# Find the distance using the Haversine formula between two degree points
# @params lat and lng values for each point
# @return distance in metters
def distance(lat1, lat2, lng1, lng2):
	latDistance = math.radians(lat2 - lat1)
	lngDistance = math.radians(lng2 - lng1)
	a = math.sin(latDistance/ 2) * math.sin(latDistance/ 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(lngDistance / 2) * math.sin(lngDistance / 2)
	c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
	distance = R_EARTH * c * EXPONENTIAL_MODIFIER
	return distance

# Calculate the area of the given polygon by calculating the vector area of the cycle
# @return String describing square foootage
def calculateArea():
	area = 0
	for i in range(0,len(latlist) - 1):
		if i == 0:
			latlist.append(latlist[i])
			lnglist.append(lnglist[i])
		area += math.radians(lnglist[i+1] - lnglist[i]) * (2 + math.sin(math.radians(latlist[i])) + math.sin(math.radians(latlist[i+1])))
	area = abs(area * level * FOOT_CONVERSION_FACTOR * R_EARTH_M**2 / 2)
	return str(area) + " square feet"

# Logging function
def log_error(e):
	print(e)

# Pull first return result for geocoded address and driver during async wait
# @param browser the chrome webdriver instance
# @param addr the address to async parse
# @return the url for the building
def waitForID(browser,addr) :
	tag = '\'Building \''
	browser.get(addr)
	url = ''
	try:
		browser.implicitly_wait(3)
		element = browser.find_element_by_xpath("//div[@id='query-nearby']/ul[@class='query-results-list']//p[contains(.,'Building ')]")
		url = element.find_element_by_tag_name("a").get_attribute('href')
	finally:
		browser.quit()
		return url

# Find the grid components based on the x y from the lat and lng
def findGridSize() :
	maxLat = max(latlist)
	minLat = min(latlist)
	maxLng = max(lnglist)
	minLng = min(lnglist)
	avgLat = (minLat + maxLat) * 0.5
	avgLng = (minLng + maxLng) * 0.5
	grid_x = math.ceil(distance(minLat, maxLat, avgLng, avgLng))
	grid_y = math.ceil(distance(avgLat, avgLat, minLng, maxLng))
	return grid_x, grid_y

# Parse the building xml to extract the latitudes and longitudes of the vertices
# @param http for the search thread
# @param addr query argument
def gpsFromNode(http, addr) :
	xml = BeautifulSoup(http.request('GET', openSearchPathPrefix + openSearchPathAPI + addr).data.decode('utf-8'), 'lxml')
	latlist.append(float(xml.node['lat']))
	lnglist.append(float(xml.node['lon']))

# Encode the building dimensions into json format
# @return JSON representing building
def encodeJSON(e) :
	grid_x, grid_y = findGridSize()
	buildingJSON = {'address': e, 'grid_x': grid_x, 'grid_y': grid_y}
	return buildingJSON

def setupFirebase():
    config = {
    "apiKey": "AIzaSyBbH3aaS3jJTfzJGEaDhTj8F5zumuJFvtU",
    "authDomain": "",
    "databaseURL": "https://atomolocationapi.firebaseio.com/",
    "storageBucket": "",
    "serviceAccount": ""
    }

    firebase = pyrebase.initialize_app(config)  
    db = firebase.database()
    return db

def createLocation(e, addr):
	e.child("locations").push(encodeJSON(addr))

# Main script for digitizing building from address
def squareFootage(e):
	fb = setupFirebase()
	urllib3.disable_warnings()
	driver = webdriver.Chrome(executable_path=r"C:/Users/legof/Downloads/chromedriver_win32/chromedriver.exe")
	query = googleSearchPathPrefix + e + googleKey + googleAPIKey
	http = urllib3.PoolManager()
	latandlngjson = json.loads(http.request('GET', query).data.decode('utf-8'))
	lat = latandlngjson['results'][0]['geometry']['location']['lat']
	lng = latandlngjson['results'][0]['geometry']['location']['lng']
	testquery = 'https://www.openstreetmap.org/query?lat=' + str(lat) + '&lon=' + str(lng)
	locationURL = waitForID(driver,testquery)
	reverseGeohtml = http.request('GET', locationURL)
	html = BeautifulSoup(reverseGeohtml.data, 'html.parser')
	for a in html.select('a'):
		if a.has_attr('class') and 'node' in a['class']:
			gpsFromNode(http,a['href'])
	createLocation(fb,e)
	driver.quit()
	return calculateArea()