"""
Public Transport API routes - integrates with LTA DataMall for MRT/Bus data.
Provides real-time bus arrivals, MRT status, and transport overlay data.
"""

from flask import Blueprint, request, jsonify
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

transport_bp = Blueprint('transport', __name__)

# LTA DataMall API configuration
LTA_API_KEY = os.getenv('LTA_API_KEY')
LTA_BASE_URL = "http://datamall2.mytransport.sg/ltaodataservice"

# API endpoints
BUS_ARRIVALS_URL = f"{LTA_BASE_URL}/BusArrivalv2"
BUS_STOPS_URL = f"{LTA_BASE_URL}/BusStops"
BUS_ROUTES_URL = f"{LTA_BASE_URL}/BusRoutes"
BUS_SERVICES_URL = f"{LTA_BASE_URL}/BusServices"
TRAIN_SERVICE_ALERTS_URL = f"{LTA_BASE_URL}/TrainServiceAlerts"
TAXI_AVAILABILITY_URL = f"{LTA_BASE_URL}/Taxi-Availability"

# MRT Station data (key stations with coordinates)
MRT_STATIONS = {
    # North-South Line (NS)
    "NS1": {"name": "Jurong East", "lat": 1.3329, "lon": 103.7422, "line": "NS"},
    "NS2": {"name": "Bukit Batok", "lat": 1.3492, "lon": 103.7495, "line": "NS"},
    "NS3": {"name": "Bukit Gombak", "lat": 1.3587, "lon": 103.7519, "line": "NS"},
    "NS4": {"name": "Choa Chu Kang", "lat": 1.3853, "lon": 103.7444, "line": "NS"},
    "NS5": {"name": "Yew Tee", "lat": 1.3973, "lon": 103.7475, "line": "NS"},
    "NS7": {"name": "Kranji", "lat": 1.4251, "lon": 103.7620, "line": "NS"},
    "NS8": {"name": "Marsiling", "lat": 1.4329, "lon": 103.7742, "line": "NS"},
    "NS9": {"name": "Woodlands", "lat": 1.4370, "lon": 103.7863, "line": "NS"},
    "NS10": {"name": "Admiralty", "lat": 1.4406, "lon": 103.8009, "line": "NS"},
    "NS11": {"name": "Sembawang", "lat": 1.4491, "lon": 103.8200, "line": "NS"},
    "NS12": {"name": "Canberra", "lat": 1.4431, "lon": 103.8296, "line": "NS"},
    "NS13": {"name": "Yishun", "lat": 1.4295, "lon": 103.8350, "line": "NS"},
    "NS14": {"name": "Khatib", "lat": 1.4172, "lon": 103.8329, "line": "NS"},
    "NS15": {"name": "Yio Chu Kang", "lat": 1.3817, "lon": 103.8449, "line": "NS"},
    "NS16": {"name": "Ang Mo Kio", "lat": 1.3699, "lon": 103.8497, "line": "NS"},
    "NS17": {"name": "Bishan", "lat": 1.3511, "lon": 103.8491, "line": "NS"},
    "NS18": {"name": "Braddell", "lat": 1.3405, "lon": 103.8467, "line": "NS"},
    "NS19": {"name": "Toa Payoh", "lat": 1.3327, "lon": 103.8473, "line": "NS"},
    "NS20": {"name": "Novena", "lat": 1.3203, "lon": 103.8435, "line": "NS"},
    "NS21": {"name": "Newton", "lat": 1.3127, "lon": 103.8380, "line": "NS"},
    "NS22": {"name": "Orchard", "lat": 1.3044, "lon": 103.8319, "line": "NS"},
    "NS23": {"name": "Somerset", "lat": 1.3007, "lon": 103.8388, "line": "NS"},
    "NS24": {"name": "Dhoby Ghaut", "lat": 1.2993, "lon": 103.8455, "line": "NS"},
    "NS25": {"name": "City Hall", "lat": 1.2931, "lon": 103.8519, "line": "NS"},
    "NS26": {"name": "Raffles Place", "lat": 1.2837, "lon": 103.8515, "line": "NS"},
    "NS27": {"name": "Marina Bay", "lat": 1.2765, "lon": 103.8545, "line": "NS"},
    "NS28": {"name": "Marina South Pier", "lat": 1.2715, "lon": 103.8632, "line": "NS"},

    # East-West Line (EW)
    "EW1": {"name": "Pasir Ris", "lat": 1.3730, "lon": 103.9494, "line": "EW"},
    "EW2": {"name": "Tampines", "lat": 1.3548, "lon": 103.9454, "line": "EW"},
    "EW3": {"name": "Simei", "lat": 1.3432, "lon": 103.9534, "line": "EW"},
    "EW4": {"name": "Tanah Merah", "lat": 1.3272, "lon": 103.9463, "line": "EW"},
    "EW5": {"name": "Bedok", "lat": 1.3242, "lon": 103.9300, "line": "EW"},
    "EW6": {"name": "Kembangan", "lat": 1.3209, "lon": 103.9129, "line": "EW"},
    "EW7": {"name": "Eunos", "lat": 1.3197, "lon": 103.9030, "line": "EW"},
    "EW8": {"name": "Paya Lebar", "lat": 1.3176, "lon": 103.8926, "line": "EW"},
    "EW9": {"name": "Aljunied", "lat": 1.3165, "lon": 103.8829, "line": "EW"},
    "EW10": {"name": "Kallang", "lat": 1.3114, "lon": 103.8714, "line": "EW"},
    "EW11": {"name": "Lavender", "lat": 1.3073, "lon": 103.8630, "line": "EW"},
    "EW12": {"name": "Bugis", "lat": 1.3006, "lon": 103.8559, "line": "EW"},
    "EW13": {"name": "City Hall", "lat": 1.2931, "lon": 103.8519, "line": "EW"},
    "EW14": {"name": "Raffles Place", "lat": 1.2837, "lon": 103.8515, "line": "EW"},
    "EW15": {"name": "Tanjong Pagar", "lat": 1.2764, "lon": 103.8466, "line": "EW"},
    "EW16": {"name": "Outram Park", "lat": 1.2802, "lon": 103.8396, "line": "EW"},
    "EW17": {"name": "Tiong Bahru", "lat": 1.2862, "lon": 103.8270, "line": "EW"},
    "EW18": {"name": "Redhill", "lat": 1.2896, "lon": 103.8168, "line": "EW"},
    "EW19": {"name": "Queenstown", "lat": 1.2945, "lon": 103.8060, "line": "EW"},
    "EW20": {"name": "Commonwealth", "lat": 1.3024, "lon": 103.7983, "line": "EW"},
    "EW21": {"name": "Buona Vista", "lat": 1.3074, "lon": 103.7902, "line": "EW"},
    "EW22": {"name": "Dover", "lat": 1.3115, "lon": 103.7785, "line": "EW"},
    "EW23": {"name": "Clementi", "lat": 1.3151, "lon": 103.7652, "line": "EW"},
    "EW24": {"name": "Jurong East", "lat": 1.3329, "lon": 103.7422, "line": "EW"},
    "EW25": {"name": "Chinese Garden", "lat": 1.3425, "lon": 103.7326, "line": "EW"},
    "EW26": {"name": "Lakeside", "lat": 1.3441, "lon": 103.7209, "line": "EW"},
    "EW27": {"name": "Boon Lay", "lat": 1.3386, "lon": 103.7055, "line": "EW"},
    "EW28": {"name": "Pioneer", "lat": 1.3376, "lon": 103.6972, "line": "EW"},
    "EW29": {"name": "Joo Koon", "lat": 1.3279, "lon": 103.6787, "line": "EW"},
    "EW30": {"name": "Gul Circle", "lat": 1.3194, "lon": 103.6605, "line": "EW"},
    "EW31": {"name": "Tuas Crescent", "lat": 1.3210, "lon": 103.6491, "line": "EW"},
    "EW32": {"name": "Tuas West Road", "lat": 1.3299, "lon": 103.6397, "line": "EW"},
    "EW33": {"name": "Tuas Link", "lat": 1.3405, "lon": 103.6368, "line": "EW"},

    # North-East Line (NE)
    "NE1": {"name": "HarbourFront", "lat": 1.2653, "lon": 103.8210, "line": "NE"},
    "NE3": {"name": "Outram Park", "lat": 1.2802, "lon": 103.8396, "line": "NE"},
    "NE4": {"name": "Chinatown", "lat": 1.2849, "lon": 103.8443, "line": "NE"},
    "NE5": {"name": "Clarke Quay", "lat": 1.2886, "lon": 103.8465, "line": "NE"},
    "NE6": {"name": "Dhoby Ghaut", "lat": 1.2993, "lon": 103.8455, "line": "NE"},
    "NE7": {"name": "Little India", "lat": 1.3066, "lon": 103.8494, "line": "NE"},
    "NE8": {"name": "Farrer Park", "lat": 1.3124, "lon": 103.8541, "line": "NE"},
    "NE9": {"name": "Boon Keng", "lat": 1.3195, "lon": 103.8618, "line": "NE"},
    "NE10": {"name": "Potong Pasir", "lat": 1.3314, "lon": 103.8688, "line": "NE"},
    "NE11": {"name": "Woodleigh", "lat": 1.3392, "lon": 103.8707, "line": "NE"},
    "NE12": {"name": "Serangoon", "lat": 1.3498, "lon": 103.8735, "line": "NE"},
    "NE13": {"name": "Kovan", "lat": 1.3601, "lon": 103.8851, "line": "NE"},
    "NE14": {"name": "Hougang", "lat": 1.3715, "lon": 103.8923, "line": "NE"},
    "NE15": {"name": "Buangkok", "lat": 1.3831, "lon": 103.8929, "line": "NE"},
    "NE16": {"name": "Sengkang", "lat": 1.3917, "lon": 103.8953, "line": "NE"},
    "NE17": {"name": "Punggol", "lat": 1.4052, "lon": 103.9024, "line": "NE"},

    # Circle Line (CC)
    "CC1": {"name": "Dhoby Ghaut", "lat": 1.2993, "lon": 103.8455, "line": "CC"},
    "CC2": {"name": "Bras Basah", "lat": 1.2968, "lon": 103.8506, "line": "CC"},
    "CC3": {"name": "Esplanade", "lat": 1.2936, "lon": 103.8553, "line": "CC"},
    "CC4": {"name": "Promenade", "lat": 1.2933, "lon": 103.8610, "line": "CC"},
    "CC5": {"name": "Nicoll Highway", "lat": 1.2997, "lon": 103.8636, "line": "CC"},
    "CC6": {"name": "Stadium", "lat": 1.3028, "lon": 103.8753, "line": "CC"},
    "CC7": {"name": "Mountbatten", "lat": 1.3064, "lon": 103.8823, "line": "CC"},
    "CC8": {"name": "Dakota", "lat": 1.3083, "lon": 103.8886, "line": "CC"},
    "CC9": {"name": "Paya Lebar", "lat": 1.3176, "lon": 103.8926, "line": "CC"},
    "CC10": {"name": "MacPherson", "lat": 1.3265, "lon": 103.8900, "line": "CC"},
    "CC11": {"name": "Tai Seng", "lat": 1.3360, "lon": 103.8880, "line": "CC"},
    "CC12": {"name": "Bartley", "lat": 1.3428, "lon": 103.8796, "line": "CC"},
    "CC13": {"name": "Serangoon", "lat": 1.3498, "lon": 103.8735, "line": "CC"},
    "CC14": {"name": "Lorong Chuan", "lat": 1.3516, "lon": 103.8643, "line": "CC"},
    "CC15": {"name": "Bishan", "lat": 1.3511, "lon": 103.8491, "line": "CC"},
    "CC16": {"name": "Marymount", "lat": 1.3493, "lon": 103.8390, "line": "CC"},
    "CC17": {"name": "Caldecott", "lat": 1.3374, "lon": 103.8396, "line": "CC"},
    "CC19": {"name": "Botanic Gardens", "lat": 1.3223, "lon": 103.8153, "line": "CC"},
    "CC20": {"name": "Farrer Road", "lat": 1.3172, "lon": 103.8073, "line": "CC"},
    "CC21": {"name": "Holland Village", "lat": 1.3116, "lon": 103.7961, "line": "CC"},
    "CC22": {"name": "Buona Vista", "lat": 1.3074, "lon": 103.7902, "line": "CC"},
    "CC23": {"name": "one-north", "lat": 1.2994, "lon": 103.7874, "line": "CC"},
    "CC24": {"name": "Kent Ridge", "lat": 1.2936, "lon": 103.7844, "line": "CC"},
    "CC25": {"name": "Haw Par Villa", "lat": 1.2824, "lon": 103.7818, "line": "CC"},
    "CC26": {"name": "Pasir Panjang", "lat": 1.2760, "lon": 103.7915, "line": "CC"},
    "CC27": {"name": "Labrador Park", "lat": 1.2720, "lon": 103.8027, "line": "CC"},
    "CC28": {"name": "Telok Blangah", "lat": 1.2707, "lon": 103.8098, "line": "CC"},
    "CC29": {"name": "HarbourFront", "lat": 1.2653, "lon": 103.8210, "line": "CC"},

    # Downtown Line (DT)
    "DT1": {"name": "Bukit Panjang", "lat": 1.3784, "lon": 103.7628, "line": "DT"},
    "DT2": {"name": "Cashew", "lat": 1.3690, "lon": 103.7647, "line": "DT"},
    "DT3": {"name": "Hillview", "lat": 1.3626, "lon": 103.7673, "line": "DT"},
    "DT5": {"name": "Beauty World", "lat": 1.3408, "lon": 103.7759, "line": "DT"},
    "DT6": {"name": "King Albert Park", "lat": 1.3355, "lon": 103.7830, "line": "DT"},
    "DT7": {"name": "Sixth Avenue", "lat": 1.3307, "lon": 103.7969, "line": "DT"},
    "DT8": {"name": "Tan Kah Kee", "lat": 1.3260, "lon": 103.8074, "line": "DT"},
    "DT9": {"name": "Botanic Gardens", "lat": 1.3223, "lon": 103.8153, "line": "DT"},
    "DT10": {"name": "Stevens", "lat": 1.3199, "lon": 103.8260, "line": "DT"},
    "DT11": {"name": "Newton", "lat": 1.3127, "lon": 103.8380, "line": "DT"},
    "DT12": {"name": "Little India", "lat": 1.3066, "lon": 103.8494, "line": "DT"},
    "DT13": {"name": "Rochor", "lat": 1.3035, "lon": 103.8525, "line": "DT"},
    "DT14": {"name": "Bugis", "lat": 1.3006, "lon": 103.8559, "line": "DT"},
    "DT15": {"name": "Promenade", "lat": 1.2933, "lon": 103.8610, "line": "DT"},
    "DT16": {"name": "Bayfront", "lat": 1.2815, "lon": 103.8594, "line": "DT"},
    "DT17": {"name": "Downtown", "lat": 1.2795, "lon": 103.8528, "line": "DT"},
    "DT18": {"name": "Telok Ayer", "lat": 1.2822, "lon": 103.8485, "line": "DT"},
    "DT19": {"name": "Chinatown", "lat": 1.2849, "lon": 103.8443, "line": "DT"},
    "DT20": {"name": "Fort Canning", "lat": 1.2923, "lon": 103.8444, "line": "DT"},
    "DT21": {"name": "Bencoolen", "lat": 1.2985, "lon": 103.8499, "line": "DT"},
    "DT22": {"name": "Jalan Besar", "lat": 1.3054, "lon": 103.8555, "line": "DT"},
    "DT23": {"name": "Bendemeer", "lat": 1.3136, "lon": 103.8631, "line": "DT"},
    "DT24": {"name": "Geylang Bahru", "lat": 1.3214, "lon": 103.8713, "line": "DT"},
    "DT25": {"name": "Mattar", "lat": 1.3267, "lon": 103.8830, "line": "DT"},
    "DT26": {"name": "MacPherson", "lat": 1.3265, "lon": 103.8900, "line": "DT"},
    "DT27": {"name": "Ubi", "lat": 1.3299, "lon": 103.8991, "line": "DT"},
    "DT28": {"name": "Kaki Bukit", "lat": 1.3350, "lon": 103.9080, "line": "DT"},
    "DT29": {"name": "Bedok North", "lat": 1.3346, "lon": 103.9181, "line": "DT"},
    "DT30": {"name": "Bedok Reservoir", "lat": 1.3365, "lon": 103.9322, "line": "DT"},
    "DT31": {"name": "Tampines West", "lat": 1.3463, "lon": 103.9384, "line": "DT"},
    "DT32": {"name": "Tampines", "lat": 1.3548, "lon": 103.9454, "line": "DT"},
    "DT33": {"name": "Tampines East", "lat": 1.3564, "lon": 103.9545, "line": "DT"},
    "DT34": {"name": "Upper Changi", "lat": 1.3413, "lon": 103.9613, "line": "DT"},
    "DT35": {"name": "Expo", "lat": 1.3351, "lon": 103.9617, "line": "DT"},

    # Thomson-East Coast Line (TE)
    "TE1": {"name": "Woodlands North", "lat": 1.4487, "lon": 103.7856, "line": "TE"},
    "TE2": {"name": "Woodlands", "lat": 1.4370, "lon": 103.7863, "line": "TE"},
    "TE3": {"name": "Woodlands South", "lat": 1.4271, "lon": 103.7929, "line": "TE"},
    "TE4": {"name": "Springleaf", "lat": 1.3978, "lon": 103.8188, "line": "TE"},
    "TE5": {"name": "Lentor", "lat": 1.3848, "lon": 103.8362, "line": "TE"},
    "TE6": {"name": "Mayflower", "lat": 1.3715, "lon": 103.8378, "line": "TE"},
    "TE7": {"name": "Bright Hill", "lat": 1.3635, "lon": 103.8335, "line": "TE"},
    "TE8": {"name": "Upper Thomson", "lat": 1.3538, "lon": 103.8326, "line": "TE"},
    "TE9": {"name": "Caldecott", "lat": 1.3374, "lon": 103.8396, "line": "TE"},
    "TE11": {"name": "Stevens", "lat": 1.3199, "lon": 103.8260, "line": "TE"},
    "TE12": {"name": "Napier", "lat": 1.3067, "lon": 103.8177, "line": "TE"},
    "TE13": {"name": "Orchard Boulevard", "lat": 1.3020, "lon": 103.8265, "line": "TE"},
    "TE14": {"name": "Orchard", "lat": 1.3044, "lon": 103.8319, "line": "TE"},
    "TE15": {"name": "Great World", "lat": 1.2934, "lon": 103.8316, "line": "TE"},
    "TE16": {"name": "Havelock", "lat": 1.2879, "lon": 103.8317, "line": "TE"},
    "TE17": {"name": "Outram Park", "lat": 1.2802, "lon": 103.8396, "line": "TE"},
    "TE18": {"name": "Maxwell", "lat": 1.2796, "lon": 103.8451, "line": "TE"},
    "TE19": {"name": "Shenton Way", "lat": 1.2764, "lon": 103.8476, "line": "TE"},
    "TE20": {"name": "Marina Bay", "lat": 1.2765, "lon": 103.8545, "line": "TE"},
    "TE22": {"name": "Gardens by the Bay", "lat": 1.2795, "lon": 103.8689, "line": "TE"}
}

