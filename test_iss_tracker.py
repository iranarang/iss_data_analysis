import pytest
import math
from datetime import datetime
from iss_tracker import calculate_speed, find_closest_time, get_epochs, get_specific_epoch, get_instant_speed
import requests
import xmltodict

@pytest.fixture
def data():
    return {
        'ndm': {
            'oem': {
                'body': {
                    'segment': {
                        'metadata': {
                            'START_TIME': '2024-047T12:00:00.000Z',
                            'STOP_TIME': '2024-062T12:00:00.000Z'
                        },
                        'data': {
                            'stateVector': [
                                {
                                    'EPOCH': '2024-047T12:00:00.000Z',
                                    'X': {'#text': '1', 'units': 'km'},
                                    'Y': {'#text': '2', 'units': 'km'},
                                    'Z': {'#text': '3', 'units': 'km'},
                                    'X_DOT': {'#text': '4', 'units': 'km/s'},
                                    'Y_DOT': {'#text': '5', 'units': 'km/s'},
                                    'Z_DOT': {'#text': '6', 'units': 'km/s'}
                                },
                                {
                                    'EPOCH': '2024-058T22:04:00.000Z',
                                    'X': {'#text': '7', 'units': 'km'},
                                    'Y': {'#text': '8', 'units': 'km'},
                                    'Z': {'#text': '9', 'units': 'km'},
                                    'X_DOT': {'#text': '10', 'units': 'km/s'},
                                    'Y_DOT': {'#text': '11', 'units': 'km/s'},
                                    'Z_DOT': {'#text': '12', 'units': 'km/s'}
                                }
                            ]
                        }
                    }
                }
            }
        }
    }

current_time_str = "2024-02-19 12:00:00.000000"
current_time = datetime.strptime(current_time_str, '%Y-%m-%d %H:%M:%S.%f')

response_epochs = requests.get('http://127.0.0.1:8080/epochs')
data_epochs = response_epochs.json()
print(data_epochs['ndm']['oem']['body']['segment']['data']['stateVector'][0]['EPOCH'])
a_representative_epoch = data_epochs['ndm']['oem']['body']['segment']['data']['stateVector'][0]['EPOCH']

#a_representative_epoch = response_epochs.content[0]

def test_route_epochs():
    assert response_epochs.status_code == 200
    assert isinstance(response_epochs.json(), dict) == True

def test_specific_epoch_route():
    response_epoch = requests.get(f'http://127.0.0.1:8080/epochs/{a_representative_epoch}')

    assert response_epoch.status_code == 200
    assert isinstance(response_epoch.json(), dict) == True

def test_specific_epoch_speed_route():
    response_epoch_speed = requests.get(f'http://127.0.0.1:8080/epochs/{a_representative_epoch}/speed')

    assert response_epoch_speed.status_code == 200
    assert isinstance(float(response_epoch_speed.content.decode()), float)


# def test_specific_epoch_speed_route_not_found():
#     response_epoch_speed = requests.get(f'http://127.0.0.1:8080/epochs/test_epoch/speed')

#     assert response_epoch_speed.status_code == 200
#     assert not isinstance(response_epoch_speed.content.decode(), dict)


def test_route_header():
    response = requests.get('http://127.0.0.1:8080/header')
    assert response.status_code == 200
    assert isinstance(response.json(), dict) == True

def test_route_comment():
    response = requests.get('http://127.0.0.1:8080/comment')
    assert response.status_code == 200
    assert isinstance(response.json(), list) == True

def test_route_metadata():
    response = requests.get('http://127.0.0.1:8080/metadata')
    assert response.status_code == 200
    assert isinstance(response.json(), dict) == True

def test_route_now():
    response = requests.get('http://127.0.0.1:8080/now')
    assert response.status_code == 200
    assert isinstance(response.json(), dict) == True

def test_route_location():
    response = requests.get(f'http://127.0.0.1:8080/epochs/{a_representative_epoch}/location')
    assert response.status_code == 200
    print(response.json())
    assert isinstance(response.json(), dict) == True

def test_calculate_speed():
    state_vector = {
        'X_DOT': {'#text': '3', 'units': 'km/s'},
        'Y_DOT': {'#text': '4', 'units': 'km/s'},
        'Z_DOT': {'#text': '5', 'units': 'km/s'}
    }

    expected_speed = (3 ** 2 + 4 ** 2 + 5 ** 2) ** 0.5

    calculated_speed = calculate_speed(state_vector)

    assert calculated_speed == expected_speed

def test_find_closest_time(data):
    expected_closest_epoch = {
        'EPOCH': '2024-047T12:00:00.000Z',
        'X': {'#text': '1', 'units': 'km'},
        'Y': {'#text': '2', 'units': 'km'},
        'Z': {'#text': '3', 'units': 'km'},
        'X_DOT': {'#text': '4', 'units': 'km/s'},
        'Y_DOT': {'#text': '5', 'units': 'km/s'},
        'Z_DOT': {'#text': '6', 'units': 'km/s'}
    }

    expected_closest_speed = math.sqrt(4 ** 2 + 5 ** 2 + 6 ** 2)
    closest_epoch, closest_speed = find_closest_time(data, current_time)

    assert closest_epoch is not None
    assert closest_epoch == expected_closest_epoch
    assert closest_speed == expected_closest_speed



if __name__ == "__main__":
    pytest.main()
