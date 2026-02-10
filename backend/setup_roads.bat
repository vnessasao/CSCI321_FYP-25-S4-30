@echo off
echo Installing required Python packages for road geometry...
pip install osmnx geopandas shapely

echo.
echo Downloading Singapore road network from OpenStreetMap...
python download_roads.py

echo.
echo Setup complete! You can now start the Flask server.
pause