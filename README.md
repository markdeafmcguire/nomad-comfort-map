
# Nomad Comfort Map — 200 Cities (Monthly Climate Normals)

This kit fetches **monthly climate normals** (average temperatures & precipitation) for 200 popular nomad/travel cities using **Meteostat**, and builds an interactive **Leaflet** map where you can filter by month, temperature range, and precipitation.

## What's included
- `cities_200.csv` — list of 200 cities (City, Country). The script will geocode to lat/lon.
- `build_dataset.py` — fetches monthly normals via Meteostat, saves CSV/JSON, and creates `comfort_map_dropdown.html`.
- (Output) `dataset_monthly_normals.csv` — °F temps + inches of precipitation, per month.
- (Output) `dataset_monthly_normals.json` — same data in JSON for the web map.
- (Output) `comfort_map_dropdown.html` — interactive map with month dropdown + sliders.

## Requirements
- Python 3.9+
- Internet connection (for geocoding & Meteostat API)
- Install dependencies:
  ```bash
  pip install meteostat geopy pandas jinja2 folium
  ```

## How to run
1. Ensure `cities_200.csv` has the cities you want. You can add columns `Lat` and `Lon` to skip geocoding for any city.
2. Run:
   ```bash
   python build_dataset.py
   ```
3. Open `comfort_map_dropdown.html` in your browser.

## Notes & Tips
- Geocoding uses Nominatim (OpenStreetMap). The script rate-limits 1 req/sec to respect usage policy. For big changes, consider pre-filling `Lat`/`Lon` yourself.
- Meteostat returns temperatures in °C — the script converts to **°F** and precipitation to **inches**.
- If some cities return incomplete data, try adjusting to a nearby major city or pre-fill coordinates.

## Customization
- Change default comfort range in `build_dataset.py` (`COMFORT_MIN_F`, `COMFORT_MAX_F`).
- Adjust filters or add humidity/sunshine if your Meteostat normals include them.
- You can swap station-based normals for gridded sources (WorldClim) if you prefer raster coverage.

Happy planning and smooth travels!
