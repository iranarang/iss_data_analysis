#!/usr/bin/env python3

import requests
import xmltodict
from datetime import datetime
import math
import logging
import numpy as np
from flask import Flask, request, jsonify
from geopy.geocoders import Nominatim
import time
from astropy import coordinates
from astropy import units
from astropy.time import Time

# Used ChatGPT to fix errors

app = Flask(__name__)

response = requests.get(url='https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml')
data = xmltodict.parse(response.content)

logging.basicConfig(level=logging.DEBUG)


def calculate_speed(state_vector: list) -> float:
    """
    This function calculates the speed within at the selected stateVector.

    Args:
        state_vector (list): Contains all of the information at the selected stateVector.

    Returns:
        speed (float): The speed at the selected stateVector.
    """

    x_dot = float(state_vector['X_DOT']['#text'])
    y_dot = float(state_vector['Y_DOT']['#text'])
    z_dot = float(state_vector['Z_DOT']['#text'])

    if state_vector == None:
        logging.error(f"Couldn't find epoch data.")

    speed = math.sqrt(x_dot ** 2 + y_dot ** 2 + z_dot ** 2)

    return speed

def find_closest_time(data: dict, current_time: str) -> list:
    """
    This function calculates the epoch with the time closest to the current time as well as the speed at that time.

    Args:
        data (dict): A dictionary containing positional and velocity data for the International Space Station (ISS).
        current_time (str): A string containing the current time. 

    Returns:
        closest_epoch (list): The epoch with the time closest to the current time.
        closest_speed (float): The speed at that time.
    """

    state_vectors = data['ndm']['oem']['body']['segment']['data']['stateVector']

    closest_epoch = None
    min_time_diff = float('inf')

    for state_vector in state_vectors:
        epoch_str = state_vector['EPOCH']
        epoch_time = datetime.strptime(epoch_str, '%Y-%jT%H:%M:%S.%fZ')
        time_diff = abs((current_time - epoch_time).total_seconds())

        if time_diff < min_time_diff:
            min_time_diff = time_diff
            closest_epoch = state_vector

    closest_speed = calculate_speed(closest_epoch)

    return closest_epoch, closest_speed


@app.route('/epochs', methods=['GET'])
def get_epochs() -> str:
    """
    This function returns the desired data from the XML file. It can return both the entire data set and a specific section of the data.

    Returns:
        data (str): The entire data set if unspecified.
        modified xml (str): The XML data with modified parameters if specified.

    """

    limit = request.args.get('limit', default=None)
    offset = request.args.get('offset', default=None)

    response = requests.get(url='https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml')

    data = response.content
    
    if limit is None and offset is None:
        data = xmltodict.parse(data)
        data = jsonify(data)
        return data
    else:
        try:
            if limit is not None:
                limit = int(limit)
            if offset is not None:
                offset = int(offset)
        except ValueError:
            return "Invalid parameter(s), must be an integer."
        xml_data = xmltodict.parse(data)
        state_vectors = xml_data['ndm']['oem']['body']['segment']['data']['stateVector']
        if limit is None:
            limit = len(state_vectors) - offset
        if offset is None:
            offset = 0
        if (limit+offset) > len(state_vectors):
            return "Invalid parameter(s), must be in the data set."
        
        modified_data = state_vectors[offset:(offset + limit)]

        new_xml = {'body': {}}
        modified_xml = new_xml['body']['stateVector'] = modified_data
        modified_xml = jsonify(modified_xml)
        #modified_xml = xmltodict.unparse(new_xml, pretty=True)

        return modified_xml


@app.route('/epochs/<epoch>', methods=['GET'])
def get_specific_epoch(epoch: str) -> str:
    """
    This function outputs the data in the stateVector at the designated epoch.

    Args:
        epoch (str): The inputted epoch.

    Returns:
        state_vector (str): The data at the designated epoch.
    """

    for state_vector in data['ndm']['oem']['body']['segment']['data']['stateVector']:
        if state_vector['EPOCH'] == epoch:
            return jsonify(state_vector)

    return '<error>Epoch not found</error>'


@app.route('/epochs/<epoch>/speed', methods=['GET'])
def get_instant_speed(epoch):
    """
    This function calculates the speed for the epoch

    Args:
        epoch (str): The inputted epoch.

    Returns:
        speed (str): the calculated speed at the epoch if epoch exists
        '<error>Epoch not found</error>' if epoch does not exist
    """

    for state_vector in data['ndm']['oem']['body']['segment']['data']['stateVector']:
        if state_vector['EPOCH'] == epoch:
            speed = calculate_speed(state_vector)
            
            return f'{speed}'

    return '<error>Epoch not found</error>'


