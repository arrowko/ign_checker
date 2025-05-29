import requests
from requests.exceptions import RequestException
import time

def robust_get(url, retries=3, delay=10):
    for i in range(retries):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 403:
                print("🚫 Rate limited (403), waiting 60s...")
                time.sleep(60)
                continue
            return response
        except RequestException as e:
            print(f"⚠️ Network error (try {i+1}/{retries}): {e}")
            time.sleep(delay)
    print("❌ Failed after retries.")
    return None
