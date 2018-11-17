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
max_lat = 51.69031564760695
min_lat = 51.29150416286872
max_lng = 0.3226031423929305
min_lng = -0.49931701722075333
lat_grid_steps = 92
lng_grid_steps = 45

lat_grid_size = (max_lat - min_lat) / lat_grid_steps
lng_grid_size = (max_lng - min_lng) / lng_grid_steps

severity = {'Violence and sexual offences': 10, 'Anti-social behaviour': 3, 'Burglary': 5,
            'Criminal damage and arson': -1, 'Other theft': -1, 'Possession of weapons': 7,
            'Robbery': 8, 'Theft from the person': 8, 'Vehicle crime': 5, 'Other crime': -1,
            'Public order': 9, 'Shoplifting': 2, 'Drugs': 1, 'Bicycle theft': 10}


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
    superhero = request.args.get("superhero")

    active_crimes = mongo.db.crimes.find(
        {"datetime": {"$gt": datetime.datetime.now() - datetime.timedelta(minutes=5)}, "solved_time": {"$ne": 0}})

    # Filter based on radius
    active_crimes_in_radius = [active_crime for active_crime in active_crimes if (
            lat_lng_distance(active_crime["lat"], active_crime["lng"], current_lat, current_lng) <= radius)]

    for crime in active_crimes_in_radius:
        del crime["_id"]
        crime["vantage_points"] = get_tallest_buildings(crime["lat"], crime["lng"], 0.2, 3, True)
        crime["crime_duration"] = get_crime_duration_estimate(superhero, crime["type"])

    return jsonify(active_crimes_in_radius)


def get_crime_duration_estimate(superhero, crime_type):
    crimes = list(mongo.db.crimes.find({
        "solved_by": superhero,
        "type": crime_type
    }))

    times = [(crime["solved_at"] - crime["datetime"]).total_seconds() for crime in crimes]

    estimate = np.nanmean(times) / 60

    return estimate


@app.route("/new_crime")
def new_crime():
    crime = {}
    crime['datetime'] = datetime.datetime.now()
    crime['lng'] = np.random.uniform(-0.49931701722075333, 0.3226031423929305)
    crime['lat'] = np.random.uniform(51.29150416286872, 51.69031564760695)
    crime['type'] = np.random.choice(list(severity.keys()))

    lat_param = request.args.get("lat")
    if lat_param is not None:
        crime["lat"] = float(lat_param)

    lng_param = request.args.get("lat")
    if lng_param is not None:
        crime["lat"] = float(lat_param)

    sev = severity[crime["type"]]
    if sev != -1:
        crime['severity'] = sev
    else:
        crime['severity'] = np.random.randint(3, 8)

    crimes = mongo.db.crimes.find({
        "type": crime.get('type')
    })

    times = [(crime["solved_at"] - crime["datetime"]).total_seconds() for crime in crimes]

    solve_time = np.nanmean(times)
    crime['solved_at'] = crime['datetime'] + datetime.timedelta(seconds=solve_time)

    crime['solved_by'] = np.random.choice(['Spiderman', 'Wonder Woman', 'Ironman', 'Batman', 'Aquaman'])

    return str(mongo.db.crimes.insert_one(crime).inserted_id)


@app.route("/new_crime_unsolved")
def new_crime_unsolved():
    crime = {}
    crime['datetime'] = datetime.datetime.now()
    crime['lng'] = np.random.uniform(-0.49931701722075333, 0.3226031423929305)
    crime['lat'] = np.random.uniform(51.29150416286872, 51.69031564760695)
    crime['type'] = np.random.choice(list(severity.keys()))

    lat_param = request.args.get("lat")
    if lat_param is not None:
        crime["lat"] = float(lat_param)

    lng_param = request.args.get("lat")
    if lng_param is not None:
        crime["lat"] = float(lat_param)

    sev = severity[crime["type"]]
    if sev != -1:
        crime['severity'] = sev
    else:
        crime['severity'] = np.random.randint(3, 8)

    crimes = mongo.db.crimes.find({
        "type": crime.get('type')
    })

    crime['solved_at'] = ""

    crime['solved_by'] = datetime.datetime.min

    return str(mongo.db.crimes.insert_one(crime).inserted_id)


# Heatmap data
@app.route("/heatmap")
def heatmap_data():
    # Get current heatmap data
    heatmap_grid = list(mongo.db.heatmap_grid.find({}))
    # For all crimes in the last 20 minutes, assign to nearest grid point
    recent_crimes = list(mongo.db.crimes.find(
        {"datetime": {"$gt": datetime.datetime.now() - datetime.timedelta(minutes=20)}}))

    grid_dict = {}
    grid_crime_dict = {}
    for grid in heatmap_grid:
        grid_dict[(grid["grid_x"], grid["grid_y"])] = grid
        grid_crime_dict[(grid["grid_x"], grid["grid_y"])] = []

    for crime in recent_crimes:
        nearest_x = round((crime["lat"] - min_lat) / lat_grid_size)
        nearest_y = round((crime["lng"] - min_lng) / lng_grid_size)

        grid_crime_dict[(nearest_x, nearest_y)].append(crime)
    # For each grid point, calculate average severity
    output = []
    for ((grid_x, grid_y), crimes) in grid_crime_dict.items():
        if len(crimes) != 0:
            grid = grid_dict[(grid_x, grid_y)]
            average_severity = sum(crime["severity"] for crime in crimes) / len(crimes)
            output.append((grid["centre_lat"], grid["centre_lng"], average_severity))

    # Return data
    return jsonify(output)


# User Login
@app.route("/user/<username>")
def user_login(username):
    users = mongo.db.heroes.find_one({"Name": username})
    return jsonify(users)
