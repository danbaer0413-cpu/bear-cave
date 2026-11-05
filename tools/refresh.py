"""Refresh the live files from the needle repo and stamp the data manifest. Run by .github/workflows/refresh.yml.
usage: python tools/refresh.py <path to election-needle checkout>"""
import datetime, json, subprocess, sys
needle = sys.argv[1]
subprocess.run([sys.executable, 'tools/build_needles.py', needle, 'data'], check=True)
subprocess.run([sys.executable, 'tools/build_seats.py', needle, 'data'], check=True)
m = json.load(open('data/manifest.json'))
m['updated'] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
json.dump(m, open('data/manifest.json', 'w'), indent=1)
print('refreshed', m['updated'])
