"""
Weather API routes - integrates with data.gov.sg for Singapore weather data.
Provides current weather, forecasts, and rainfall data for traffic overlay.
"""

from flask import Blueprint, request, jsonify
import requests
from datetime import datetime, timedelta
import os

weather_bp = Blueprint('weather', __name__)

# data.gov.sg API endpoints (no API key required)
WEATHER_2H_FORECAST = "https://api.data.gov.sg/v1/environment/2-hour-weather-forecast"
WEATHER_24H_FORECAST = "https://api.data.gov.sg/v1/environment/24-hour-weather-forecast"
WEATHER_4DAY_FORECAST = "https://api.data.gov.sg/v1/environment/4-day-weather-forecast"
RAINFALL_API = "https://api.data.gov.sg/v1/environment/rainfall"
AIR_TEMP_API = "https://api.data.gov.sg/v1/environment/air-temperature"
HUMIDITY_API = "https://api.data.gov.sg/v1/environment/relative-humidity"
PM25_API = "https://api.data.gov.sg/v1/environment/pm25"
PSI_API = "https://api.data.gov.sg/v1/environment/psi"

# Singapore region area metadata (approximate centers)
SINGAPORE_AREAS = {
    "Ang Mo Kio": {"lat": 1.3691, "lon": 103.8454, "region": "Central"},
    "Bedok": {"lat": 1.3236, "lon": 103.9273, "region": "East"},
    "Bishan": {"lat": 1.3526, "lon": 103.8352, "region": "Central"},
    "Boon Lay": {"lat": 1.3048, "lon": 103.7067, "region": "West"},
    "Bukit Batok": {"lat": 1.3590, "lon": 103.7637, "region": "West"},
    "Bukit Merah": {"lat": 1.2819, "lon": 103.8239, "region": "Central"},
    "Bukit Panjang": {"lat": 1.3774, "lon": 103.7719, "region": "West"},
    "Bukit Timah": {"lat": 1.3294, "lon": 103.8021, "region": "Central"},
    "Central Water Catchment": {"lat": 1.3800, "lon": 103.8050, "region": "Central"},
    "Changi": {"lat": 1.3644, "lon": 103.9915, "region": "East"},
    "Choa Chu Kang": {"lat": 1.3840, "lon": 103.7470, "region": "West"},
    "Clementi": {"lat": 1.3162, "lon": 103.7649, "region": "West"},
    "City": {"lat": 1.2921, "lon": 103.8523, "region": "Central"},
    "Geylang": {"lat": 1.3201, "lon": 103.8918, "region": "East"},
    "Hougang": {"lat": 1.3612, "lon": 103.8863, "region": "North-East"},
    "Jalan Bahar": {"lat": 1.3473, "lon": 103.6920, "region": "West"},
    "Jurong East": {"lat": 1.3329, "lon": 103.7436, "region": "West"},
    "Jurong Island": {"lat": 1.2660, "lon": 103.6990, "region": "West"},
    "Jurong West": {"lat": 1.3404, "lon": 103.7090, "region": "West"},
    "Kallang": {"lat": 1.3117, "lon": 103.8666, "region": "Central"},
    "Lim Chu Kang": {"lat": 1.4304, "lon": 103.7175, "region": "North"},
    "Mandai": {"lat": 1.4040, "lon": 103.7890, "region": "North"},
    "Marine Parade": {"lat": 1.3020, "lon": 103.9070, "region": "East"},
    "Novena": {"lat": 1.3203, "lon": 103.8435, "region": "Central"},
    "Pasir Ris": {"lat": 1.3721, "lon": 103.9474, "region": "East"},
    "Paya Lebar": {"lat": 1.3582, "lon": 103.9142, "region": "East"},
    "Pioneer": {"lat": 1.3150, "lon": 103.6750, "region": "West"},
    "Pulau Tekong": {"lat": 1.4030, "lon": 104.0530, "region": "East"},
    "Pulau Ubin": {"lat": 1.4044, "lon": 103.9625, "region": "North-East"},
    "Punggol": {"lat": 1.4041, "lon": 103.9025, "region": "North-East"},
    "Queenstown": {"lat": 1.2942, "lon": 103.7861, "region": "Central"},
    "Seletar": {"lat": 1.4048, "lon": 103.8690, "region": "North"},
    "Sembawang": {"lat": 1.4491, "lon": 103.8185, "region": "North"},
    "Sengkang": {"lat": 1.3868, "lon": 103.8914, "region": "North-East"},
    "Sentosa": {"lat": 1.2494, "lon": 103.8303, "region": "South"},
    "Serangoon": {"lat": 1.3554, "lon": 103.8679, "region": "North-East"},
    "Southern Islands": {"lat": 1.2270, "lon": 103.8420, "region": "South"},
    "Sungei Kadut": {"lat": 1.4130, "lon": 103.7490, "region": "North"},
    "Tampines": {"lat": 1.3496, "lon": 103.9568, "region": "East"},
    "Tanglin": {"lat": 1.3077, "lon": 103.8130, "region": "Central"},
    "Tengah": {"lat": 1.3740, "lon": 103.7280, "region": "West"},
    "Toa Payoh": {"lat": 1.3343, "lon": 103.8563, "region": "Central"},
    "Tuas": {"lat": 1.2940, "lon": 103.6360, "region": "West"},
    "Western Islands": {"lat": 1.1930, "lon": 103.7360, "region": "West"},
    "Western Water Catchment": {"lat": 1.4050, "lon": 103.6860, "region": "West"},
    "Woodlands": {"lat": 1.4382, "lon": 103.7890, "region": "North"},
    "Yishun": {"lat": 1.4304, "lon": 103.8354, "region": "North"}
}

