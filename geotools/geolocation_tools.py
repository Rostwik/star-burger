import requests


def fetch_coordinates(apikey, address):
    payload = {
        'geocode': address,
        'apikey': apikey,
        'format': 'json',
    }
    url = 'https://geocode-maps.yandex.ru/1.x'

    try:
        response = requests.get(url, params=payload)
        response.raise_for_status()
        found_places = response.json()['response']['GeoObjectCollection']['featureMember']

        if not found_places:
            return None

        most_relevant = found_places[0]
        lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
        return lon, lat

    except requests.HTTPError:
        return None

    except requests.JSONDecodeError:
        return None

    except KeyError:
        return None
