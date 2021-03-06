# smartmirror.py
# requirements
# requests, feedparser, traceback, Pillow

from Tkinter import *
import locale
import threading
import time
import locale
import requests
import json
import traceback
import feedparser
import serial
import subprocess #checks if camera connected
from time import sleep
#from serial import SerialException
from PIL import Image, ImageTk
from contextlib import contextmanager
#classes stored in utilites below
from utilities.userData.data import Data
from utilities.facematch.FaceMatch import FaceMatch
from utilities.septa import Septa
from contextlib import contextmanager #check http://preshing.com/20110920/the-python-with-statement-by-example/
from serial import SerialException
LOCALE_LOCK = threading.Lock()

ui_locale = "en_US.utf8" # e.g. 'fr_FR' fro French, '' as default
time_format = 12 # 12 or 24
date_format = "%b %d, %Y" # check python doc for strftime() for options
news_country_code = 'us'
weather_api_token = 'fbbdfae3c5f26c016c543398fc7f8cbf' # create account at https://darksky.net/dev/
weather_lang = 'en' # see https://darksky.net/dev/docs/forecast for full list of language parameters values
weather_unit = 'us' # see https://darksky.net/dev/docs/forecast for full list of unit parameters values
latitude = None # Set this if IP location lookup does not work for you (must be a string)
longitude = None # Set this if IP location lookup does not work for you (must be a string)
xlarge_text_size = 94
large_text_size = 48
medium_text_size = 28
small_text_size = 18
#Serial port parameters
serial_speed = 9600
serial_port = '/dev/rfcomm0'
camera_folder = '/home/pi/Smart-Mirror/test/pictures_faces'
#setpa
############
#Septa API website
#http://www3.septa.org/hackathon/
septa_API = "http://www3.septa.org/hackathon/Arrivals"
stationID = 90815
numTrains = 5 #number of scheduled results
parameters = {"req1": stationID, "req2": numTrains} #req1 = Septa train station code / req2 number of results
direction = 1 # 0 for north / 1 for south
traintime = 1 # temp, used to parse out train schedules from numTrains (can only go up to numTrains)


#Bluetooth-Serial connection check#
#############
send = 1
try:
    ser = serial.Serial(serial_port, serial_speed, timeout=1)
    print "Bluetooth Connected"
except serial.SerialException:
     print "No connection to the bluetooth device could be established"
     send=0
##############

#CAMERA CHECK#
##############
camera = subprocess.check_output(["vcgencmd","get_camera"])
#int(camera.strip()[-1]) #gets only 0 or 1 from detected status
section = camera.split(" ")[1]
detector = section.split("=")[-1]
print detector
if (int(detector)==1):
    print "Camera Detected"
    print camera
else:
    print "Camera not detected"
    print camera
##############


#@contextmanager
def setlocale(name): #thread proof function to work with locale
    print "locale " + name
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, name)
        finally:
            locale.setlocale(locale.LC_ALL, saved)

# maps open weather icons to
# icon reading is not impacted by the 'lang' parameter
icon_lookup = {
    'clear-day': "assets/Sun.png",  # clear sky day
    'wind': "assets/Wind.png",   #wind
    'cloudy': "assets/Cloud.png",  # cloudy day
    'partly-cloudy-day': "assets/PartlySunny.png",  # partly cloudy day
    'rain': "assets/Rain.png",  # rain day
    'snow': "assets/Snow.png",  # snow day
    'snow-thin': "assets/Snow.png",  # sleet day
    'fog': "assets/Haze.png",  # fog day
    'clear-night': "assets/Moon.png",  # clear sky night
    'partly-cloudy-night': "assets/PartlyMoon.png",  # scattered clouds night
    'thunderstorm': "assets/Storm.png",  # thunderstorm
    'tornado': "assests/Tornado.png",    # tornado
    'hail': "assests/Hail.png"  # hail
}


class FaceRec:

    def find(self):
	print detector
        if (int(detector)==1):
            fm=FaceMatch(camera_folder)
            name=fm.getName()
        else:
            name=("camera not connected")
        return name


