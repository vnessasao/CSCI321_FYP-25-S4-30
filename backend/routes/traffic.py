"""
Traffic congestion API routes using LTA Data Mall API
Provides real-time traffic speed data and congestion analysis
"""

from flask import Blueprint, jsonify, request
import requests
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create blueprint for LTA traffic routes
lta_bp = Blueprint('lta_traffic', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Singapore region boundaries (lat/lon) - Subdividing the route-dense area
SINGAPORE_REGIONS = {
    'North': {'lat_min': 1.32, 'lat_max': 1.36, 'lon_min': 103.82, 'lon_max': 103.88},
    'Central': {'lat_min': 1.29, 'lat_max': 1.32, 'lon_min': 103.84, 'lon_max': 103.88},
    'South': {'lat_min': 1.27, 'lat_max': 1.29, 'lon_min': 103.83, 'lon_max': 103.87},
    'East': {'lat_min': 1.29, 'lat_max': 1.34, 'lon_min': 103.88, 'lon_max': 103.90},
    'West': {'lat_min': 1.30, 'lat_max': 1.33, 'lon_min': 103.82, 'lon_max': 103.84}
}


def is_in_region(lat, lon, region):
    """Check if coordinates are within a specific Singapore region."""
    if region == 'All' or region not in SINGAPORE_REGIONS:
        return True
    bounds = SINGAPORE_REGIONS[region]
    return (bounds['lat_min'] <= lat <= bounds['lat_max'] and
            bounds['lon_min'] <= lon <= bounds['lon_max'])


def classify_congestion(speed):
    """
    Classify congestion level based on speed
    Args:
        speed (float): Speed in km/h
    Returns:
        str: Congestion level ('normal', 'moderate', 'heavy')
    """
    if speed < 20:
        return 'heavy'
    elif speed < 40:
        return 'moderate'
    else:
        return 'normal'

def transform_to_geojson(lta_data):
    """
    Transform LTA API response to GeoJSON format using OSM road geometries
    Args:
        lta_data (dict): Raw response from LTA API
    Returns:
        dict: GeoJSON FeatureCollection
    """
    try:
        features = []
        
        # Process LTA data directly using their coordinates
        
        # Handle different LTA API response formats
        lta_features = []
        
        if isinstance(lta_data, dict):
            if 'value' in lta_data and isinstance(lta_data['value'], list):
                # LTA DataMall v2 format: {"value": [...]}
                lta_features = lta_data['value']
            elif 'features' in lta_data and isinstance(lta_data['features'], list):
                # GeoJSON format: {"features": [...]}
                lta_features = lta_data['features']
            elif isinstance(lta_data.get('data'), list):
                # Alternative format: {"data": [...]}
                lta_features = lta_data['data']
        
        logger.info(f"📊 Processing {len(lta_features)} traffic records from LTA")
        
        # Debug: Log the first few LTA records to understand the format
        if lta_features and len(lta_features) > 0:
            logger.info(f"🔍 First LTA record keys: {list(lta_features[0].keys())}")
            logger.info(f"🔍 First LTA record sample: {str(lta_features[0])[:200]}...")
        
        matched_roads = 0
        for item in lta_features:
            # Handle both direct object and nested properties
            if 'properties' in item:
                properties = item['properties']
            else:
                properties = item
            
            # Extract road information - try multiple possible field names
            road_name = (
                properties.get('RoadName') or 
                properties.get('road_name') or 
                properties.get('ROAD_NAME') or 
                properties.get('name') or
                'Unknown Road'
            )
            
            # Debug: Log road name extraction
            if len(features) < 3:  # Log first few for debugging
                logger.info(f"🛣️  Road: '{road_name}' | Available keys: {list(properties.keys())}")
            
            # Extract speed information - convert strings to numbers
            try:
                min_speed = float(
                    properties.get('MinimumSpeed') or
                    properties.get('MINIMUM_SPEED') or 
                    properties.get('min_speed') or 0
                )
                max_speed = float(
                    properties.get('MaximumSpeed') or
                    properties.get('MAXIMUM_SPEED') or 
                    properties.get('max_speed') or 0
                )
            except (ValueError, TypeError):
                min_speed = 0
                max_speed = 0
            
            # Calculate average speed for congestion classification
            avg_speed = (min_speed + max_speed) / 2 if max_speed > 0 else min_speed
            
            # Create geometry from LTA coordinates (StartLon/Lat, EndLon/Lat)
            geometry = None
            
            try:
                start_lon = float(properties.get('StartLon', 0))
                start_lat = float(properties.get('StartLat', 0))
                end_lon = float(properties.get('EndLon', 0))
                end_lat = float(properties.get('EndLat', 0))
                
                # Create LineString geometry from start and end coordinates
                if all([start_lon, start_lat, end_lon, end_lat]):
                    geometry = {
                        "type": "LineString",
                        "coordinates": [[start_lon, start_lat], [end_lon, end_lat]]
                    }
                    matched_roads += 1
                    
                    if len(features) < 3:  # Debug first few
                        logger.info(f"✅ Created geometry for '{road_name}': ({start_lat:.4f},{start_lon:.4f}) -> ({end_lat:.4f},{end_lon:.4f})")
                else:
                    if len(features) < 3:
                        logger.info(f"❌ Missing coordinates for '{road_name}': StartLon={start_lon}, StartLat={start_lat}, EndLon={end_lon}, EndLat={end_lat}")
                        
            except (ValueError, TypeError) as e:
                if len(features) < 3:
                    logger.info(f"❌ Coordinate conversion error for '{road_name}': {str(e)}")
            
            # Only create feature if we have geometry
            if geometry:
                geojson_feature = {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {
                        "road_name": road_name,
                        "speed": avg_speed,
                        "min_speed": min_speed,
                        "max_speed": max_speed,
                        "congestion": classify_congestion(avg_speed),
                        "speed_band": properties.get('SpeedBand', 'unknown')
                    }
                }
                
                features.append(geojson_feature)
        
        logger.info(f"✅ Created geometries for {matched_roads} road segments out of {len(lta_features)} LTA records")
        
        return {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "total_segments": len(features)
            }
        }
    
    except Exception as e:
        logger.error(f"Error transforming data to GeoJSON: {str(e)}")
        return {
            "type": "FeatureCollection",
            "features": [],
            "error": "Data transformation failed"
        }

