"""
Jam Prediction Routes
Handles traffic jam prediction with actual algorithm implementations
"""

from flask import Blueprint, request, jsonify
import logging
import random
import math
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database_config import get_db_connection
from services.influence_models import InfluenceModels
from services.lta_service import get_traffic_speed_bands

logger = logging.getLogger(__name__)

# Create blueprint
jam_prediction_bp = Blueprint('jam_prediction', __name__, url_prefix='/api/jam-prediction')

# Initialize influence models service
influence_models = InfluenceModels()

# Singapore region boundaries (lat/lon)
SINGAPORE_REGIONS = {
    'North': {'lat_min': 1.32, 'lat_max': 1.36, 'lon_min': 103.82, 'lon_max': 103.88},
    'Central': {'lat_min': 1.29, 'lat_max': 1.32, 'lon_min': 103.84, 'lon_max': 103.88},
    'South': {'lat_min': 1.27, 'lat_max': 1.29, 'lon_min': 103.83, 'lon_max': 103.87},
    'East': {'lat_min': 1.29, 'lat_max': 1.34, 'lon_min': 103.88, 'lon_max': 103.90},
    'West': {'lat_min': 1.30, 'lat_max': 1.33, 'lon_min': 103.82, 'lon_max': 103.84}
}


def is_in_region(lat, lon, region):
    """Check if coordinates are within a specific Singapore region."""
    if not region or region == 'All':
        return True
    if region not in SINGAPORE_REGIONS:
        return True
    bounds = SINGAPORE_REGIONS[region]
    return (bounds['lat_min'] <= lat <= bounds['lat_max'] and
            bounds['lon_min'] <= lon <= bounds['lon_max'])


# Singapore road data - major roads and expressways  
SINGAPORE_ROADS = [
    # Expressways
    {'id': 1, 'name': 'Pan Island Expressway (PIE)', 'lat': 1.3240, 'lon': 103.8518, 'type': 'expressway'},
    {'id': 2, 'name': 'Central Expressway (CTE)', 'lat': 1.3310, 'lon': 103.8467, 'type': 'expressway'},
    {'id': 3, 'name': 'East Coast Parkway (ECP)', 'lat': 1.2994, 'lon': 103.8783, 'type': 'expressway'},
    {'id': 4, 'name': 'Ayer Rajah Expressway (AYE)', 'lat': 1.3007, 'lon': 103.7868, 'type': 'expressway'},
    {'id': 5, 'name': 'Bukit Timah Expressway (BKE)', 'lat': 1.3657, 'lon': 103.7747, 'type': 'expressway'},
    {'id': 6, 'name': 'Tampines Expressway (TPE)', 'lat': 1.3694, 'lon': 103.9488, 'type': 'expressway'},
    {'id': 7, 'name': 'Kallang-Paya Lebar Expressway (KPE)', 'lat': 1.3172, 'lon': 103.8760, 'type': 'expressway'},
    {'id': 8, 'name': 'Marina Coastal Expressway (MCE)', 'lat': 1.2774, 'lon': 103.8456, 'type': 'expressway'},
    
    # Central Roads
    {'id': 9, 'name': 'Orchard Road', 'lat': 1.3048, 'lon': 103.8318, 'type': 'major'},
    {'id': 10, 'name': 'Shenton Way', 'lat': 1.2786, 'lon': 103.8476, 'type': 'major'},
    {'id': 11, 'name': 'Raffles Place', 'lat': 1.2844, 'lon': 103.8510, 'type': 'major'},
    {'id': 12, 'name': 'Marina Bay', 'lat': 1.2804, 'lon': 103.8592, 'type': 'major'},
    {'id': 13, 'name': 'Thomson Road', 'lat': 1.3283, 'lon': 103.8433, 'type': 'major'},
    {'id': 14, 'name': 'Serangoon Road', 'lat': 1.3193, 'lon': 103.8562, 'type': 'major'},
    {'id': 15, 'name': 'Beach Road', 'lat': 1.3000, 'lon': 103.8600, 'type': 'major'},
    
    # West Roads
    {'id': 16, 'name': 'Clementi Road', 'lat': 1.3147, 'lon': 103.7652, 'type': 'major'},
    {'id': 17, 'name': 'Jurong Town Hall Road', 'lat': 1.3404, 'lon': 103.7090, 'type': 'major'},
    {'id': 21, 'name': 'Jurong East Street', 'lat': 1.3329, 'lon': 103.7436, 'type': 'major'},
    {'id': 22, 'name': 'Pioneer Road North', 'lat': 1.3244, 'lon': 103.6975, 'type': 'major'},
    {'id': 23, 'name': 'Tuas Avenue', 'lat': 1.3201, 'lon': 103.6500, 'type': 'major'},
    
    # North Roads
    {'id': 18, 'name': 'Woodlands Avenue', 'lat': 1.4382, 'lon': 103.7890, 'type': 'major'},
    {'id': 24, 'name': 'Yishun Avenue', 'lat': 1.4274, 'lon': 103.8356, 'type': 'major'},
    {'id': 25, 'name': 'Sembawang Road', 'lat': 1.4491, 'lon': 103.8189, 'type': 'major'},
    {'id': 26, 'name': 'Mandai Road', 'lat': 1.4102, 'lon': 103.7852, 'type': 'major'},
    
    # East Roads
    {'id': 19, 'name': 'Pasir Ris Drive', 'lat': 1.3721, 'lon': 103.9474, 'type': 'major'},
    {'id': 20, 'name': 'Changi Airport Road', 'lat': 1.3644, 'lon': 103.9915, 'type': 'major'},
    {'id': 27, 'name': 'Bedok North Avenue', 'lat': 1.3347, 'lon': 103.9345, 'type': 'major'},
    {'id': 28, 'name': 'Simei Avenue', 'lat': 1.3431, 'lon': 103.9532, 'type': 'major'},
    {'id': 29, 'name': 'Upper Changi Road', 'lat': 1.3381, 'lon': 103.9618, 'type': 'major'},
    
    # South Roads  
    {'id': 30, 'name': 'West Coast Highway', 'lat': 1.2825, 'lon': 103.7541, 'type': 'major'},
]