# MRT Line colors
MRT_LINE_COLORS = {
    "NS": "#D42E12",  # Red
    "EW": "#009645",  # Green
    "NE": "#9900AA",  # Purple
    "CC": "#FA9E0D",  # Orange
    "DT": "#005EC4",  # Blue
    "TE": "#9D5B25",  # Brown
    "BP": "#748477",  # Gray (Bukit Panjang LRT)
    "SK": "#748477",  # Gray (Sengkang LRT)
    "PG": "#748477"   # Gray (Punggol LRT)
}


def get_lta_headers():
    """Get headers for LTA API requests"""
    return {
        'AccountKey': LTA_API_KEY,
        'accept': 'application/json'
    }


def fetch_lta_data(url, params=None):
    """Fetch data from LTA DataMall API"""
    if not LTA_API_KEY:
        return None

    try:
        response = requests.get(url, headers=get_lta_headers(), params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"LTA API request failed: {e}")
        return None


@transport_bp.route('/mrt/stations', methods=['GET'])
def get_mrt_stations():
    """
    Get all MRT stations with coordinates for map overlay
    """
    try:
        line = request.args.get('line', 'All')

        stations = []
        for code, info in MRT_STATIONS.items():
            if line != 'All' and info['line'] != line:
                continue

            stations.append({
                'code': code,
                'name': info['name'],
                'latitude': info['lat'],
                'longitude': info['lon'],
                'line': info['line'],
                'color': MRT_LINE_COLORS.get(info['line'], '#000000')
            })

        return jsonify({
            'success': True,
            'data': {
                'stations': stations,
                'total': len(stations),
                'lines': list(MRT_LINE_COLORS.keys())
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@transport_bp.route('/mrt/alerts', methods=['GET'])
def get_train_alerts():
    """
    Get train service alerts from LTA
    Returns disruptions and delays on MRT/LRT lines
    """
    try:
        data = fetch_lta_data(TRAIN_SERVICE_ALERTS_URL)

        if not data:
            return jsonify({
                'success': True,
                'data': {
                    'status': 'normal',
                    'message': 'All train services operating normally',
                    'alerts': [],
                    'timestamp': datetime.utcnow().isoformat()
                }
            }), 200

        alerts = data.get('value', {}).get('Message', [])

        processed_alerts = []
        for alert in alerts:
            processed_alerts.append({
                'content': alert.get('Content', ''),
                'created_at': alert.get('CreatedDate', ''),
                'status': alert.get('Status', 1)  # 1 = normal, 2 = disrupted
            })

        status = 'normal'
        if any(a.get('status') == 2 for a in processed_alerts):
            status = 'disrupted'

        return jsonify({
            'success': True,
            'data': {
                'status': status,
                'alerts': processed_alerts,
                'affected_segments': data.get('value', {}).get('AffectedSegments', []),
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 200

    except Exception as e:
        print(f"Error getting train alerts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@transport_bp.route('/bus/stops', methods=['GET'])
def get_bus_stops():
    """
    Get bus stops with coordinates
    Supports pagination via skip parameter
    """
    try:
        skip = int(request.args.get('skip', 0))
        lat_min = request.args.get('lat_min', type=float)
        lat_max = request.args.get('lat_max', type=float)
        lon_min = request.args.get('lon_min', type=float)
        lon_max = request.args.get('lon_max', type=float)

        all_stops = []

        # LTA API returns max 500 records at a time
        # Fetch multiple pages if needed
        while True:
            data = fetch_lta_data(BUS_STOPS_URL, {'$skip': skip})

            if not data or 'value' not in data:
                break

            stops = data.get('value', [])
            if not stops:
                break

            for stop in stops:
                lat = stop.get('Latitude')
                lon = stop.get('Longitude')

                # Filter by bounds if specified
                if lat_min and lat_max and lon_min and lon_max:
                    if not (lat_min <= lat <= lat_max and lon_min <= lon <= lon_max):
                        continue

                all_stops.append({
                    'bus_stop_code': stop.get('BusStopCode'),
                    'road_name': stop.get('RoadName'),
                    'description': stop.get('Description'),
                    'latitude': lat,
                    'longitude': lon
                })

            skip += 500

            # Limit total fetches to prevent timeout
            if skip >= 5000:
                break

        return jsonify({
            'success': True,
            'data': {
                'stops': all_stops,
                'total': len(all_stops)
            }
        }), 200

    except Exception as e:
        print(f"Error getting bus stops: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@transport_bp.route('/bus/arrival', methods=['GET'])
def get_bus_arrival():
    """
    Get real-time bus arrival information for a specific bus stop
    """
    try:
        bus_stop_code = request.args.get('bus_stop_code')

        if not bus_stop_code:
            return jsonify({
                'success': False,
                'error': 'bus_stop_code parameter is required'
            }), 400

        data = fetch_lta_data(BUS_ARRIVALS_URL, {'BusStopCode': bus_stop_code})

        if not data:
            return jsonify({
                'success': False,
                'error': 'Unable to fetch bus arrival data'
            }), 503

        services = []
        for service in data.get('Services', []):
            next_bus = service.get('NextBus', {})
            next_bus2 = service.get('NextBus2', {})
            next_bus3 = service.get('NextBus3', {})

            services.append({
                'service_no': service.get('ServiceNo'),
                'operator': service.get('Operator'),
                'next_bus': {
                    'estimated_arrival': next_bus.get('EstimatedArrival'),
                    'load': next_bus.get('Load'),  # SEA, SDA, LSD
                    'feature': next_bus.get('Feature'),  # WAB (wheelchair)
                    'type': next_bus.get('Type')  # SD, DD, BD
                },
                'next_bus_2': {
                    'estimated_arrival': next_bus2.get('EstimatedArrival'),
                    'load': next_bus2.get('Load'),
                    'feature': next_bus2.get('Feature'),
                    'type': next_bus2.get('Type')
                },
                'next_bus_3': {
                    'estimated_arrival': next_bus3.get('EstimatedArrival'),
                    'load': next_bus3.get('Load'),
                    'feature': next_bus3.get('Feature'),
                    'type': next_bus3.get('Type')
                }
            })

        return jsonify({
            'success': True,
            'data': {
                'bus_stop_code': bus_stop_code,
                'services': services,
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 200

    except Exception as e:
        print(f"Error getting bus arrival: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@transport_bp.route('/taxi/availability', methods=['GET'])
def get_taxi_availability():
    """
    Get real-time taxi availability locations
    """
    try:
        data = fetch_lta_data(TAXI_AVAILABILITY_URL)

        if not data:
            return jsonify({
                'success': False,
                'error': 'Unable to fetch taxi availability data'
            }), 503

        taxis = []
        for taxi in data.get('value', []):
            coords = taxi.get('Coordinates', '').split(',')
            if len(coords) == 2:
                taxis.append({
                    'longitude': float(coords[0]),
                    'latitude': float(coords[1])
                })

        return jsonify({
            'success': True,
            'data': {
                'taxis': taxis,
                'total': len(taxis),
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 200

    except Exception as e:
        print(f"Error getting taxi availability: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@transport_bp.route('/combined', methods=['GET'])
def get_combined_transport():
    """
    Get combined transport data for overlay
    Includes: MRT stations, train alerts, bus stops (limited area)
    """
    try:
        lat = request.args.get('lat', 1.3521, type=float)
        lon = request.args.get('lon', 103.8198, type=float)
        radius_km = request.args.get('radius', 2, type=float)

        # Convert radius to lat/lon bounds (approximate)
        lat_delta = radius_km / 111  # 1 degree lat ≈ 111 km
        lon_delta = radius_km / (111 * 0.85)  # Adjust for Singapore's latitude

        lat_min = lat - lat_delta
        lat_max = lat + lat_delta
        lon_min = lon - lon_delta
        lon_max = lon + lon_delta

        result = {
            'mrt_stations': [],
            'train_alerts': [],
            'bus_stops': [],
            'timestamp': datetime.utcnow().isoformat()
        }

        # Get nearby MRT stations
        for code, info in MRT_STATIONS.items():
            if lat_min <= info['lat'] <= lat_max and lon_min <= info['lon'] <= lon_max:
                result['mrt_stations'].append({
                    'code': code,
                    'name': info['name'],
                    'latitude': info['lat'],
                    'longitude': info['lon'],
                    'line': info['line'],
                    'color': MRT_LINE_COLORS.get(info['line'], '#000000')
                })

        # Get train alerts
        alerts_data = fetch_lta_data(TRAIN_SERVICE_ALERTS_URL)
        if alerts_data:
            alerts = alerts_data.get('value', {}).get('Message', [])
            for alert in alerts:
                result['train_alerts'].append({
                    'content': alert.get('Content', ''),
                    'created_at': alert.get('CreatedDate', ''),
                    'status': alert.get('Status', 1)
                })

        # Get nearby bus stops (limited to one page for performance)
        bus_data = fetch_lta_data(BUS_STOPS_URL)
        if bus_data:
            for stop in bus_data.get('value', []):
                stop_lat = stop.get('Latitude')
                stop_lon = stop.get('Longitude')

                if lat_min <= stop_lat <= lat_max and lon_min <= stop_lon <= lon_max:
                    result['bus_stops'].append({
                        'bus_stop_code': stop.get('BusStopCode'),
                        'road_name': stop.get('RoadName'),
                        'description': stop.get('Description'),
                        'latitude': stop_lat,
                        'longitude': stop_lon
                    })

        return jsonify({
            'success': True,
            'data': result
        }), 200

    except Exception as e:
        print(f"Error getting combined transport: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@transport_bp.route('/lines', methods=['GET'])
def get_mrt_lines():
    """Get MRT line information"""
    lines = []
    for code, color in MRT_LINE_COLORS.items():
        line_names = {
            "NS": "North-South Line",
            "EW": "East-West Line",
            "NE": "North-East Line",
            "CC": "Circle Line",
            "DT": "Downtown Line",
            "TE": "Thomson-East Coast Line",
            "BP": "Bukit Panjang LRT",
            "SK": "Sengkang LRT",
            "PG": "Punggol LRT"
        }

        station_count = sum(1 for s in MRT_STATIONS.values() if s['line'] == code)

        lines.append({
            'code': code,
            'name': line_names.get(code, code),
            'color': color,
            'station_count': station_count
        })

    return jsonify({
        'success': True,
        'data': {
            'lines': lines,
            'total_stations': len(MRT_STATIONS)
        }
    }), 200
