# Real-Time Traffic Congestion Map

A comprehensive real-time traffic congestion map feature using the LTA Data Mall API to provide live traffic conditions across Singapore.

## Features

### Backend (Flask API)
- **LTA API Integration**: Fetches real-time traffic speed data from Singapore's Land Transport Authority
- **Smart Congestion Classification**: Automatically categorizes traffic into Normal, Moderate, and Heavy congestion levels
- **GeoJSON Transformation**: Converts LTA data into standard GeoJSON format for frontend consumption
- **Comprehensive Error Handling**: Handles API failures, timeouts, and malformed responses gracefully
- **Health Check Endpoint**: Monitor API service status

### Frontend (React + Leaflet)
- **Interactive Map**: Full-featured map with zoom controls and Singapore boundaries
- **Real-Time Visualization**: Color-coded road segments (Green=Normal, Yellow=Moderate, Red=Heavy)
- **Auto-Refresh**: Configurable 60-second automatic data refresh
- **Detailed Tooltips**: Hover over road segments to see speed and congestion information
- **Statistics Dashboard**: Live statistics showing congestion distribution
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## API Endpoints

### GET `/api/traffic-map`
Fetches real-time traffic data and returns GeoJSON format.

**Headers Required:**
```
AccountKey: YOUR_LTA_API_KEY
```

**Response Format:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[lng, lat], [lng, lat], ...]
      },
      "properties": {
        "road_name": "Marina Coastal Expressway",
        "speed": 45.5,
        "min_speed": 40,
        "max_speed": 51,
        "congestion": "normal",
        "speed_band": "40-60"
      }
    }
  ],
  "metadata": {
    "timestamp": "2025-12-11T10:30:00Z",
    "total_segments": 1234
  }
}
```

### GET `/api/traffic-map/health`
Health check endpoint for monitoring service status.

## Congestion Classification Logic

The system uses average speed to determine congestion levels:

```python
def classify_congestion(speed):
    if speed < 20:
        return 'heavy'    # Red - Severe congestion
    elif speed < 40:
        return 'moderate' # Yellow/Orange - Moderate congestion  
    else:
        return 'normal'   # Green - Free flowing traffic
```

## Setup Instructions

### Backend Setup

1. **Install Dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

2. **Register Flask Blueprint** (already configured):
```python
# In app.py
from routes.traffic import traffic_bp
app.register_blueprint(traffic_bp)
```

3. **Start Flask Server**:
```bash
python app.py
```

### Frontend Setup

1. **Install Node Dependencies** (already configured):
```bash
npm install
```

2. **Start Development Server**:
```bash
npm run dev
```

### LTA API Key Configuration

1. **Get API Key**: Visit [LTA DataMall](https://datamall.lta.gov.sg/content/datamall/en/request-for-api.html)
2. **Configure in App**: Enter your API key in the frontend interface when prompted
3. **API Limits**: LTA API allows 5,000 calls per day for registered users

## Usage Guide

### Accessing the Traffic Map

1. Navigate to `/map` in your application
2. Enter your LTA DataMall API key when prompted
3. The map will automatically load and start refreshing every 60 seconds

### Map Controls

- **Pan**: Click and drag to move around the map
- **Zoom**: Use mouse wheel or zoom controls
- **Road Information**: Hover over any road segment for details
- **Auto-Refresh**: Toggle automatic updates on/off
- **Manual Refresh**: Click "Refresh" button for immediate update

### Understanding the Data

- **Green Roads**: Normal traffic flow (≥40 km/h)
- **Yellow Roads**: Moderate congestion (20-39 km/h)  
- **Red Roads**: Heavy congestion (<20 km/h)
- **Statistics Bar**: Shows distribution of congestion levels
- **Last Updated**: Timestamp of the most recent data fetch

## Error Handling

### Common Error Scenarios

1. **Invalid API Key**: 
   - Error: "Unauthorized" or "Invalid LTA API key"
   - Solution: Check your API key and registration status

2. **API Rate Limit**: 
   - Error: "Forbidden" or rate limit messages
   - Solution: Wait for rate limit reset or upgrade API plan

3. **Network Issues**:
   - Error: "Network Error" or "Timeout"
   - Solution: Check internet connection and LTA service status

4. **Malformed Data**:
   - Error: "Invalid data format"
   - Solution: API may be temporarily returning unexpected data format

### Backend Error Responses

```json
{
  "error": "Error Type",
  "message": "Human-readable error message",
  "details": "Additional technical details (if available)"
}
```

## Performance Considerations

### Backend Optimization
- **Caching**: Consider implementing Redis caching for frequently requested data
- **Rate Limiting**: Implement rate limiting to prevent API abuse
- **Async Processing**: Use async requests for better concurrent handling

### Frontend Optimization  
- **Data Debouncing**: Prevent excessive API calls during user interactions
- **Map Bounds**: Only fetch data for visible map area (future enhancement)
- **Progressive Loading**: Load critical map features first, then details

## Monitoring and Maintenance

### Health Monitoring
```bash
# Check API health
curl http://localhost:5000/api/traffic-map/health

# Expected response
{
  "status": "healthy",
  "service": "Traffic Map API",
  "timestamp": "2025-12-11T10:30:00Z",
  "endpoints": {
    "traffic_map": "/api/traffic-map"
  }
}
```

### Logs and Debugging
- Backend logs all API calls and errors with timestamps
- Frontend console logs network requests and data processing
- Monitor LTA API response times and error rates

## Future Enhancements

### Planned Features
1. **Historical Data**: Store and display traffic patterns over time
2. **Predictive Analytics**: Use machine learning to forecast congestion  
3. **Route Planning**: Integrate with routing algorithms for optimal paths
4. **Incident Correlation**: Link traffic data with incident reports
5. **Mobile App**: Native mobile application with push notifications
6. **Custom Alerts**: Set up notifications for specific road conditions

### Technical Improvements
1. **WebSocket Integration**: Real-time data streaming instead of polling
2. **Map Clustering**: Aggregate nearby road segments for better performance
3. **Offline Mode**: Cache recent data for offline viewing
4. **Multi-Source Data**: Integrate additional traffic data sources
5. **Advanced Filtering**: Filter by road type, congestion level, time of day

## API Documentation

### LTA DataMall Integration

The system integrates with Singapore's official traffic data source:

**Base URL**: `https://api.data.gov.sg/v1/transport/traffic-speed-bands`

**Authentication**: Account Key header required

**Data Format**: GeoJSON with traffic speed information

**Update Frequency**: Every 1-2 minutes from LTA

**Coverage**: Major expressways and arterial roads in Singapore

## Troubleshooting

### Map Not Loading
1. Check browser console for JavaScript errors
2. Verify API key is correctly entered
3. Ensure backend server is running on correct port
4. Check network connectivity to LTA API

### No Traffic Data Displayed
1. Verify LTA API is returning data (check network tab)
2. Check if API key has sufficient quota remaining
3. Ensure GeoJSON transformation is working correctly
4. Verify map bounds include Singapore

### Performance Issues
1. Reduce refresh frequency if needed
2. Check for memory leaks in map layer management
3. Monitor API response times
4. Consider implementing data compression

## Support and Maintenance

For issues or enhancements:
1. Check application logs for error messages
2. Verify LTA API service status
3. Test with fresh API key if authentication fails
4. Monitor system resources during peak usage

## License and Attribution

- **LTA Data**: Contains data from Land Transport Authority Singapore
- **Map Tiles**: © OpenStreetMap contributors  
- **Leaflet**: Open-source mapping library
- **React**: MIT License