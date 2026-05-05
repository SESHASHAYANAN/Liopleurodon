import requests

url = "http://localhost:8000/api/jobs"
params = {
    "location": "india",
    "experience_level": "junior"
}

try:
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        print(f"Total found for india & junior: {data.get('total')}")
    else:
        print(f"Error {response.status_code}: {response.text}")
except Exception as e:
    print(f"Failed to connect: {e}")

params2 = {
    "company_type": "vc_backed",
    "vc_backer": "Y Combinator",
    "location": "india"
}
try:
    response = requests.get(url, params=params2)
    if response.status_code == 200:
        data = response.json()
        print(f"Total found for YC & india: {data.get('total')}")
except Exception as e:
    pass

params3 = {
    "company_type": "stealth",
    "location": "india"
}
try:
    response = requests.get(url, params=params3)
    if response.status_code == 200:
        data = response.json()
        print(f"Total found for stealth & india: {data.get('total')}")
except Exception as e:
    pass
