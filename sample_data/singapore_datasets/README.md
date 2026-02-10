# Singapore Traffic Dataset Collection

This folder contains 5 sets of sample traffic data covering different regions of Singapore. Each dataset includes a road network (GeoJSON) and corresponding GPS traces (CSV).

## Naming Convention

```
{number}_{area_name}_roads.geojson  →  Road network definition
{number}_{area_name}_gps.csv        →  Vehicle GPS traces
```

## Dataset Overview

| # | Area | Files | Description | Peak Traffic Time |
|---|------|-------|-------------|-------------------|
| 01 | CBD Marina Bay | `01_cbd_marina_bay_roads.geojson` + `01_cbd_marina_bay_gps.csv` | Financial district | 08:00 - Morning rush |
| 02 | Orchard Newton | `02_orchard_newton_roads.geojson` + `02_orchard_newton_gps.csv` | Shopping district | 10:00 - Weekend shopping |
| 03 | Jurong West | `03_jurong_west_roads.geojson` + `03_jurong_west_gps.csv` | Industrial area | 07:00 - Factory shifts |
| 04 | Tampines East | `04_tampines_east_roads.geojson` + `04_tampines_east_gps.csv` | Residential east | 17:00 - Evening commute |
| 05 | Woodlands North | `05_woodlands_north_roads.geojson` + `05_woodlands_north_gps.csv` | Malaysia border | 06:00 - Cross-border rush |

---

## Dataset 01: CBD Marina Bay

**Location:** Central Business District and Marina Bay
**Coordinates Center:** 1.2840°N, 103.8510°E

### Roads Included:
- Raffles Place (Primary)
- Shenton Way (Primary)
- Robinson Road (Primary)
- Marina Boulevard (Primary)
- Marina Coastal Expressway (Expressway)
- Bayfront Avenue, Collyer Quay, etc.

### Traffic Pattern:
- **08:00-08:06:** Normal traffic (40-50 km/h)
- **08:06-08:12:** Building congestion (15-25 km/h)
- **08:12-08:18:** Heavy congestion (3-8 km/h)
- **08:18-08:26:** Severe jam (0.1-2 km/h)

### Bottleneck Expected:
Shenton Way → Raffles Place junction (main CBD entry point)

---

## Dataset 02: Orchard Newton

**Location:** Orchard Road shopping belt and Newton
**Coordinates Center:** 1.3050°N, 103.8310°E

### Roads Included:
- Orchard Road (Primary) - Main shopping street
- Scotts Road (Secondary)
- Tanglin Road (Primary)
- Newton Road (Primary)
- Bukit Timah Road (Primary)
- Somerset Road, Paterson Road, etc.

### Traffic Pattern:
- **10:00-10:06:** Normal weekend traffic (35-40 km/h)
- **10:06-10:12:** Shopping crowd builds (15-25 km/h)
- **10:12-10:18:** Congestion peak (5-12 km/h)
- **10:18-10:24:** Severe congestion (0.1-3 km/h)

### Bottleneck Expected:
Orchard Road central (near ION/Takashimaya)

---

## Dataset 03: Jurong West

**Location:** Jurong industrial and residential area
**Coordinates Center:** 1.3350°N, 103.7400°E

### Roads Included:
- Jurong Town Hall Road (Primary)
- Boon Lay Way (Primary)
- Pioneer Road (Primary)
- Tuas Road (Primary)
- Ayer Rajah Expressway (Expressway)
- Yuan Ching Road, Corporation Road, etc.

### Traffic Pattern:
- **07:00-07:06:** Factory shift start (40-50 km/h)
- **07:06-07:12:** Industrial area congestion (15-30 km/h)
- **07:12-07:18:** Heavy traffic (5-15 km/h)
- **07:18-07:26:** Jam near industrial parks (0.1-4 km/h)

### Bottleneck Expected:
Boon Lay Way → Jurong Town Hall Road junction

---

## Dataset 04: Tampines East

**Location:** Tampines residential and Bedok area
**Coordinates Center:** 1.3530°N, 103.9450°E

### Roads Included:
- Tampines Avenue 1 (Primary)
- Tampines Avenue 4 (Primary)
- Bedok North Road (Primary)
- Upper Changi Road (Primary)
- Pan Island Expressway (Expressway)
- Simei Avenue, Pasir Ris Drive, etc.

### Traffic Pattern:
- **17:00-17:06:** Evening commute starts (40-50 km/h)
- **17:06-17:12:** Residential area fills (18-28 km/h)
- **17:12-17:18:** Peak congestion (5-12 km/h)
- **17:18-17:26:** Heavy jam (0.1-3 km/h)

### Bottleneck Expected:
Tampines Avenue 1 → Tampines Central junction

---

## Dataset 05: Woodlands North

**Location:** Woodlands border area (Malaysia Causeway)
**Coordinates Center:** 1.4390°N, 103.7850°E

### Roads Included:
- Woodlands Avenue 1 (Primary)
- Woodlands Causeway (Primary) - To Malaysia
- Sembawang Road (Primary)
- Yishun Avenue 1 (Primary)
- Seletar Expressway (Expressway)
- Bukit Timah Expressway (Expressway)
- Admiralty Road, Marsiling Road, etc.

### Traffic Pattern:
- **06:00-06:06:** Early cross-border traffic (35-50 km/h)
- **06:06-06:12:** Causeway queue builds (10-20 km/h)
- **06:12-06:18:** Heavy causeway jam (3-8 km/h)
- **06:18-06:26:** Severe border jam (0.1-2 km/h)

### Bottleneck Expected:
Woodlands Causeway entrance (checkpoint area)

---

## How to Use

1. **Upload Road Network:** Upload the `_roads.geojson` file first
2. **Upload GPS Data:** Upload the matching `_gps.csv` file
3. **Run Model:** Execute the bottleneck analysis
4. **View Results:** See animated flow lines showing congestion spread

## File Matching Guide

| Road Network File | GPS Data File |
|-------------------|---------------|
| `01_cbd_marina_bay_roads.geojson` | `01_cbd_marina_bay_gps.csv` |
| `02_orchard_newton_roads.geojson` | `02_orchard_newton_gps.csv` |
| `03_jurong_west_roads.geojson` | `03_jurong_west_gps.csv` |
| `04_tampines_east_roads.geojson` | `04_tampines_east_gps.csv` |
| `05_woodlands_north_roads.geojson` | `05_woodlands_north_gps.csv` |

## Data Format

### GeoJSON (Roads)
```json
{
  "type": "Feature",
  "properties": {
    "road_id": "unique_road_id",
    "road_name": "Road Name",
    "highway": "primary|secondary|tertiary|expressway",
    "area": "District Name"
  },
  "geometry": {
    "type": "LineString",
    "coordinates": [[lon, lat], [lon, lat], ...]
  }
}
```

### CSV (GPS)
```
vehicle_id,timestamp,latitude,longitude,speed,heading
V001,2025-01-15T08:00:00Z,1.3048,103.8281,45.5,90
```

- **vehicle_id:** Unique vehicle identifier
- **timestamp:** ISO 8601 format
- **latitude/longitude:** WGS84 coordinates
- **speed:** km/h (lower = more congestion)
- **heading:** Degrees (0=North, 90=East, 180=South, 270=West)
