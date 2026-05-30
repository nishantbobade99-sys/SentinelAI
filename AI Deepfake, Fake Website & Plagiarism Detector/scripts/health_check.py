import requests
import sys

def run_health_check():
    url = "http://localhost:5000/health"
    print(f"Checking health at {url}...")
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        print("Service is UP.")
        print(f"Status: {data}")
        sys.exit(0)
    except Exception as e:
        print(f"Health check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_health_check()
