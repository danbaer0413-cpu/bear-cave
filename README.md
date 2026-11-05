# Bear Cave Election Database

Public copy of the Bear Cave election dashboard: live 2026 needles, Senate and House seat charts, state, county and congressional-district maps, results back to 1976, state trends, county and district demographics, and the 2026 forecast check.

Open it at the GitHub Pages address for this repo. On a phone, use "Add to Home Screen" to install it like an app.

- `index.html`, `dash.js`: the page and the small runtime that loads the data files and draws the charts.
- `data/`: the datasets (CSV and JSON). `data/manifest.json` lists them.
- `tools/refresh.py`: rebuilds the live needle and seat files from the `election-needle` repo; `.github/workflows/refresh.yml` runs it on a schedule.

Sources: MIT Election Data and Science Lab, OpenElections, FiveThirtyEight election-results, state election offices, U.S. Census Bureau (ACS, decennial, TIGER), USDA ERS, Redistricting Data Hub, nickoneill/districts, NBC News/AP (2026, unofficial).