# Weather condition to icon/severity mapping
WEATHER_CONDITIONS = {
    "Cloudy": {"icon": "cloudy", "severity": "low", "traffic_impact": "none"},
    "Fair": {"icon": "sunny", "severity": "low", "traffic_impact": "none"},
    "Fair (Day)": {"icon": "sunny", "severity": "low", "traffic_impact": "none"},
    "Fair (Night)": {"icon": "clear-night", "severity": "low", "traffic_impact": "none"},
    "Fair & Warm": {"icon": "sunny", "severity": "low", "traffic_impact": "none"},
    "Hazy": {"icon": "haze", "severity": "medium", "traffic_impact": "moderate"},
    "Slightly Hazy": {"icon": "haze", "severity": "low", "traffic_impact": "low"},
    "Light Rain": {"icon": "light-rain", "severity": "low", "traffic_impact": "low"},
    "Light Showers": {"icon": "light-rain", "severity": "low", "traffic_impact": "low"},
    "Moderate Rain": {"icon": "rain", "severity": "medium", "traffic_impact": "moderate"},
    "Heavy Rain": {"icon": "heavy-rain", "severity": "high", "traffic_impact": "high"},
    "Passing Showers": {"icon": "rain", "severity": "medium", "traffic_impact": "moderate"},
    "Heavy Showers": {"icon": "heavy-rain", "severity": "high", "traffic_impact": "high"},
    "Thundery Showers": {"icon": "thunderstorm", "severity": "high", "traffic_impact": "high"},
    "Heavy Thundery Showers": {"icon": "thunderstorm", "severity": "very_high", "traffic_impact": "severe"},
    "Heavy Thundery Showers with Gusty Winds": {"icon": "thunderstorm", "severity": "very_high", "traffic_impact": "severe"},
    "Partly Cloudy": {"icon": "partly-cloudy", "severity": "low", "traffic_impact": "none"},
    "Partly Cloudy (Day)": {"icon": "partly-cloudy-day", "severity": "low", "traffic_impact": "none"},
    "Partly Cloudy (Night)": {"icon": "partly-cloudy-night", "severity": "low", "traffic_impact": "none"},
    "Showers": {"icon": "rain", "severity": "medium", "traffic_impact": "moderate"},
    "Windy": {"icon": "windy", "severity": "medium", "traffic_impact": "low"}
}


def fetch_api_data(url, params=None):
    """Fetch data from data.gov.sg API with error handling"""
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None


@weather_bp.route('/current', methods=['GET'])
def get_current_weather():
    """
    Get current 2-hour weather forecast for all areas
    Returns weather conditions with coordinates for map overlay
    """
    try:
        data = fetch_api_data(WEATHER_2H_FORECAST)

        if not data or 'items' not in data or not data['items']:
            return jsonify({
                'success': False,
                'error': 'No weather data available'
            }), 503

        item = data['items'][0]
        forecasts = item.get('forecasts', [])
        valid_period = item.get('valid_period', {})

        # Build response with coordinates
        weather_data = []
        for forecast in forecasts:
            area_name = forecast.get('area')
            condition = forecast.get('forecast', 'Unknown')

            area_info = SINGAPORE_AREAS.get(area_name, {})
            condition_info = WEATHER_CONDITIONS.get(condition, {
                "icon": "unknown",
                "severity": "unknown",
                "traffic_impact": "unknown"
            })

            weather_data.append({
                'area': area_name,
                'forecast': condition,
                'latitude': area_info.get('lat'),
                'longitude': area_info.get('lon'),
                'region': area_info.get('region', 'Unknown'),
                'icon': condition_info['icon'],
                'severity': condition_info['severity'],
                'traffic_impact': condition_info['traffic_impact']
            })

        return jsonify({
            'success': True,
            'data': {
                'forecasts': weather_data,
                'valid_period': {
                    'start': valid_period.get('start'),
                    'end': valid_period.get('end')
                },
                'update_timestamp': item.get('update_timestamp'),
                'timestamp': item.get('timestamp')
            }
        }), 200

    except Exception as e:
        print(f"Error getting current weather: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to fetch weather data: {str(e)}'
        }), 500