@lta_bp.route('/traffic-map', methods=['GET'])
def get_traffic_map():
    """
    Fetch real-time traffic speed data from LTA API and return as GeoJSON

    Query Parameters:
    - region: 'North', 'South', 'East', 'West', 'Central', or 'All' (default: 'All')

    Returns:
        JSON: GeoJSON FeatureCollection with traffic data
    """
    try:
        # Get region filter from query params
        region = request.args.get('region', 'All')
        # Get LTA API key from environment variables
        api_key = os.getenv('LTA_API_KEY')
        
        if not api_key:
            return jsonify({
                "error": "Missing LTA API Key",
                "message": "Please set LTA_API_KEY in your .env file"
            }), 500
        
        # LTA DataMall API endpoint for traffic speed bands
        lta_url = "https://datamall2.mytransport.sg/ltaodataservice/v3/TrafficSpeedBands"

        
        # Set up headers for LTA API - must use exact format
        headers = {
            'AccountKey': api_key.strip(),
            'accept': 'application/json'
        }
        logger.info(f"Fetching traffic data from LTA API: {lta_url}")
        logger.info(f"API Key configured: {'Yes' if api_key else 'No'}")
        
        # Make request to LTA API
        response = requests.get(lta_url, headers=headers, timeout=30)
        
        logger.info(f"LTA API Response - Status: {response.status_code}, Content-Type: {response.headers.get('content-type', 'unknown')}")
        
        # Check if request was successful
        if response.status_code == 200:
            # Check if response is actually JSON
            content_type = response.headers.get('content-type', '')
            if 'application/json' not in content_type:
                logger.error(f"LTA API returned non-JSON response. Content-Type: {content_type}")
                logger.error(f"Response content (first 500 chars): {response.text[:500]}")
                return jsonify({
                    "error": "Invalid Response Format",
                    "message": "LTA API returned HTML instead of JSON. This may indicate an API issue or invalid endpoint."
                }), 502
            
            try:
                lta_data = response.json()
            except ValueError as e:
                logger.error(f"Failed to parse JSON from LTA API: {str(e)}")
                logger.error(f"Response content (first 500 chars): {response.text[:500]}")
                return jsonify({
                    "error": "JSON Parse Error",
                    "message": "Unable to parse response from LTA API as JSON"
                }), 502

            # Transform LTA data to GeoJSON format
            geojson_data = transform_to_geojson(lta_data)

            # Apply region filter if specified
            if region != 'All' and region in SINGAPORE_REGIONS:
                original_count = len(geojson_data.get('features', []))
                filtered_features = []
                for feature in geojson_data.get('features', []):
                    coords = feature.get('geometry', {}).get('coordinates', [])
                    if coords and len(coords) >= 2:
                        # Use midpoint of line segment
                        mid_lon = (coords[0][0] + coords[1][0]) / 2
                        mid_lat = (coords[0][1] + coords[1][1]) / 2
                        if is_in_region(mid_lat, mid_lon, region):
                            filtered_features.append(feature)
                geojson_data['features'] = filtered_features
                geojson_data['metadata']['region'] = region
                geojson_data['metadata']['total_segments'] = len(filtered_features)
                logger.info(f"Region filter '{region}': {len(filtered_features)}/{original_count} segments")

            logger.info(f"Successfully processed {len(geojson_data.get('features', []))} traffic segments")

            return jsonify(geojson_data)
        
        elif response.status_code == 401:
            return jsonify({
                "error": "Unauthorized",
                "message": "Invalid LTA API key provided"
            }), 401
        
        elif response.status_code == 403:
            return jsonify({
                "error": "Forbidden", 
                "message": "LTA API access denied - check your account permissions"
            }), 403
        
        else:
            logger.error(f"LTA API error: {response.status_code} - {response.text}")
            return jsonify({
                "error": "LTA API Error",
                "message": f"Failed to fetch data from LTA API: {response.status_code}",
                "details": response.text[:200]  # Limit error details
            }), 502
    
    except requests.exceptions.Timeout:
        logger.error("Timeout when calling LTA API")
        return jsonify({
            "error": "Timeout",
            "message": "Request to LTA API timed out"
        }), 504
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error when calling LTA API: {str(e)}")
        return jsonify({
            "error": "Network Error",
            "message": "Failed to connect to LTA API"
        }), 502
    
    except Exception as e:
        logger.error(f"Unexpected error in get_traffic_map: {str(e)}")
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }), 500

