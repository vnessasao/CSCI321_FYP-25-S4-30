"""
Script to download Singapore road network from OpenStreetMap
and save as GeoJSON for traffic map visualization
"""

import osmnx as ox
import geopandas as gpd
import json
import os
from pathlib import Path

def download_singapore_roads():
    """
    Download Singapore road network from OpenStreetMap and save as GeoJSON
    """
    print("📍 Downloading Singapore road network from OpenStreetMap...")
    
    # Define Singapore bounding box for more precise control
    # Singapore boundaries: roughly 1.16°N to 1.48°N, 103.6°E to 104.0°E
    place = "Singapore"
    
    try:
        # Download road network - only drivable roads
        print("🚗 Fetching drivable roads...")
        G = ox.graph_from_place(
            place, 
            network_type='drive',  # Only drivable roads
            simplify=True,         # Simplify road geometry
            retain_all=False       # Remove isolated road segments
        )
        
        print(f"✅ Downloaded road network with {len(G.nodes)} nodes and {len(G.edges)} edges")
        
        # Convert graph to GeoDataFrame (edges = road segments)
        print("🗺️  Converting to GeoDataFrame...")
        gdf_edges = ox.graph_to_gdfs(G, nodes=False, edges=True)
        
        # Clean and prepare the data
        gdf_edges = gdf_edges.reset_index()
        
        # Create unique road segment ID
        gdf_edges['road_id'] = gdf_edges.index.astype(str)
        
        # Clean road names for better matching with LTA data
        gdf_edges['road_name_clean'] = gdf_edges['name'].fillna('Unknown Road')
        
        # Convert to standard GeoJSON format
        gdf_edges = gdf_edges.to_crs('EPSG:4326')  # Ensure WGS84 coordinates
        
        # Select relevant columns
        columns_to_keep = [
            'road_id', 'name', 'road_name_clean', 'highway', 'length', 'geometry'
        ]
        
        # Keep only existing columns
        available_columns = [col for col in columns_to_keep if col in gdf_edges.columns]
        gdf_clean = gdf_edges[available_columns].copy()
        
        # Create data directory if it doesn't exist
        data_dir = Path(__file__).parent / 'data'
        data_dir.mkdir(exist_ok=True)
        
        # Save as GeoJSON
        output_file = data_dir / 'roads.geojson'
        print(f"💾 Saving to {output_file}...")
        
        gdf_clean.to_file(output_file, driver="GeoJSON")
        
        print(f"✅ Singapore roads saved successfully!")
        print(f"📊 Total road segments: {len(gdf_clean)}")
        print(f"📍 File location: {output_file}")
        
        # Create a road name mapping for quick lookup
        road_map_file = data_dir / 'road_name_mapping.json'
        print(f"🗂️  Creating road name mapping...")
        
        # Create mapping from road name to geometry
        road_mapping = {}
        for idx, row in gdf_clean.iterrows():
            road_name = row.get('name', 'Unknown Road')
            
            # Handle cases where road_name might be a list
            if isinstance(road_name, list):
                # Take the first name if it's a list
                road_name = road_name[0] if road_name else 'Unknown Road'
            elif road_name is None:
                road_name = 'Unknown Road'
            
            # Convert to string and clean
            road_name = str(road_name).strip()
            
            if road_name and road_name != 'Unknown Road' and road_name != 'nan':
                # Store geometry as GeoJSON
                if hasattr(row.geometry, '__geo_interface__'):
                    road_mapping[road_name] = row.geometry.__geo_interface__
        
        with open(road_map_file, 'w') as f:
            json.dump(road_mapping, f, indent=2)
        
        print(f"✅ Road name mapping saved with {len(road_mapping)} named roads")
        print(f"📍 Mapping file: {road_map_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error downloading Singapore roads: {str(e)}")
        return False

if __name__ == "__main__":
    success = download_singapore_roads()
    if success:
        print("\n🎉 Singapore road network ready for traffic mapping!")
    else:
        print("\n💥 Failed to download road network")