"""
OneMap API Service for Singapore geocoding and routing.
Uses OSRM (Open Source Routing Machine) for routing - no auth required.
"""

import os
import requests
from datetime import datetime, timedelta

ONEMAP_BASE_URL = "https://www.onemap.gov.sg/api"
OSRM_BASE_URL = "https://router.project-osrm.org/route/v1"


def search_location(query, limit=10):
    """
    Search for locations in Singapore using OneMap.
    (Search API doesn't require authentication)
    """
    if not query or len(query) < 2:
        return []

    try:
        response = requests.get(
            f"{ONEMAP_BASE_URL}/common/elastic/search",
            params={
                "searchVal": query,
                "returnGeom": "Y",
                "getAddrDetails": "Y",
                "pageNum": 1
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])

        locations = []
        for result in results[:limit]:
            locations.append({
                "name": result.get("SEARCHVAL", ""),
                "address": result.get("ADDRESS", ""),
                "lat": float(result.get("LATITUDE", 0)),
                "lon": float(result.get("LONGITUDE", 0)),
                "postalCode": result.get("POSTAL", ""),
                "buildingName": result.get("BUILDING", "")
            })

        return locations

    except requests.RequestException as e:
        print(f"Error searching location: {e}")
        return []
    except (ValueError, KeyError) as e:
        print(f"Error parsing location data: {e}")
        return []


def get_route(start_lat, start_lon, end_lat, end_lon, route_type="drive"):
    """
    Get driving route using OSRM (free, no auth required).
    """
    try:
        # OSRM expects lon,lat format (opposite of what we have)
        response = requests.get(
            f"{OSRM_BASE_URL}/driving/{start_lon},{start_lat};{end_lon},{end_lat}",
            params={
                "overview": "full",
                "geometries": "geojson",
                "steps": "true"
            },
            timeout=15
        )
        response.raise_for_status()
        data = response.json()

        if data.get("code") == "Ok" and data.get("routes"):
            route = data["routes"][0]

            # Extract path coordinates (OSRM returns [lon, lat], Leaflet needs [lat, lon])
            geometry = route.get("geometry", {})
            coordinates = geometry.get("coordinates", [])
            path_coords = [[coord[1], coord[0]] for coord in coordinates]

            # Extract road segments from steps
            segments = []
            legs = route.get("legs", [])
            for leg in legs:
                steps = leg.get("steps", [])
                for step in steps:
                    road_name = step.get("name", "")
                    if road_name and road_name != "":
                        segments.append({
                            "roadName": road_name,
                            "distance": step.get("distance", 0),
                            "duration": step.get("duration", 0),
                            "direction": step.get("maneuver", {}).get("type", "")
                        })

            # If no segments, add a default
            if not segments:
                segments.append({
                    "roadName": "Route",
                    "distance": route.get("distance", 0),
                    "duration": route.get("duration", 0),
                    "direction": "drive"
                })

            return {
                "found": True,
                "distance": route.get("distance", 0) / 1000,  # Convert to km
                "estimatedTime": route.get("duration", 0) / 60,  # Convert to minutes
                "path": path_coords,
                "segments": segments
            }
        else:
            return {
                "found": False,
                "error": "No route found between these locations"
            }

    except requests.RequestException as e:
        print(f"Error getting route from OSRM: {e}")
        return {
            "found": False,
            "error": f"Failed to get route: {str(e)}"
        }