@app.route('/comment', methods=['GET'])
def get_comment_data():
    """
    This function returns information included in the 'comment' section of the data.

    Returns:
        comment_data (json): comments from the data.
    """
    comment_data = data['ndm']['oem']['body']['segment']['data']['COMMENT']

    return jsonify(comment_data)

@app.route('/header', methods=['GET'])
def get_header_data():
    """
    This function returns information included in the 'header' section of the data.

    Returns:
        header_data (json): header data from the dataset
    """
    header_data = data['ndm']['oem']['header']

    return jsonify(header_data)

@app.route('/metadata', methods=['GET'])
def get_metadata():

    """
    This function returns information included in the 'metadata' section of the data.

    Returns:
        metadata(json): metadata for the dataset segment
    """
    metadata = data['ndm']['oem']['body']['segment']['metadata']

    return jsonify(metadata)

@app.route('/epochs/<epoch>/location', methods=['GET'])
def get_location(epoch):

    """
    This function finds the location(lat, long, altitude, geolocation) for the epoch

    Args:
        epoch (str): The inputted epoch.

    Returns:
       json: returns a json containing location(lat, long, altitude, geolocation)
    """
    R = 6378
    

    for state_vector in data['ndm']['oem']['body']['segment']['data']['stateVector']:
        if state_vector['EPOCH'] == epoch:
            x = float(state_vector['X']['#text'])
            y = float(state_vector['Y']['#text'])
            z = float(state_vector['Z']['#text'])

            this_epoch=time.strftime('%Y-%m-%d %H:%m:%S', time.strptime(state_vector['EPOCH'][:-5], '%Y-%jT%H:%M:%S'))
            
            cartrep = coordinates.CartesianRepresentation([x, y, z], unit=units.km)
            gcrs = coordinates.GCRS(cartrep, obstime=this_epoch) 
            itrs = gcrs.transform_to(coordinates.ITRS(obstime=this_epoch))
            loc = coordinates.EarthLocation(*itrs.cartesian.xyz)
            
            lat = loc.lat.value
            long = loc.lon.value
            altitude = loc.height.value

            geolocator = Nominatim(user_agent="iss_locator")
            location = geolocator.reverse(f'{lat}, {long}')
            if location == None:
                location = "Located in the ocean"
                
            return jsonify({
                'latitude': str(lat),
                'longitude': str(long), 
                'altitude': f'{str(altitude)} km', 
                'geolocation': f'{str(location)}',
            })
            
    return "error"


@app.route('/now', methods=['GET'])
def get_current_location():

    """
    This function finds the current location(lat, long, altitude, instaneous speed) for the epoch based on current time

    Args:
        epoch (str): The inputted epoch.

    Returns:
       json: returns a json containing location(lat, long, altitude, geolocation)
    """

    current_time = datetime.now()
    closest_epoch, closest_speed = find_closest_time(data, current_time)
    
    closest_epoch_time = closest_epoch['EPOCH'] 
    
    R = 6378
    for state_vector in data['ndm']['oem']['body']['segment']['data']['stateVector']:
        if state_vector['EPOCH'] == closest_epoch_time:
            x = float(state_vector['X']['#text'])
            y = float(state_vector['Y']['#text'])
            z = float(state_vector['Z']['#text'])
            
            this_epoch=time.strftime('%Y-%m-%d %H:%m:%S', time.strptime(state_vector['EPOCH'][:-5], '%Y-%jT%H:%M:%S'))
            
            cartrep = coordinates.CartesianRepresentation([x, y, z], unit=units.km)
            gcrs = coordinates.GCRS(cartrep, obstime=this_epoch) 
            itrs = gcrs.transform_to(coordinates.ITRS(obstime=this_epoch))
            loc = coordinates.EarthLocation(*itrs.cartesian.xyz)
            
            lat = loc.lat.value
            long = loc.lon.value
            altitude = loc.height.value

            geolocator = Nominatim(user_agent="iss_locator")
            location = geolocator.reverse(f'{lat}, {long}')
            if location == None:
                location = "Located in the ocean"

    return jsonify({
        'instantaneous speed': closest_speed,
        'latitude': str(lat),
        'longitude': str(long), 
        'altitude': f'{str(altitude)} km', 
        'geolocation': f'{str(location)}', 
    })

if __name__ == "__main__":

    app.run(host='0.0.0.0', port=8080, debug=True)


