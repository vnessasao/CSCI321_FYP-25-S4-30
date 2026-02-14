"""
Traffic API routes for route status and location search.
"""

from flask import Blueprint, request, jsonify
from services.lta_service import (
    get_traffic_speed_bands,
    speed_band_to_congestion,
    get_congestion_for_location
)
from services.onemap_service import search_location, get_route

traffic_bp = Blueprint("traffic", __name__)


@traffic_bp.route("/search", methods=["GET"])
def search_locations():
    """
    Search for locations in Singapore.

    Query params:
        query: Search string (required, min 2 characters)

    Returns:
        List of matching locations with coordinates
    """
    query = request.args.get("query", "").strip()

    if len(query) < 2:
        return jsonify({
            "success": False,
            "error": "Query must be at least 2 characters",
            "results": []
        }), 400

    results = search_location(query, limit=10)

    return jsonify({
        "success": True,
        "results": results
    })


@traffic_bp.route("/route", methods=["POST"])
def get_route_traffic():
    """
    Get route between two points with real-time traffic data.

    Body:
        start: { lat, lon } - Starting coordinates
        end: { lat, lon } - Ending coordinates

    Returns:
        Route with distance, time, segments with congestion levels
    """
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "error": "Request body is required"
        }), 400

    start = data.get("start")
    end = data.get("end")

    if not start or not end:
        return jsonify({
            "success": False,
            "error": "Both start and end coordinates are required"
        }), 400

    try:
        start_lat = float(start.get("lat"))
        start_lon = float(start.get("lon"))
        end_lat = float(end.get("lat"))
        end_lon = float(end.get("lon"))
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "error": "Invalid coordinates format"
        }), 400

    route_data = get_route(start_lat, start_lon, end_lat, end_lon)

    if not route_data.get("found"):
        return jsonify({
            "success": False,
            "error": route_data.get("error", "Route not found")
        }), 404

    speed_bands = get_traffic_speed_bands()

    segments_with_traffic = []
    total_delay = 0

    for segment in route_data.get("segments", []):
        road_name = segment.get("roadName", "Unknown Road")

        matching_band = None
        for band in speed_bands:
            if band.get("RoadName", "").lower() in road_name.lower() or \
               road_name.lower() in band.get("RoadName", "").lower():
                matching_band = band
                break

        if matching_band:
            speed_band = matching_band.get("SpeedBand", 8)
            congestion = speed_band_to_congestion(speed_band)
            min_speed = matching_band.get("MinimumSpeed", 60)

            if congestion == "heavy":
                delay = 5
            elif congestion == "moderate":
                delay = 2
            else:
                delay = 0
        else:
            speed_band = 8
            congestion = "free"
            delay = 0
            min_speed = 60

        total_delay += delay

        segments_with_traffic.append({
            "roadName": road_name,
            "distance": segment.get("distance", 0),
            "speedBand": speed_band,
            "congestion": congestion,
            "delay": delay,
            "minSpeed": min_speed
        })

    path = route_data.get("path", [])

    return jsonify({
        "success": True,
        "distance": round(route_data.get("distance", 0), 2),
        "estimatedTime": round(route_data.get("estimatedTime", 0) + total_delay, 0),
        "baseTime": round(route_data.get("estimatedTime", 0), 0),
        "totalDelay": total_delay,
        "segments": segments_with_traffic,
        "route": path
    })


@traffic_bp.route("/speed-bands", methods=["GET"])
def get_speed_bands():
    """
    Get all current traffic speed bands.

    Returns:
        List of all road segments with speed band data
    """
    bands = get_traffic_speed_bands()

    processed = []
    for band in bands[:100]:
        processed.append({
            "linkId": band.get("LinkID", ""),
            "roadName": band.get("RoadName", ""),
            "speedBand": band.get("SpeedBand", 8),
            "congestion": speed_band_to_congestion(band.get("SpeedBand", 8)),
            "minSpeed": band.get("MinimumSpeed", 0),
            "maxSpeed": band.get("MaximumSpeed", 0)
        })

    return jsonify({
        "success": True,
        "count": len(bands),
        "sample": processed
    })