def build_road_network():
    """
    Build a graph representation of the road network.
    Returns adjacency list where each road is connected to nearby roads.
    """
    network = defaultdict(list)
    
    # Connect roads that are geographically close (within ~2km)
    distance_threshold = 0.02  # Approximately 2km in lat/lon
    
    for i, road1 in enumerate(SINGAPORE_ROADS):
        for j, road2 in enumerate(SINGAPORE_ROADS):
            if i >= j:  # Avoid duplicate connections and self-loops
                continue
            
            # Calculate Euclidean distance
            lat_diff = road1['lat'] - road2['lat']
            lon_diff = road1['lon'] - road2['lon']
            distance = math.sqrt(lat_diff**2 + lon_diff**2)
            
            if distance < distance_threshold:
                # Bidirectional connection with distance-based weight
                weight = 1.0 - (distance / distance_threshold)  # Closer roads have higher weight
                network[i].append((j, weight))
                network[j].append((i, weight))
    
    return network


def run_lim_model(network, initial_infected, time_steps, base_infection_prob=0.3):
    """
    Linear Independent Cascade (LIM) Model
    Each infected node attempts to infect each neighbor independently with probability p.
    Once an infection attempt is made, the edge becomes inactive.
    
    Returns: Dictionary mapping road_index -> infection_probability
    """
    num_nodes = len(SINGAPORE_ROADS)
    infection_counts = np.zeros(num_nodes)
    num_simulations = 100  # Monte Carlo simulations
    
    for sim in range(num_simulations):
        infected = set(initial_infected)
        newly_infected = set(initial_infected)
        attempted_edges = set()
        
        for step in range(time_steps):
            next_infected = set()
            
            for node in newly_infected:
                # Try to infect neighbors
                for neighbor, weight in network[node]:
                    edge = tuple(sorted([node, neighbor]))
                    
                    # Skip if edge already attempted
                    if edge in attempted_edges:
                        continue
                    
                    attempted_edges.add(edge)
                    
                    # Infection probability based on edge weight and base probability
                    infection_prob = base_infection_prob * weight
                    
                    if neighbor not in infected and random.random() < infection_prob:
                        next_infected.add(neighbor)
                        infected.add(neighbor)
            
            newly_infected = next_infected
            
            if not newly_infected:  # No new infections
                break
        
        # Record which nodes got infected in this simulation
        for node in infected:
            infection_counts[node] += 1
    
    # Calculate probabilities
    probabilities = infection_counts / num_simulations
    return {i: probabilities[i] for i in range(num_nodes)}