@lta_bp.route('/traffic-map/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for traffic API
    Returns:
        JSON: Status information
    """
    api_key = os.getenv('LTA_API_KEY')
    return jsonify({
        "status": "healthy",
        "service": "Traffic Map API",
        "timestamp": datetime.utcnow().isoformat(),
        "api_key_configured": bool(api_key and api_key != 'your_lta_api_key_here'),
        "lta_api_url": "https://datamall2.mytransport.sg/ltaodataservice/TrafficSpeedBandsv2",
        "endpoints": {
            "traffic_map": "/api/lta/traffic-map",
            "health": "/api/lta/traffic-map/health",
            "test": "/api/lta/traffic-map/test"
        }
    })

@lta_bp.route('/traffic-map/test', methods=['GET'])
def test_lta_connection():
    """
    Test connection to LTA API without processing data
    Returns:
        JSON: Raw response from LTA API for debugging
    """
    try:
        api_key = os.getenv('LTA_API_KEY')
        
        if not api_key or api_key == 'your_lta_api_key_here':
            return jsonify({
                "error": "API key not configured",
                "message": "Please set a valid LTA_API_KEY in your .env file"
            }), 500
        
        lta_url = "http://datamall2.mytransport.sg/ltaodataservice/v3/TrafficSpeedBands"
        headers = {
            'AccountKey': api_key.strip(),
            'accept': 'application/json'
        }
        
        logger.info(f"Testing LTA API connection: {lta_url}")
        
        response = requests.get(lta_url, headers=headers, timeout=30)
        
        return jsonify({
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content_type": response.headers.get('content-type', 'unknown'),
            "response_size": len(response.content),
            "response_preview": response.text[:500] if len(response.text) > 500 else response.text,
            "is_json": 'application/json' in response.headers.get('content-type', ''),
            "url": lta_url
        })
        
    except Exception as e:
        logger.error(f"Error testing LTA API: {str(e)}")
        return jsonify({
            "error": "Connection Error",
            "message": str(e)
        }), 500