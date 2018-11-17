from flask import Flask, request
from math import sin, cos, atan, sqrt, pi
import numpy as np
from flask_pymongo import PyMongo
import datetime
import random
from flask.json import jsonify

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/Soopa"
mongo = PyMongo(app)

earthRadius = 6371


# Get Great Circle Distance between 2 coordinates
def lat_lng_distance(lat1, lng1, lat2, lng2):
    lat1 = lat1 * pi / 180
    lat2 = lat2 * pi / 180
    lng1 = lng1 * pi / 180
    lng2 = lng2 * pi / 180
    radian_distance = atan(sqrt(((cos(lat2) * sin(lng1 - lng2)) ** 2 + (
            cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(lng1 - lng2)) ** 2)) / (
                                   sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lng1 - lng2)))
    if radian_distance < 0:
        radian_distance += pi
    return earthRadius * radian_distance


building_heights_data = []

heightData = np.genfromtxt("building_heights.csv", delimiter=",")

for building in heightData:
    building_heights_data.append((float(building[0]), float(building[1]), float(building[2])))


# Building Height from Lat Long and radius
@app.route("/building_height/")
def building_heights():
    current_lat = float(request.args.get("lat"))
    current_lng = float(request.args.get("lng"))
    radius = float(request.args.get("radius"))

    buildings = get_tallest_buildings(current_lat, current_lng, radius, 3, True)

    # Convert to JSON

    return jsonify(buildings)


def get_tallest_buildings(current_lat, current_lng, radius, count, dict=False):
    buildings_in_radius = [(lat, lng, height) for (lat, lng, height) in building_heights_data if
                           (lat_lng_distance(lat, lng, current_lat, current_lng) <= radius)]

    # Filter for top 3
    top_buildings_in_radius = sorted(buildings_in_radius, key=lambda x: x[2], reverse=True)[:count]

    if dict:
        json_building_list = []
        for (lat, lng, height) in top_buildings_in_radius:
            json_building_list.append({
                "lat": lat,
                "lng": lng,
                "height": height
            })
        return json_building_list

    return top_buildings_in_radius


# Active Crimes (Last 5 minutes)
@app.route("/active_crimes")
def get_active_crimes():
    current_lat = float(request.args.get("lat"))
    current_lng = float(request.args.get("lng"))
    radius = float(request.args.get("radius"))

    active_crimes = mongo.db.crimes.find(
        {"datetime": {"$gt": datetime.datetime.now() - datetime.timedelta(minutes=5)}, "solved_time": {"$ne": 0}})

    # Filter based on radius
    active_crimes_in_radius = [active_crime for active_crime in active_crimes if (
            lat_lng_distance(active_crime["lat"], active_crime["lng"], current_lat, current_lng) <= radius)]

    for crime in active_crimes_in_radius:
        del crime["_id"]
        crime["vantage_points"] = get_tallest_buildings(crime["lat"], crime["lng"], 0.2, 3, True)

    return jsonify(active_crimes_in_radius)


@app.route("/new_crime")
def new_crime():
    lat = np.random.uniform(51.29150416286872, 51.69031564760695)
    lng = np.random.uniform(-0.49931701722075333, 0.3226031423929305)
    crime_type = random.choice(["Anti-social behaviour",
                          "Bicycle theft",
                          "Burglary",
                          "Criminal damage and arson",
                          "Drugs",
                          "Other crime",
                          "Other theft",
                          "Possession of weapons",
                          "Public order",
                          "Robbery",
                          "Shoplifting",
                          "Theft from the person",
                          "Vehicle crime",
                          "Violence and sexual offences"])
    severity = np.random.randint(1, 10)
    return str(mongo.db.crimes.insert_one({
        "type": crime_type,
        "datetime": datetime.datetime.now(),
        "severity": severity,
        "lat": lat,
        "lng": lng,
        "solved_by": "",
        "solved_at": 0
    }).inserted_id)

# User Login
@app.route("/user/<username>")
def user_login(username):
    users = mongo.db.heroes.find_one({"Name": username})
    return jsonify(users)
