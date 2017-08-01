#IMPORTANT
#It should be noted that log data does not generally line up perfectly with the start of the drone video and
#therefore the flyTimes retrieved from the logs do not correspond with the video times
#An easy way to determine the difference in time between the two forms of media is to match up the takeoff time
#by looking where the altitude first becomes positive for the drone in the .csv file

from pylab import *
import numpy as np
import struct as struct
import csv
import preparser as preparser
import simplekml

#Insert the full path name of the log file that you would like to parse as filename
fileName = "/Users/heather/Desktop/Flight Records/TXT/DJIFlightRecord_2015-08-01_[15-57-19].txt"
preparser.main(fileName)

#Each tenth of a second of flytime has a dictionary containing all of the drone's current values
array = np.load("SaveFile.npy")

coordinatesArray = []
lineArray = []
timeArray = []
latitudeArray = []
longitudeArray = []
rollArray = []
csvArray = []
newLatitudeArray = []
newLongitudeArray = []
#Heading is the same as yaw, tilt is the same as pitch, and altitude is the same as height
headingArray = []
tiltArray = []
altitudeArray = []

#This function is derived from the Haversine formula and uses the latitude and longitude of the drone
#along with its heading and the distance between it and the centerpoint of its camera to calculate the GPS coordinates
#for the centerpoint of the view of the camera
def getNewGPSCoordinates(lat1, long1, theta, distance):
	radius = 6371000
	lat1 = radians(lat1)
	long1 = radians(long1)
	theta = radians(theta)
	lat2 = arcsin(sin(lat1)*cos(distance/radius) + cos(lat1)*sin(distance/radius)*cos(theta));
	long2 = long1 + arctan2(sin(theta)*sin(distance/radius)*cos(lat1), cos(distance/radius)-sin(lat1)*sin(lat2));
	lat2 = degrees(lat2)
	long2 = degrees(long2)
	latLong = [lat2,long2]
	return latLong

for dataObject in array:
	#Create an array of flyTimes
	time = dataObject.get("flyTime")
	timeArray.append(time)

	#This creates an array of coordinates for the drone which are plotted in the .kml
	coordinate = (dataObject.get("longitude"),dataObject.get("latitude"),dataObject.get("height"))
	coordinatesArray.append(coordinate)

	#This generates an array of lines between the drone's coordinates and the coordinates that
	#the centerpoint of its camera is pointed at
	longitude = dataObject.get("longitude")
	latitude = dataObject.get("latitude")
	height = dataObject.get("height")
	pitch = dataObject.get("pitch")
	distance = 0
	theta = dataObject.get("yaw")
	if(pitch < 0):
		#Use trigonometry to calculate the distance between the drone and the camera centerpoint coordinates
		distance = tan(radians(pitch+90))*height
		latLong = getNewGPSCoordinates(latitude,longitude,theta,distance)
		newLatitude = latLong[0]
		newLongitude = latLong[1]
		height = 0
	#If the camera is not pointed down I cannot generate a gps coordinate that it is pointed at
	#therefore I set coordinate2 equal to the drone's coordinates
	else:
		newLatitude = latitude
		newLongitude = longitude
	coordinate2 = (newLongitude,newLatitude,height)
	newLatitudeArray.append(newLatitude)
	newLongitudeArray.append(newLongitude)
	lineArray.append(coordinate2)

	#The Lookat function requires a number of attributes which I retreive from the below arrays
	lookatLatitude = dataObject.get("latitude")
	latitudeArray.append(lookatLatitude)
	lookatLongitude = dataObject.get("longitude")
	longitudeArray.append(lookatLongitude)
	lookatHeading = dataObject.get("yaw")
	headingArray.append(lookatHeading)
	lookatTilt = dataObject.get("pitch")+90
	tiltArray.append(lookatTilt)
	lookatAltitude = dataObject.get("height")
	altitudeArray.append(lookatAltitude)
	rollObject = dataObject.get("roll")
	rollArray.append(rollObject)


#Create a new array of dictionaries for each timestamp that contains the newLatitude and newLongitude (calculated coordinates for centerpoint of cameraview)
for i in range(0,len(timeArray),1):
	csvDictionary = {"flyTime": timeArray[i], "longitude": longitudeArray[i], "latitude": latitudeArray[i], "height": altitudeArray[i], "pitch": tiltArray[i], "roll": rollArray[i], "yaw": headingArray[i], "newLongitude": newLongitudeArray[i], "newLatitude": newLatitudeArray[i]}
	csvArray.append(csvDictionary)


#Write all data to a csv file
keys = csvArray[0].keys()
with open('logdata.csv', 'w') as output_file:
    dict_writer = csv.DictWriter(output_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(csvArray)


#Create kml file
kml = simplekml.Kml()
#This first linestring is the path of the drone through three dimensional space
lineString = kml.newlinestring(name='Drone Path')
lineString.coords = coordinatesArray
lineString.tessellate = 1
lineString.style.linestyle.width = 2
lineString.style.linestyle.color = simplekml.Color.orange
lineString.altitudemode = simplekml.AltitudeMode.absolute
#This loop creates the linestrings that show where the centerpoint of the camera is pointed
#It also creates a view for each of the linestrings that should line up with the video view
for i in range(0,len(coordinatesArray),1):
	point1 = lineArray[i]
	point2 = coordinatesArray[i]
	time = timeArray[i]
	cameraLine = kml.newlinestring(name=str(time))
	cameraLine.coords = [point1,point2]
	cameraLine.tessellate = 1
	cameraLine.style.linestyle.width = 2
	cameraLine.style.linestyle.color = simplekml.Color.red
	cameraLine.altitudemode = simplekml.AltitudeMode.absolute
	cameraLine.lookat.latitude = latitudeArray[i]
	cameraLine.lookat.longitude = longitudeArray[i]
	cameraLine.lookat.range = 5
	cameraLine.lookat.heading = headingArray[i]
	cameraLine.lookat.tilt = tiltArray[i]
	cameraLine.lookat.altitude = altitudeArray[i]
	cameraLine.lookat.altitudemode = simplekml.AltitudeMode.absolute
kml.save("DronePath.kml")