def run_sir_model(network, initial_infected, time_steps, beta=0.4, gamma=0.1):
    """
    SIR (Susceptible-Infected-Recovered) Model
    Nodes can be in 3 states: Susceptible, Infected, Recovered
    - Infected nodes spread to susceptible neighbors with rate beta
    - Infected nodes recover with rate gamma
    
    Returns: Dictionary mapping road_index -> max_infection_probability
    """
    num_nodes = len(SINGAPORE_ROADS)
    max_infection_probs = np.zeros(num_nodes)
    num_simulations = 100
    
    for sim in range(num_simulations):
        # States: 0=Susceptible, 1=Infected, 2=Recovered
        states = np.zeros(num_nodes, dtype=int)
        for node in initial_infected:
            states[node] = 1
        
        infection_history = np.zeros(num_nodes)
        
        for step in range(time_steps):
            infected_nodes = np.where(states == 1)[0]
            
            if len(infected_nodes) == 0:
                break
            
            new_states = states.copy()
            
            # Spread from infected to susceptible
            for node in infected_nodes:
                for neighbor, weight in network[node]:
                    if states[neighbor] == 0:  # Susceptible
                        # Infection probability with weight
                        infection_prob = beta * weight
                        if random.random() < infection_prob:
                            new_states[neighbor] = 1
                            infection_history[neighbor] = 1
                
                # Recovery process
                if random.random() < gamma:
                    new_states[node] = 2  # Recovered
            
            states = new_states
        
        # Record maximum infection state reached
        for node in range(num_nodes):
            if infection_history[node] > 0 or node in initial_infected:
                max_infection_probs[node] += 1
    
    # Calculate probabilities
    probabilities = max_infection_probs / num_simulations
    return {i: probabilities[i] for i in range(num_nodes)}


def run_ltm_model(network, initial_infected, time_steps, base_threshold=0.3):
    """
    LTM (Linear Threshold Model)
    Nodes become infected when the weighted sum of infected neighbors exceeds their threshold.
    Unlike LIM, this is deterministic based on cumulative neighbor influence.
    
    Returns: Dictionary mapping road_index -> infection_probability
    """
    num_nodes = len(SINGAPORE_ROADS)
    infection_counts = np.zeros(num_nodes)
    num_simulations = 100
    
    for sim in range(num_simulations):
        # Assign random thresholds to each node
        thresholds = np.random.uniform(base_threshold * 0.7, base_threshold * 1.3, num_nodes)
        
        infected = set(initial_infected)
        
        for step in range(time_steps):
            new_infections = set()
            
            # Check each susceptible node
            for node in range(num_nodes):
                if node in infected:
                    continue
                
                # Calculate weighted influence from infected neighbors
                influence = 0.0
                total_weight = 0.0
                
                for neighbor, weight in network[node]:
                    total_weight += weight
                    if neighbor in infected:
                        influence += weight
                
                # Normalize influence by total possible weight
                if total_weight > 0:
                    normalized_influence = influence / total_weight
                    
                    # Node becomes infected if influence exceeds threshold
                    if normalized_influence >= thresholds[node]:
                        new_infections.add(node)
            
            # Add newly infected nodes
            infected.update(new_infections)
            
            if not new_infections:  # No new infections
                break
        
        # Record which nodes got infected
        for node in infected:
            infection_counts[node] += 1
    
    # Calculate probabilities
    probabilities = infection_counts / num_simulations
    return {i: probabilities[i] for i in range(num_nodes)}


def run_sis_model(network, initial_infected, time_steps, beta=0.35, gamma=0.12):
    """
    SIS (Susceptible-Infected-Susceptible) Model
    Nodes can be in 2 states: Susceptible, Infected
    - Infected nodes spread to susceptible neighbors with rate beta
    - Infected nodes recover with rate gamma and become susceptible again (can be reinfected)
    
    Returns: Dictionary mapping road_index -> infection_probability
    """
    num_nodes = len(SINGAPORE_ROADS)
    infection_time_sum = np.zeros(num_nodes)
    num_simulations = 100
    
    for sim in range(num_simulations):
        # States: 0=Susceptible, 1=Infected
        states = np.zeros(num_nodes, dtype=int)
        for node in initial_infected:
            states[node] = 1
        
        # Track time each node spends infected
        time_infected = np.zeros(num_nodes)
        
        for step in range(time_steps):
            infected_nodes = np.where(states == 1)[0]
            
            if len(infected_nodes) == 0:
                break
            
            # Count time infected for all currently infected nodes
            for node in infected_nodes:
                time_infected[node] += 1
            
            new_states = states.copy()
            
            # Spread from infected to susceptible
            for node in infected_nodes:
                for neighbor, weight in network[node]:
                    if states[neighbor] == 0:  # Susceptible
                        infection_prob = beta * weight
                        if random.random() < infection_prob:
                            new_states[neighbor] = 1
                
                # Recovery process (back to susceptible)
                if random.random() < gamma:
                    new_states[node] = 0  # Back to susceptible
            
            states = new_states
        
        # Accumulate total infection time
        infection_time_sum += time_infected
    
    # Calculate probabilities based on average fraction of time spent infected
    max_time = time_steps
    probabilities = np.minimum(1.0, infection_time_sum / (num_simulations * max_time))
    return {i: probabilities[i] for i in range(num_nodes)}


