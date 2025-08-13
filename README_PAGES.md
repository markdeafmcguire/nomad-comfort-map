# Nomad Comfort Map (GitHub Pages)

This is a **static**, JavaScript-only map which can be hosted on **GitHub Pages** with no backend.

## Use it now (demo)
- Open `index.html` (it will load `data/demo_dataset.json`).

## Load your full dataset
- Place your file at `data/dataset_monthly_normals.json` (same shape as the demo).
- Or click **Load dataset (.json)** in the top bar and select your JSON file.

## Deploy to GitHub Pages
1. Create a new repo (e.g., `nomad-comfort-map`).
2. Upload the contents of the `site/` folder:
   - `index.html`
   - `data/demo_dataset.json` (optional)
   - (Optional) `data/dataset_monthly_normals.json` – your real 200-city dataset
3. Commit & push.
4. In GitHub → **Settings** → **Pages**:
   - Source: **Deploy from a branch**
   - Branch: **main**, folder: **/** (root)
5. Wait for Pages to build, then visit your site URL.

## Where to get the 200-city dataset
- Use `build_dataset.py` in this kit to fetch **Meteostat** monthly climate normals and write `dataset_monthly_normals.json`.
- Then upload that file to the `data/` folder or load it dynamically via the upload button.

### JSON format (example entry)
```json
[
  {
    "city": "Lisbon",
    "country": "Portugal",
    "lat": 38.72,
    "lon": -9.14,
    "tavg_f": {"Jan": 57, "...": 0},
    "tmin_f": {"Jan": 48, "...": 0},
    "tmax_f": {"Jan": 60, "...": 0},
    "prcp_in": {"Jan": 3.1, "...": 0}
  }
]
```

## Notes
- Everything runs in the browser. Large datasets (thousands of cities) may benefit from marker clustering or WebGL layers.
- You can customize the look & behavior by editing `index.html`.