@weather_bp.route('/forecast/24h', methods=['GET'])
def get_24h_forecast():
    """Get 24-hour weather forecast"""
    try:
        data = fetch_api_data(WEATHER_24H_FORECAST)

        if not data or 'items' not in data or not data['items']:
            return jsonify({
                'success': False,
                'error': 'No forecast data available'
            }), 503

        item = data['items'][0]

        return jsonify({
            'success': True,
            'data': {
                'general': item.get('general', {}),
                'periods': item.get('periods', []),
                'update_timestamp': item.get('update_timestamp'),
                'timestamp': item.get('timestamp')
            }
        }), 200

    except Exception as e:
        print(f"Error getting 24h forecast: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to fetch forecast: {str(e)}'
        }), 500


@weather_bp.route('/forecast/4day', methods=['GET'])
def get_4day_forecast():
    """Get 4-day weather forecast"""
    try:
        data = fetch_api_data(WEATHER_4DAY_FORECAST)

        if not data or 'items' not in data or not data['items']:
            return jsonify({
                'success': False,
                'error': 'No forecast data available'
            }), 503

        item = data['items'][0]

        return jsonify({
            'success': True,
            'data': {
                'forecasts': item.get('forecasts', []),
                'update_timestamp': item.get('update_timestamp'),
                'timestamp': item.get('timestamp')
            }
        }), 200

    except Exception as e:
        print(f"Error getting 4-day forecast: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to fetch forecast: {str(e)}'
        }), 500


@weather_bp.route('/rainfall', methods=['GET'])
def get_rainfall():
    """
    Get real-time rainfall readings from weather stations
    Returns rainfall in mm for each station
    """
    try:
        data = fetch_api_data(RAINFALL_API)

        if not data or 'items' not in data or not data['items']:
            return jsonify({
                'success': False,
                'error': 'No rainfall data available'
            }), 503

        item = data['items'][0]
        readings = item.get('readings', [])
        stations = {s['id']: s for s in data.get('metadata', {}).get('stations', [])}

        rainfall_data = []
        for reading in readings:
            station_id = reading.get('station_id')
            station_info = stations.get(station_id, {})
            location = station_info.get('location', {})

            rainfall_data.append({
                'station_id': station_id,
                'station_name': station_info.get('name', 'Unknown'),
                'rainfall_mm': reading.get('value', 0),
                'latitude': location.get('latitude'),
                'longitude': location.get('longitude')
            })

        return jsonify({
            'success': True,
            'data': {
                'readings': rainfall_data,
                'timestamp': item.get('timestamp')
            }
        }), 200

    except Exception as e:
        print(f"Error getting rainfall: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to fetch rainfall data: {str(e)}'
        }), 500


@weather_bp.route('/temperature', methods=['GET'])
def get_temperature():
    """Get real-time air temperature readings"""
    try:
        data = fetch_api_data(AIR_TEMP_API)

        if not data or 'items' not in data or not data['items']:
            return jsonify({
                'success': False,
                'error': 'No temperature data available'
            }), 503

        item = data['items'][0]
        readings = item.get('readings', [])
        stations = {s['id']: s for s in data.get('metadata', {}).get('stations', [])}

        temp_data = []
        for reading in readings:
            station_id = reading.get('station_id')
            station_info = stations.get(station_id, {})
            location = station_info.get('location', {})

            temp_data.append({
                'station_id': station_id,
                'station_name': station_info.get('name', 'Unknown'),
                'temperature_c': reading.get('value'),
                'latitude': location.get('latitude'),
                'longitude': location.get('longitude')
            })

        return jsonify({
            'success': True,
            'data': {
                'readings': temp_data,
                'timestamp': item.get('timestamp')
            }
        }), 200

    except Exception as e:
        print(f"Error getting temperature: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to fetch temperature data: {str(e)}'
        }), 500