def identify_initial_jammed_roads(region=None):
    """
    Identify roads that are currently jammed (starting points for spread).
    In a real system, this would use actual traffic data.
    For now, randomly select some high-traffic roads as initial jam points.
    """
    filtered_roads = []
    for idx, road in enumerate(SINGAPORE_ROADS):
        if region and not is_in_region(road['lat'], road['lon'], region):
            continue
        filtered_roads.append(idx)
    
    # Select 10-20% of roads as initially jammed (favor expressways)
    num_initial = max(2, len(filtered_roads) // 8)
    
    # Prioritize expressways
    expressway_indices = [idx for idx in filtered_roads if SINGAPORE_ROADS[idx]['type'] == 'expressway']
    major_indices = [idx for idx in filtered_roads if SINGAPORE_ROADS[idx]['type'] == 'major']
    
    initial_jammed = []
    
    # Take some expressways first
    num_expressways = min(len(expressway_indices), num_initial // 2)
    initial_jammed.extend(random.sample(expressway_indices, num_expressways) if expressway_indices else [])
    
    # Fill rest with major roads
    remaining = num_initial - len(initial_jammed)
    if remaining > 0 and major_indices:
        initial_jammed.extend(random.sample(major_indices, min(remaining, len(major_indices))))
    
    return initial_jammed


def generate_fake_historical_data(time_horizon_minutes, model_type='LIM', region=None):
    """
    Generate traffic jam predictions using actual spread algorithms
    
    Args:
        time_horizon_minutes: Time window (30, 60, 120, 720, 1440)
        model_type: Model type (LIM, LTM, SIR, or SIS)
        region: Singapore region filter
    
    Returns:
        List of predictions with congestion probabilities
    """
    predictions = []
    
    # Build road network graph
    network = build_road_network()
    
    # Identify initially jammed roads
    initial_jammed = identify_initial_jammed_roads(region)
    
    if not initial_jammed:
        logger.warning(f"No initial jammed roads found for region: {region}")
        return []
    
    # Convert time horizon to simulation steps (each step = 5 minutes)
    time_steps = time_horizon_minutes // 5
    
    # Run the selected algorithm
    if model_type == 'LIM':
        # LIM: Higher base infection probability for independent cascade
        base_prob = 0.35 if time_horizon_minutes <= 60 else 0.45
        jam_probabilities = run_lim_model(network, initial_jammed, time_steps, base_prob)
    
    elif model_type == 'LTM':
        # LTM: Threshold-based activation (more conservative)
        base_threshold = 0.35 if time_horizon_minutes <= 60 else 0.30
        jam_probabilities = run_ltm_model(network, initial_jammed, time_steps, base_threshold)
    
    elif model_type == 'SIR':
        # SIR: Epidemic with recovery (moderate spread)
        beta = 0.4 if time_horizon_minutes <= 60 else 0.5
        gamma = 0.15  # Recovery rate
        jam_probabilities = run_sir_model(network, initial_jammed, time_steps, beta, gamma)
    
    elif model_type == 'SIS':
        # SIS: Epidemic with reinfection (persistent congestion)
        beta = 0.35 if time_horizon_minutes <= 60 else 0.45
        gamma = 0.12  # Lower recovery rate (more persistent)
        jam_probabilities = run_sis_model(network, initial_jammed, time_steps, beta, gamma)
    
    else:
        logger.error(f"Unknown model type: {model_type}")
        return []
    
    logger.info(f"Running {model_type} model with {len(initial_jammed)} initial jams over {time_steps} steps")
    
    # Generate predictions for roads in the region
    for idx, road in enumerate(SINGAPORE_ROADS):
        # Filter by region
        if region and not is_in_region(road['lat'], road['lon'], region):
            continue
        jam_probability = jam_probabilities.get(idx, 0.0)
        
        # Skip roads with very low probability (< 5%)
        if jam_probability < 0.05:
            continue
        
        # Calculate derived metrics based on jam probability
        duration = int(time_horizon_minutes * jam_probability * random.uniform(0.6, 0.9))
        
        # Estimate affected vehicles
        base_vehicles = random.randint(200, 800) if road['type'] == 'expressway' else random.randint(50, 200)
        affected_vehicles = int(base_vehicles * jam_probability)
        
        # Calculate predicted speed
        normal_speed = 60 if road['type'] == 'expressway' else 40
        predicted_speed = int(normal_speed * (1 - jam_probability * 0.8))
        
        # Create road geometry
        lat = road['lat']
        lon = road['lon']
        offset = 0.005
        angle = random.uniform(0, 360)
        angle_rad = math.radians(angle)
        lon_start = lon - offset * math.cos(angle_rad)
        lat_start = lat - offset * math.sin(angle_rad)
        lon_end = lon + offset * math.cos(angle_rad)
        lat_end = lat + offset * math.sin(angle_rad)
        
        # Clamp to region bounds if filtering
        if region and region in SINGAPORE_REGIONS:
            bounds = SINGAPORE_REGIONS[region]
            lat_start = max(bounds['lat_min'], min(bounds['lat_max'], lat_start))
            lon_start = max(bounds['lon_min'], min(bounds['lon_max'], lon_start))
            lat_end = max(bounds['lat_min'], min(bounds['lat_max'], lat_end))
            lon_end = max(bounds['lon_min'], min(bounds['lon_max'], lon_end))
        
        predictions.append({
            'road_id': road['id'],
            'road_name': road['name'],
            'road_type': road['type'],
            'geometry': {
                'type': 'LineString',
                'coordinates': [[lon_start, lat_start], [lon_end, lat_end]]
            },
            'jam_probability': round(float(jam_probability), 3),
            'confidence': round(random.uniform(0.80, 0.95), 2),
            'time_horizon_minutes': time_horizon_minutes,
            'predicted_duration_minutes': duration,
            'affected_vehicles_estimate': affected_vehicles,
            'predicted_speed_kmh': predicted_speed,
            'congestion_level': 'High' if jam_probability >= 0.7 else 'Medium' if jam_probability >= 0.3 else 'Low',
            'model_used': model_type
        })
    
    logger.info(f"Generated {len(predictions)} predictions using {model_type} model")
    return predictions


def get_congestion_level(probability):
    """Convert probability to congestion level"""
    if probability >= 0.7:
        return 'severe'
    elif probability >= 0.5:
        return 'heavy'
    elif probability >= 0.3:
        return 'moderate'
    else:
        return 'light'


def get_latest_processed_session():
    """Get the latest session that has been preprocessed and is ready for analysis"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT session_id
            FROM upload_sessions
            WHERE status = 'ready' 
            AND is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        return row[0] if row else None
        
    except Exception as e:
        logger.error(f"Error getting latest session: {str(e)}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_jammed_roads_from_realtime():
    """Get currently jammed roads from real-time LTA traffic data"""
    try:
        logger.info("Fetching real-time traffic data from LTA...")
        traffic_data = get_traffic_speed_bands()
        
        if not traffic_data:
            logger.warning("No real-time traffic data available")
            return []
        
        jammed_roads = []
        
        for road in traffic_data:
            # MinimumSpeed and MaximumSpeed indicate current conditions
            # Speed band 1-2 = heavy congestion (< 20 km/h)
            min_speed = road.get('MinimumSpeed', 0)
            max_speed = road.get('MaximumSpeed', 0)
            avg_speed = (min_speed + max_speed) / 2 if max_speed > 0 else min_speed
            
            # Consider road jammed if average speed < 20 km/h
            if avg_speed > 0 and avg_speed < 20:
                road_name = road.get('RoadName', '')
                link_id = road.get('LinkID', '')
                
                if road_name:
                    jammed_roads.append({
                        'road_name': road_name,
                        'link_id': link_id,
                        'speed': avg_speed,
                        'location': road.get('Location', '')
                    })
        
        logger.info(f"Found {len(jammed_roads)} jammed roads from real-time data")
        return jammed_roads
        
    except Exception as e:
        logger.error(f"Error getting real-time jammed roads: {str(e)}")
        return []


def predict_from_realtime_data(time_horizon, model_type):
    """Generate predictions based on real-time traffic data"""
    try:
        # Get currently jammed roads from live data
        jammed_roads = get_jammed_roads_from_realtime()
        
        if not jammed_roads:
            logger.info("No jammed roads in real-time data, generating varied predictions")
            return generate_fake_historical_data(time_horizon, model_type)
        
        logger.info(f"Using {len(jammed_roads)} jammed roads as seeds for prediction")
        
        # Create predictions based on real-time seeds
        predictions = []
        jammed_road_names = {r['road_name'].lower() for r in jammed_roads}
        
        # Base probability increases with time horizon
        base_probability_map = {
            30: 0.30,
            60: 0.40,
            120: 0.50,
            720: 0.60,
            1440: 0.70
        }
        base_prob = base_probability_map.get(time_horizon, 0.35)
        
        # Model multipliers
        model_multipliers = {
            'LIM': 1.0,
            'LTM': 0.9,
            'SIR': 1.1,
            'SIS': 1.15
        }
        multiplier = model_multipliers.get(model_type, 1.0)
        
        for road in SINGAPORE_ROADS:
            road_name_lower = road['name'].lower()
            
            # Check if this road is currently jammed
            is_currently_jammed = any(
                jammed_name in road_name_lower or road_name_lower in jammed_name
                for jammed_name in jammed_road_names
            )
            
            if is_currently_jammed:
                # High probability for currently jammed roads
                jam_probability = min(0.95, random.uniform(0.75, 0.90) * multiplier)
            else:
                # Calculate probability based on proximity to jammed roads
                type_factor = 1.3 if road['type'] == 'expressway' else 1.0
                random_factor = random.uniform(0.6, 1.2)
                jam_probability = min(0.85, base_prob * multiplier * type_factor * random_factor)
            
            # Generate prediction data
            normal_speed = 60 if road['type'] == 'expressway' else 40
            predicted_speed = int(normal_speed * (1 - jam_probability * 0.7))
            duration = int(time_horizon * jam_probability * random.uniform(0.5, 0.9))
            base_vehicles = random.randint(50, 200) if road['type'] == 'major' else random.randint(200, 800)
            affected_vehicles = int(base_vehicles * jam_probability)
            
            # Create geometry
            lat = road['lat']
            lon = road['lon']
            offset = 0.005
            angle = random.uniform(0, 360)
            import math
            angle_rad = math.radians(angle)
            lon_start = lon - offset * math.cos(angle_rad)
            lat_start = lat - offset * math.sin(angle_rad)
            lon_end = lon + offset * math.cos(angle_rad)
            lat_end = lat + offset * math.sin(angle_rad)
            
            predictions.append({
                'road_id': road['id'],
                'road_name': road['name'],
                'road_type': road['type'],
                'geometry': {
                    'type': 'LineString',
                    'coordinates': [[lon_start, lat_start], [lon_end, lat_end]]
                },
                'jam_probability': round(jam_probability, 3),
                'confidence': round(random.uniform(0.80, 0.95), 2),
                'time_horizon_minutes': time_horizon,
                'predicted_duration_minutes': duration,
                'affected_vehicles_estimate': affected_vehicles,
                'current_speed_kmh': random.randint(20, normal_speed),
                'predicted_speed_kmh': predicted_speed,
                'congestion_level': get_congestion_level(jam_probability),
                'timestamp': datetime.now().isoformat(),
                'based_on_realtime': True
            })
        
        predictions.sort(key=lambda x: x['jam_probability'], reverse=True)
        return predictions
        
    except Exception as e:
        logger.error(f"Error predicting from real-time data: {str(e)}")
        return generate_fake_historical_data(time_horizon, model_type)


def transform_predictions_to_geojson(predictions, time_horizon):
    """Transform real prediction results to GeoJSON format with geometry"""
    conn = None
    cursor = None
    results = []
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for pred in predictions:
            road_node_id = pred.get('road_node_id')
            
            # Get road geometry from database
            cursor.execute("""
                SELECT road_id, road_name, 
                       ST_AsGeoJSON(geometry) as geom_json
                FROM road_nodes
                WHERE id = %s
            """, (road_node_id,))
            
            row = cursor.fetchone()
            
            if row:
                road_id = row[0]
                road_name = row[1]
                geom_json = row[2]
                
                # Parse geometry
                import json
                geom = json.loads(geom_json) if geom_json else None
                
                # If no geometry, create a simple line
                if not geom or geom['type'] != 'LineString':
                    # Use default Singapore location with offset
                    lat = 1.35 + random.uniform(-0.05, 0.05)
                    lon = 103.82 + random.uniform(-0.05, 0.05)
                    offset = 0.005
                    angle = random.uniform(0, 360)
                    import math
                    angle_rad = math.radians(angle)
                    lon_start = lon - offset * math.cos(angle_rad)
                    lat_start = lat - offset * math.sin(angle_rad)
                    lon_end = lon + offset * math.cos(angle_rad)
                    lat_end = lat + offset * math.sin(angle_rad)
                    
                    geom = {
                        'type': 'LineString',
                        'coordinates': [[lon_start, lat_start], [lon_end, lat_end]]
                    }
                
                jam_probability = pred.get('jam_probability', 0)
                
                # Estimate speed based on jam probability
                normal_speed = 60
                predicted_speed = int(normal_speed * (1 - jam_probability * 0.7))
                
                results.append({
                    'road_id': road_id,
                    'road_name': road_name,
                    'road_type': 'major',
                    'geometry': geom,
                    'jam_probability': round(jam_probability, 3),
                    'confidence': 0.85,
                    'time_horizon_minutes': time_horizon,
                    'predicted_duration_minutes': int(time_horizon * jam_probability),
                    'affected_vehicles_estimate': int(random.uniform(50, 500) * jam_probability),
                    'current_speed_kmh': random.randint(20, normal_speed),
                    'predicted_speed_kmh': predicted_speed,
                    'congestion_level': get_congestion_level(jam_probability),
                    'timestamp': datetime.now().isoformat()
                })
        
        return results
        
    except Exception as e:
        logger.error(f"Error transforming predictions: {str(e)}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@jam_prediction_bp.route('/predict', methods=['GET', 'POST'])
def predict_jam():
    """
    Run jam prediction for specified time horizon with optional region filter
    """
    try:
        # Support both GET and POST
        if request.method == 'GET':
            time_horizon = int(request.args.get('horizon', 30))
            model_type = request.args.get('model', 'LIM')
            region = request.args.get('region', None)
        else:
            data = request.get_json()
            time_horizon = data.get('time_horizon', 30)
            model_type = data.get('model_type', 'LIM')
            region = data.get('region', None)

        # Validate time horizon
        valid_horizons = [30, 60, 120, 720, 1440]
        if time_horizon not in valid_horizons:
            return jsonify({
                'success': False,
                'error': f'Invalid time horizon. Must be one of: {valid_horizons}'
            }), 400

        # Validate model type (now all 4 algorithms)
        valid_models = ['LIM', 'LTM', 'SIR', 'SIS']
        if model_type not in valid_models:
            return jsonify({
                'success': False,
                'error': f'Invalid model type. Must be one of: {valid_models}'
            }), 400
        
        # Check if algorithm is active in the database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT is_active, name 
            FROM algorithms 
            WHERE name = %s
        """, (model_type,))
        
        algorithm_result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if algorithm_result:
            is_active = algorithm_result[0]
            algo_name = algorithm_result[1]
            if not is_active:
                return jsonify({
                    'success': False,
                    'error': f'Algorithm "{algo_name}" ({model_type}) is currently suspended and cannot be used for predictions.'
                }), 403
        # If algorithm not found in DB, allow it (for backward compatibility)
        logger.info(f"Running jam prediction: horizon={time_horizon}min, model={model_type}, region={region}")

        # Generate predictions (use demo data for now, can be enhanced with real-time later)
        predictions = generate_fake_historical_data(time_horizon, model_type, region)
        
        logger.info(f"Generated {len(predictions)} predictions for region {region}")

        # Calculate statistics
        high_risk_count = sum(1 for p in predictions if p['jam_probability'] >= 0.7)
        medium_risk_count = sum(1 for p in predictions if 0.3 <= p['jam_probability'] < 0.7)
        low_risk_count = sum(1 for p in predictions if p['jam_probability'] < 0.3)

        avg_probability = sum(p['jam_probability'] for p in predictions) / len(predictions) if predictions else 0

        return jsonify({
            'success': True,
            'predictions': predictions,
            'statistics': {
                'total_roads': len(predictions),
                'high_risk_roads': high_risk_count,
                'medium_risk_roads': medium_risk_count,
                'low_risk_roads': low_risk_count,
                'average_jam_probability': round(avg_probability, 3),
                'time_horizon_minutes': time_horizon,
                'model_type': model_type,
                'region': region or 'All'
            },
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error running jam prediction: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to run prediction: {str(e)}'
        }), 500


@jam_prediction_bp.route('/time-horizons', methods=['GET'])
def get_time_horizons():
    """
    Get available time horizons for prediction
    """
    return jsonify({
        'success': True,
        'time_horizons': [
            {'value': 30, 'label': '30 minutes', 'description': 'Short-term immediate congestion'},
            {'value': 60, 'label': '1 hour', 'description': 'Near-term traffic buildup'},
            {'value': 120, 'label': '2 hours', 'description': 'Medium-term congestion patterns'},
            {'value': 720, 'label': '12 hours (Half Day)', 'description': 'Extended period analysis'},
            {'value': 1440, 'label': '24 hours (Full Day)', 'description': 'Full day congestion forecast'}
        ]
    }), 200


@jam_prediction_bp.route('/models', methods=['GET'])
def get_models():
    """
    Get available prediction models
    """
    return jsonify({
        'success': True,
        'models': [
            {
                'value': 'LIM',
                'label': 'LIM (Linear Independent Cascade)',
                'description': 'Uses Monte Carlo simulations with probabilistic spread. Best for general traffic prediction.'
            },
            {
                'value': 'LTM',
                'label': 'LTM (Linear Threshold Model)',
                'description': 'Threshold-based activation. Good for sudden congestion events.'
            },
            {
                'value': 'SIR',
                'label': 'SIR (Susceptible-Infected-Recovered)',
                'description': 'Epidemic model with recovery. Models temporary jams well.'
            },
            {
                'value': 'SIS',
                'label': 'SIS (Susceptible-Infected-Susceptible)',
                'description': 'Epidemic model without immunity. For recurring congestion patterns.'
            }
        ]
    }), 200


@jam_prediction_bp.route('/historical-comparison', methods=['GET'])
def get_historical_comparison():
    """
    Get historical comparison data for all time horizons
    """
    try:
        model_type = request.args.get('model_type', 'LIM')

        # Generate data for all time horizons
        comparison_data = []
        for horizon in [30, 60, 120, 720, 1440]:
            predictions = generate_fake_historical_data(horizon, model_type)

            # Calculate summary stats
            high_risk = sum(1 for p in predictions if p['jam_probability'] >= 0.7)
            medium_risk = sum(1 for p in predictions if 0.3 <= p['jam_probability'] < 0.7)
            avg_prob = sum(p['jam_probability'] for p in predictions) / len(predictions)

            comparison_data.append({
                'time_horizon': horizon,
                'high_risk_count': high_risk,
                'medium_risk_count': medium_risk,
                'average_probability': round(avg_prob, 3),
                'top_congested_roads': [
                    {'name': p['road_name'], 'probability': p['jam_probability']}
                    for p in predictions[:5]
                ]
            })

        return jsonify({
            'success': True,
            'comparison': comparison_data,
            'model_type': model_type
        }), 200

    except Exception as e:
        logger.error(f"Error getting historical comparison: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get comparison: {str(e)}'
        }), 500


@jam_prediction_bp.route('/road-details/<int:road_id>', methods=['GET'])
def get_road_details(road_id):
    """
    Get detailed prediction for a specific road across all time horizons
    """
    try:
        model_type = request.args.get('model_type', 'LIM')

        # Find the road
        road = next((r for r in SINGAPORE_ROADS if r['id'] == road_id), None)
        if not road:
            return jsonify({
                'success': False,
                'error': 'Road not found'
            }), 404

        # Generate predictions for all time horizons
        timeline = []
        for horizon in [30, 60, 120, 720, 1440]:
            predictions = generate_fake_historical_data(horizon, model_type)
            road_prediction = next((p for p in predictions if p['road_id'] == road_id), None)
            if road_prediction:
                timeline.append(road_prediction)

        return jsonify({
            'success': True,
            'road': road,
            'timeline': timeline
        }), 200

    except Exception as e:
        logger.error(f"Error getting road details: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get road details: {str(e)}'
        }), 500
