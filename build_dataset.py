
# build_dataset.py
# Fetch monthly climate normals for a 200-city list and build an interactive comfort map.
#
# What it does:
# 1) Reads cities_200.csv (City, Country)
# 2) Geocodes each city -> latitude/longitude (geopy Nominatim)
# 3) Queries Meteostat monthly climate normals for the nearest station / point
# 4) Saves outputs:
#    - dataset_monthly_normals.csv (°F temps + precipitation)
#    - dataset_monthly_normals.json (for web)
#    - comfort_map_dropdown.html (interactive map with month selector + sliders)
#
# Requirements (install once):
#   pip install meteostat geopy pandas jinja2 folium
#
# Note: Respect Nominatim's usage policy. This script adds a small delay between geocoding requests.

import time
import json
import math
import pandas as pd
from pathlib import Path
from typing import Dict, Any
from meteostat import Point, Normals, Stations
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from jinja2 import Template
import folium

DATA_CSV = "cities_200.csv"
OUT_CSV = "dataset_monthly_normals.csv"
OUT_JSON = "dataset_monthly_normals.json"
OUT_HTML = "comfort_map_dropdown.html"

COMFORT_MIN_F = 50
COMFORT_MAX_F = 75

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def c_to_f(c):
    if c is None or (isinstance(c, float) and math.isnan(c)):
        return None
    return round((c * 9/5) + 32, 1)

def mm_to_in(mm):
    if mm is None or (isinstance(mm, float) and math.isnan(mm)):
        return None
    return round(mm / 25.4, 2)

def geocode_cities(df: pd.DataFrame) -> pd.DataFrame:
    geolocator = Nominatim(user_agent="nomad-comfort-map")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    lats, lons = [], []
    for _, row in df.iterrows():
        query = f"{row['City']}, {row['Country']}"
        location = geocode(query)
        if not location:
            # Try city only
            location = geocode(row['City'])
        if location:
            lats.append(location.latitude)
            lons.append(location.longitude)
        else:
            lats.append(None)
            lons.append(None)
    df['Lat'] = lats
    df['Lon'] = lons
    return df

def fetch_normals_for_point(lat: float, lon: float) -> Dict[str, Any]:
    # Meteostat normals: 1991–2020 (default) or 1981–2010 depending on API version
    # We'll use Point-based normals; falls back to nearest station grid
    point = Point(lat, lon)
    normals = Normals(point)
    # 'Normals' returns a DataFrame with index 1..12 months and columns:
    # tavg, tmin, tmax (°C), prcp (mm), wdir, wspd, pres, tsun, etc. (availability depends)
    df = normals.fetch()
    # Ensure we have 12 rows; if missing, return empty
    if df is None or df.empty or len(df.index) < 12:
        return {}
    # Build dictionaries
    tavg_f = {MONTHS[i-1]: c_to_f(df.loc[i, 'tavg']) if 'tavg' in df.columns else None for i in range(1,13)}
    tmin_f = {MONTHS[i-1]: c_to_f(df.loc[i, 'tmin']) if 'tmin' in df.columns else None for i in range(1,13)}
    tmax_f = {MONTHS[i-1]: c_to_f(df.loc[i, 'tmax']) if 'tmax' in df.columns else None for i in range(1,13)}
    prcp_in = {MONTHS[i-1]: mm_to_in(df.loc[i, 'prcp']) if 'prcp' in df.columns else None for i in range(1,13)}
    return {"tavg_f": tavg_f, "tmin_f": tmin_f, "tmax_f": tmax_f, "prcp_in": prcp_in}

