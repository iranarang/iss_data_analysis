import pytest
from datetime import datetime
import requests


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



if __name__ == "__main__":
    pytest.main()