class TempTest(Frame):

    def __init__(self, parent,  *args, **kwargs):
	Frame.__init__(self, parent, *args, **kwargs)
        self.temp_data = StringVar()
        self.name = StringVar()
        self.weight = IntVar()
        if(int(send)==1):   #if bluetooth connected
	    self.measure()
	    print "reading data"
        self.Person()
        self.StoreData()
        self.createWidgets()
    def measure(self):

		# Request data and read the answer
        ser.write("t")
        print("this is t")
        data = ser.readline()
        print str(data)
		# If the answer is not empty, process & display data
        if (data != ""):
            processed_data = data.split(",")
	    self.temp_data.set("Temperature: " + str(data))
#	    self.temperature.pack(side=LEFT, anchor=W)

    def Person(self):
        try:
            pt=FaceRec()
            name = pt.find()  #calls fuction from FaceRec
            print ("name is " + name)
        except:
            name = "Person not found"

        self.name.set("Hello, " + name)

    def StoreData(self):
	try:
            store=Data()
            store.storeData(self.name, self.weight)
        except:
            print("data not stored")

    def createWidgets(self):
        self.name = Label(self, textvariable=self.name, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.name.pack(side=TOP, anchor=W)
       # self.temperature = Label(self, textvariable=self.temp_data, font=('Helvetica', small_text_size), fg="white", bg="black")
       # self.temperature.pack(side=TOP, anchor=E)

class Trains(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg="black")
        
        self.septaFrm = Frame(self, bg="black")
        self.septaFrm.pack(side=TOP, anchor = W)
        self.train1Lbl = Label(self, font=('Helvetica', small_text_size), justify = LEFT, fg="white", bg="black")
        self.train1Lbl.pack(side=TOP, anchor=E)
        self.train2Lbl = Label(self, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.train2Lbl.pack(side=TOP, anchor=W)
        self.getTimes()
        
    def getTimes(self):
      
        if (direction ==1):
            direc = "Southbound"
        else:
            direc = "Northbound"

        x = Septa()
        y = x.traintimes(septa_API, parameters, direction, traintime)
        z = x.traintimes(septa_API, parameters, direction, 2)

        trainline = ("Line: " +y[7])
        destination = ("Destination: " +y[3])
        depart = ("Departure: " + y[1][11:16])
        status = ("Status: " + z[21])
        filtered = [direc, trainline, destination, depart, status]
        filtered = "\n".join(filtered)
        print(filtered) 
        self.train1Lbl.config(text=(filtered))
#        self.train1Lbl.config(text=destination1)
        #self.train1Lbl.config(text=)
        #self.train1Lbl.config(text=filtered[3])
        trainline2 = z[7]
        destination2 = z[3]
        depart2 = z[1][11:16]
        status2 = z[21]
        filtered2 = (trainline2, destination2, depart2, status2)
        #self.train2Lbl.config(text=filtered[0])
        #self.train2Lbl.config(text=filtered[1])
        #self.train2Lbl.config(text=filtered[2])
        #self.train2Lbl.config(text=filtered[3])




class Clock(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        # initialize time label
        self.time1 = ''
        self.timeLbl = Label(self, font=('Helvetica', large_text_size), fg="white", bg="black")
        self.timeLbl.pack(side=TOP, anchor=E)
        # initialize day of week
        self.day_of_week1 = ''
        self.dayOWLbl = Label(self, text=self.day_of_week1, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.dayOWLbl.pack(side=TOP, anchor=E)
        # initialize date label
        self.date1 = ''
        self.dateLbl = Label(self, text=self.date1, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.dateLbl.pack(side=TOP, anchor=E)
        self.tick()

    def tick(self):
#        print "test -->: " + ui_locale
      #  with setlocale('en_US.utf8'):
        if time_format == 12:
            time2 = time.strftime('%I:%M %p') #hour in 12h format
        else:
            time2 = time.strftime('%H:%M') #hour in 24h format
        if 1:
            day_of_week2 = time.strftime('%A')
            date2 = time.strftime(date_format)
            # if time string has changed, update it
            if time2 != self.time1:
                self.time1 = time2
                self.timeLbl.config(text=time2)
            if day_of_week2 != self.day_of_week1:
                self.day_of_week1 = day_of_week2
                self.dayOWLbl.config(text=day_of_week2)
            if date2 != self.date1:
                self.date1 = date2
                self.dateLbl.config(text=date2)
            # calls itself every 200 milliseconds
            # to update the time display as needed
            # could use >200 ms, but display gets jerky
            self.timeLbl.after(200, self.tick)


class Weather(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.temperature = ''
        self.forecast = ''
        self.location = ''
        self.currently = ''
        self.icon = ''
        self.degreeFrm = Frame(self, bg="black")
        self.degreeFrm.pack(side=TOP, anchor=W)
        self.temperatureLbl = Label(self.degreeFrm, font=('Helvetica', xlarge_text_size), fg="white", bg="black")
        self.temperatureLbl.pack(side=LEFT, anchor=N)
        self.iconLbl = Label(self.degreeFrm, bg="black")
        self.iconLbl.pack(side=LEFT, anchor=N, padx=20)
        self.currentlyLbl = Label(self, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.currentlyLbl.pack(side=TOP, anchor=W)
        self.forecastLbl = Label(self, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.forecastLbl.pack(side=TOP, anchor=W)
        self.locationLbl = Label(self, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.locationLbl.pack(side=TOP, anchor=W)
        self.get_weather()

    def get_ip(self):
        try:
            ip_url = "http://jsonip.com/"
            req = requests.get(ip_url)
            ip_json = json.loads(req.text)
            return ip_json['ip']
        except Exception as e:
            traceback.print_exc()
            return "Error: %s. Cannot get ip." % e

    def get_weather(self):
        try:

            if latitude is None and longitude is None:
                # get location
                location_req_url = "http://freegeoip.net/json/%s" % self.get_ip()
                r = requests.get(location_req_url)
                location_obj = json.loads(r.text)

                lat = location_obj['latitude']
                lon = location_obj['longitude']

                location2 = "%s, %s" % (location_obj['city'], location_obj['region_code'])

                # get weather
                weather_req_url = "https://api.darksky.net/forecast/%s/%s,%s?lang=%s&units=%s" % (weather_api_token, lat,lon,weather_lang,weather_unit)
            else:
                location2 = ""
                # get weather
                weather_req_url = "https://api.darksky.net/forecast/%s/%s,%s?lang=%s&units=%s" % (weather_api_token, latitude, longitude, weather_lang, weather_unit)

            r = requests.get(weather_req_url)
            weather_obj = json.loads(r.text)

            degree_sign= u'\N{DEGREE SIGN}'
            temperature2 = "%s%s" % (str(int(weather_obj['currently']['temperature'])), degree_sign)
            currently2 = weather_obj['currently']['summary']
            forecast2 = weather_obj["hourly"]["summary"]

            icon_id = weather_obj['currently']['icon']
            icon2 = None

            if icon_id in icon_lookup:
                icon2 = icon_lookup[icon_id]

            if icon2 is not None:
                if self.icon != icon2:
                    self.icon = icon2
                    image = Image.open(icon2)
                    image = image.resize((100, 100), Image.ANTIALIAS)
                    image = image.convert('RGB')
                    photo = ImageTk.PhotoImage(image)

                    self.iconLbl.config(image=photo)
                    self.iconLbl.image = photo
            else:
                # remove image
                self.iconLbl.config(image='')

            if self.currently != currently2:
                self.currently = currently2
                self.currentlyLbl.config(text=currently2)
            if self.forecast != forecast2:
                self.forecast = forecast2
                self.forecastLbl.config(text=forecast2)
            if self.temperature != temperature2:
                self.temperature = temperature2
                self.temperatureLbl.config(text=temperature2)
            if self.location != location2:
                if location2 == ", ":
                    self.location = "Cannot Pinpoint Location"
                    self.locationLbl.config(text="Cannot Pinpoint Location")
                else:
                    self.location = location2
                    self.locationLbl.config(text=location2)
        except Exception as e:
            traceback.print_exc()
            print "Error: %s. Cannot get weather." % e

        self.after(600000, self.get_weather)

    @staticmethod
    def convert_kelvin_to_fahrenheit(kelvin_temp):
        return 1.8 * (kelvin_temp - 273) + 32


class News(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, *args, **kwargs)
        self.config(bg='black')
        self.title = 'News!' # 'News' is more internationally generic
        self.newsLbl = Label(self, text=self.title, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.newsLbl.pack(side=TOP, anchor=W)
        self.headlinesContainer = Frame(self, bg="black")
        self.headlinesContainer.pack(side=TOP, anchor=S)
        self.get_headlines()

    def get_headlines(self):
        try:
            # remove all children
            for widget in self.headlinesContainer.winfo_children():
                widget.destroy()
            if news_country_code == None:
                headlines_url = "https://news.google.com/news?ned=us&output=rss"
            else:
                headlines_url = "https://news.google.com/news?ned=%s&output=rss" % news_country_code

            feed = feedparser.parse(headlines_url)

            for post in feed.entries[0:5]:
                headline = NewsHeadline(self.headlinesContainer, post.title)
                headline.pack(side=TOP, anchor=W)
        except Exception as e:
            traceback.print_exc()
            print "Error: %s. Cannot get news." % e

        self.after(600000, self.get_headlines)


class NewsHeadline(Frame):
    def __init__(self, parent, event_name=""):
        Frame.__init__(self, parent, bg='black')

        image = Image.open("assets/Newspaper.png")
        image = image.resize((25, 25), Image.ANTIALIAS)
        image = image.convert('RGB')
        photo = ImageTk.PhotoImage(image)

        self.iconLbl = Label(self, bg='black', image=photo)
        self.iconLbl.image = photo
        self.iconLbl.pack(side=LEFT, anchor=W)

        self.eventName = event_name
        self.eventNameLbl = Label(self, text=self.eventName, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.eventNameLbl.pack(side=LEFT, anchor=N)

class FullscreenWindow:

    def __init__(self):
        self.tk = Tk()
        self.tk.configure(background='black')
        self.topFrame = Frame(self.tk, background = 'black')
	self.centerFrame = Frame(self.tk, background = 'black')
        self.bottomFrame = Frame(self.tk, background = 'black')
        self.topFrame.pack(side = TOP, fill=BOTH, expand = YES)
	self.centerFrame.pack(side = TOP, fill=BOTH, expand = YES)
        self.bottomFrame.pack(side = BOTTOM, fill=BOTH, expand = YES)
        self.state = False
        self.tk.bind("<Return>", self.toggle_fullscreen)
        self.tk.bind("<Escape>", self.end_fullscreen)
	# Name
        # clock
        self.clock = Clock(self.topFrame)
        self.clock.pack(side=RIGHT, anchor=N, padx=10, pady=10)
        # weather
        self.weather = Weather(self.topFrame)
        self.weather.pack(side=LEFT, anchor=N, padx=10, pady=10)
	#temp
#	self.temp = TempTest(self.centerFrame)
#	self.temp.pack(side=LEFT, anchor=W, padx=10)
        #setpa
        self.septa = Trains(self.centerFrame)
        self.septa.pack(side=LEFT, anchor=N, padx=10)
        # news
        self.news = News(self.bottomFrame)
        self.news.pack(side=LEFT, anchor=S, padx=10, pady=10)

    def toggle_fullscreen(self, event=None):
        self.state = not self.state  # Just toggling the boolean
        self.tk.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.tk.attributes("-fullscreen", False)
        return "break"

if __name__ == '__main__':

    w = FullscreenWindow()
    w.tk.mainloop()