@weather_bp.route('/air-quality', methods=['GET'])
def get_air_quality():
    """Get PSI and PM2.5 readings for air quality overlay"""
    try:
        # Fetch both PSI and PM2.5 data
        psi_data = fetch_api_data(PSI_API)
        pm25_data = fetch_api_data(PM25_API)

        result = {
            'psi': None,
            'pm25': None,
            'timestamp': datetime.utcnow().isoformat()
        }

        if psi_data and 'items' in psi_data and psi_data['items']:
            item = psi_data['items'][0]
            readings = item.get('readings', {})
            result['psi'] = {
                'readings': readings,
                'timestamp': item.get('timestamp')
            }

        if pm25_data and 'items' in pm25_data and pm25_data['items']:
            item = pm25_data['items'][0]
            readings = item.get('readings', {})
            result['pm25'] = {
                'readings': readings,
                'timestamp': item.get('timestamp')
            }

        return jsonify({
            'success': True,
            'data': result
        }), 200

    except Exception as e:
        print(f"Error getting air quality: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to fetch air quality data: {str(e)}'
        }), 500


@weather_bp.route('/combined', methods=['GET'])
def get_combined_weather():
    """
    Get combined weather data for comprehensive overlay
    Includes: forecasts, rainfall, temperature, air quality
    """
    try:
        region = request.args.get('region', 'All')

        # Fetch all data in parallel would be better, but sequential for simplicity
        forecast_data = fetch_api_data(WEATHER_2H_FORECAST)
        rainfall_data = fetch_api_data(RAINFALL_API)
        temp_data = fetch_api_data(AIR_TEMP_API)

        result = {
            'forecasts': [],
            'rainfall': [],
            'temperature': [],
            'timestamp': datetime.utcnow().isoformat()
        }

        # Process forecasts
        if forecast_data and 'items' in forecast_data and forecast_data['items']:
            item = forecast_data['items'][0]
            for forecast in item.get('forecasts', []):
                area_name = forecast.get('area')
                area_info = SINGAPORE_AREAS.get(area_name, {})

                # Filter by region if specified
                if region != 'All' and area_info.get('region') != region:
                    continue

                condition = forecast.get('forecast', 'Unknown')
                condition_info = WEATHER_CONDITIONS.get(condition, {
                    "icon": "unknown",
                    "severity": "unknown",
                    "traffic_impact": "unknown"
                })

                result['forecasts'].append({
                    'area': area_name,
                    'forecast': condition,
                    'latitude': area_info.get('lat'),
                    'longitude': area_info.get('lon'),
                    'region': area_info.get('region', 'Unknown'),
                    'icon': condition_info['icon'],
                    'severity': condition_info['severity'],
                    'traffic_impact': condition_info['traffic_impact']
                })

        # Process rainfall
        if rainfall_data and 'items' in rainfall_data and rainfall_data['items']:
            item = rainfall_data['items'][0]
            stations = {s['id']: s for s in rainfall_data.get('metadata', {}).get('stations', [])}

            for reading in item.get('readings', []):
                station_id = reading.get('station_id')
                station_info = stations.get(station_id, {})
                location = station_info.get('location', {})

                result['rainfall'].append({
                    'station_id': station_id,
                    'station_name': station_info.get('name', 'Unknown'),
                    'rainfall_mm': reading.get('value', 0),
                    'latitude': location.get('latitude'),
                    'longitude': location.get('longitude')
                })

        # Process temperature
        if temp_data and 'items' in temp_data and temp_data['items']:
            item = temp_data['items'][0]
            stations = {s['id']: s for s in temp_data.get('metadata', {}).get('stations', [])}

            for reading in item.get('readings', []):
                station_id = reading.get('station_id')
                station_info = stations.get(station_id, {})
                location = station_info.get('location', {})

                result['temperature'].append({
                    'station_id': station_id,
                    'station_name': station_info.get('name', 'Unknown'),
                    'temperature_c': reading.get('value'),
                    'latitude': location.get('latitude'),
                    'longitude': location.get('longitude')
                })

        return jsonify({
            'success': True,
            'data': result
        }), 200

    except Exception as e:
        print(f"Error getting combined weather: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to fetch combined weather data: {str(e)}'
        }), 500


@weather_bp.route('/areas', methods=['GET'])
def get_weather_areas():
    """Get list of all weather monitoring areas with coordinates"""
    try:
        areas = []
        for name, info in SINGAPORE_AREAS.items():
            areas.append({
                'name': name,
                'latitude': info['lat'],
                'longitude': info['lon'],
                'region': info['region']
            })

        return jsonify({
            'success': True,
            'data': {
                'areas': areas,
                'total': len(areas)
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
