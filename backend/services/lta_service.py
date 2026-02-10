"""
LTA DataMall API Service for real-time traffic data.
"""

import os
import requests
from datetime import datetime, timedelta

LTA_BASE_URL = "http://datamall2.mytransport.sg/ltaodataservice"

# Simple in-memory cache
_cache = {}
CACHE_TTL_MINUTES = 5


def _get_api_key():
    """Get LTA API key from environment."""
    return os.getenv("LTA_API_KEY")


def _get_headers():
    """Get headers for LTA API requests."""
    return {
        "AccountKey": _get_api_key(),
        "accept": "application/json"
    }


def _is_cache_valid(cache_key):
    """Check if cached data is still valid."""
    if cache_key not in _cache:
        return False
    cached_time = _cache[cache_key].get("timestamp")
    if not cached_time:
        return False
    return datetime.now() - cached_time < timedelta(minutes=CACHE_TTL_MINUTES)


def get_traffic_speed_bands():
    """
    Fetch real-time traffic speed bands from LTA.

    Returns list of road segments with speed bands (1-8 scale).
    Speed bands:
        1-2: Heavy congestion
        3-4: Moderate congestion
        5-8: Free flow
    """
    cache_key = "speed_bands"

    if _is_cache_valid(cache_key):
        return _cache[cache_key]["data"]

    try:
        all_records = []
        skip = 0

        while True:
            response = requests.get(
                f"{LTA_BASE_URL}/v3/TrafficSpeedBands",
                headers=_get_headers(),
                params={"$skip": skip},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            records = data.get("value", [])
            if not records:
                break

            all_records.extend(records)
            skip += len(records)

            if len(records) < 500:
                break

        _cache[cache_key] = {
            "data": all_records,
            "timestamp": datetime.now()
        }

        return all_records

    except requests.RequestException as e:
        print(f"Error fetching speed bands: {e}")
        if cache_key in _cache:
            return _cache[cache_key]["data"]
        return []


def get_estimated_travel_times():
    """
    Fetch estimated travel times between expressway segments.

    Returns list of travel time estimates.
    """
    cache_key = "travel_times"

    if _is_cache_valid(cache_key):
        return _cache[cache_key]["data"]

    try:
        response = requests.get(
            f"{LTA_BASE_URL}/EstTravelTimes",
            headers=_get_headers(),
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        records = data.get("value", [])

        _cache[cache_key] = {
            "data": records,
            "timestamp": datetime.now()
        }

        return records

    except requests.RequestException as e:
        print(f"Error fetching travel times: {e}")
        if cache_key in _cache:
            return _cache[cache_key]["data"]
        return []


def speed_band_to_congestion(speed_band):
    """
    Convert LTA speed band (1-8) to congestion level.

    Args:
        speed_band: Integer 1-8 from LTA API

    Returns:
        String: 'heavy', 'moderate', or 'free'
    """
    try:
        band = int(speed_band)
        if band <= 2:
            return "heavy"
        elif band <= 4:
            return "moderate"
        else:
            return "free"
    except (ValueError, TypeError):
        return "free"


def get_congestion_for_location(lat, lon, speed_bands=None):
    """
    Find congestion level for a specific location.

    Args:
        lat: Latitude
        lon: Longitude
        speed_bands: Optional pre-fetched speed bands

    Returns:
        Dict with road info and congestion level
    """
    if speed_bands is None:
        speed_bands = get_traffic_speed_bands()

    if not speed_bands:
        return None

    closest = None
    min_distance = float('inf')

    for segment in speed_bands:
        location = segment.get("Location", "")
        if not location:
            continue

        try:
            coords = location.split()
            for i in range(0, len(coords) - 1, 2):
                seg_lon = float(coords[i])
                seg_lat = float(coords[i + 1])

                distance = ((lat - seg_lat) ** 2 + (lon - seg_lon) ** 2) ** 0.5

                if distance < min_distance:
                    min_distance = distance
                    closest = segment
        except (ValueError, IndexError):
            continue

    if closest and min_distance < 0.01:
        return {
            "roadName": closest.get("RoadName", "Unknown Road"),
            "speedBand": closest.get("SpeedBand", 8),
            "congestion": speed_band_to_congestion(closest.get("SpeedBand", 8)),
            "linkId": closest.get("LinkID", "")
        }

    return None