def main():
    cities = pd.read_csv(DATA_CSV)
    if 'Lat' not in cities.columns or 'Lon' not in cities.columns:
        print("Geocoding cities (this may take several minutes; one request per second)...")
        cities = geocode_cities(cities)
        cities.to_csv(DATA_CSV, index=False)
        print("Geocoding complete and saved back to cities_200.csv")

    records = []
    json_payload = []
    for _, row in cities.iterrows():
        city = row['City']
        country = row['Country']
        lat, lon = row.get('Lat'), row.get('Lon')
        if pd.isna(lat) or pd.isna(lon):
            print(f"Skipping {city}, {country} (no coordinates)")
            continue
        try:
            normals = fetch_normals_for_point(lat, lon)
            if not normals:
                print(f"No normals returned for {city}, {country}")
                continue
            # Build a single CSV row with average temps
            out_row = {
                "City": city, "Country": country, "Lat": lat, "Lon": lon
            }
            # Use tavg_f; also include tmin/tmax/prcp for completeness
            for m in MONTHS:
                out_row[f"{m}_tavg_f"] = normals["tavg_f"][m]
                out_row[f"{m}_tmin_f"] = normals["tmin_f"][m]
                out_row[f"{m}_tmax_f"] = normals["tmax_f"][m]
                out_row[f"{m}_prcp_in"] = normals["prcp_in"][m]
            records.append(out_row)

            # JSON payload for the web map (tavg_f + prcp_in)
            json_payload.append({
                "city": city,
                "country": country,
                "lat": lat,
                "lon": lon,
                "tavg_f": normals["tavg_f"],
                "tmin_f": normals["tmin_f"],
                "tmax_f": normals["tmax_f"],
                "prcp_in": normals["prcp_in"],
            })
        except Exception as e:
            print(f"Error for {city}, {country}: {e}")
            continue

    if not records:
        print("No data collected. Please check your internet connection/API availability and try again.")
        return

    df = pd.DataFrame(records)
    df.to_csv(OUT_CSV, index=False)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(json_payload, f, ensure_ascii=False)

    # Build interactive HTML (Leaflet + dropdown + sliders)
    with open(OUT_JSON, "r", encoding="utf-8") as f:
        city_data = json.load(f)

    html_template = Template(r"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Nomad Comfort Map (Monthly Normals)</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
  <style>
    html, body { height: 100%; margin: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }
    #toolbar { padding: 10px; background: #f7f7f7; border-bottom: 1px solid #e2e2e2; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
    #map { height: calc(100% - 56px); width: 100%; }
    .pill { padding: 6px 10px; border: 1px solid #ddd; border-radius: 10px; background: #fff; }
    label { font-size: 14px; color: #333; }
    select, input { padding: 6px; }
  </style>
</head>
<body>
  <div id="toolbar">
    <div class="pill">
      <label for="month">Month:</label>
      <select id="month">
        {% for m in months %}<option value="{{m}}">{{m}}</option>{% endfor %}
      </select>
    </div>
    <div class="pill">
      <label for="minTemp">Min °F:</label>
      <input id="minTemp" type="number" value="{{ comfort_min }}" step="1" />
    </div>
    <div class="pill">
      <label for="maxTemp">Max °F:</label>
      <input id="maxTemp" type="number" value="{{ comfort_max }}" step="1" />
    </div>
    <div class="pill">
      <label for="maxPrcp">Max monthly precip (in):</label>
      <input id="maxPrcp" type="number" value="5" step="0.1" />
    </div>
    <div class="pill">
      <button id="apply">Apply Filters</button>
    </div>
  </div>
  <div id="map"></div>

  <script>
    const cityData = {{ city_data | tojson }};
    const months = {{ months | tojson }};

    const map = L.map('map').setView([20, 0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    let markers = [];

    function update() {
      const m = document.getElementById('month').value;
      const tmin = parseFloat(document.getElementById('minTemp').value);
      const tmax = parseFloat(document.getElementById('maxTemp').value);
      const maxP = parseFloat(document.getElementById('maxPrcp').value);

      // Clear existing markers
      markers.forEach(marker => map.removeLayer(marker));
      markers = [];

      cityData.forEach(c => {
        const t = c.tavg_f[m];
        const p = c.prcp_in[m];
        if (t == null) return;
        const tempOk = (t >= tmin && t <= tmax);
        const prcpOk = (p == null) ? true : (p <= maxP);

        if (tempOk && prcpOk) {
          const marker = L.marker([c.lat, c.lon]).addTo(map);
          const details = `
            <b>${c.city}, ${c.country}</b><br>
            <b>${m}</b><br>
            Avg: ${t} °F<br>
            Min/Max: ${c.tmin_f[m]} / ${c.tmax_f[m]} °F<br>
            Precip: ${p ?? "n/a"} in
          `;
          marker.bindPopup(details);
          markers.push(marker);
        }
      });
    }

    document.getElementById('apply').addEventListener('click', update);
    document.getElementById('month').addEventListener('change', update);

    // Initialize
    update();
  </script>
</body>
</html>
    """)

    html = html_template.render(
        city_data=city_data,
        months=MONTHS,
        comfort_min=COMFORT_MIN_F,
        comfort_max=COMFORT_MAX_F
    )

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Done.\n- CSV: {OUT_CSV}\n- JSON: {OUT_JSON}\n- Map: {OUT_HTML}")
    print("Tip: open comfort_map_dropdown.html in your browser.")

if __name__ == "__main__":
    main()
