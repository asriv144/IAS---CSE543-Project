import requests
import json
import time
import sys

# Wait for server to start (longer wait)
print("Waiting for server to start...")
for i in range(10):
    try:
        r = requests.get("http://localhost:8000/health", timeout=1)
        if r.status_code == 200:
            print("Server is ready!\n")
            break
    except:
        time.sleep(1)
        print(".", end="", flush=True)
else:
    print("\n\nERROR: Server is not running!")
    print("Please start the server first:")
    print("  python start_api.py")
    print("  OR")
    print("  python src/api.py")
    sys.exit(1)

base_url = "http://localhost:8000"

print("Testing API...")
print("=" * 50)

# Test health endpoint
try:
    r = requests.get(f"{base_url}/health")
    print(f"Health Check: {r.status_code}")
    print(f"Response: {r.json()}\n")
except Exception as e:
    print(f"Health check failed: {e}\n")

# Test single URL prediction
test_urls = [
    "https://google.com",  # Legitimate
    "https://bit.ly/xyz",  # Suspicious (shortener)
    "http://192.168.0.1/login",  # Suspicious (IP + login)
]

print("Testing single URL predictions:")
print("-" * 50)
for url in test_urls:
    try:
        r = requests.post(f"{base_url}/predict", json={"url": url})
        if r.status_code == 200:
            result = r.json()
            print(f"\nURL: {url}")
            print(f"  Is Phishing: {result['is_phishing']}")
            print(f"  Probability: {result['probability']:.4f}")
            print(f"  Confidence: {result['confidence']}")
        else:
            print(f"Error for {url}: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Error for {url}: {e}")

# Test batch prediction
print("\n\nTesting batch prediction:")
print("-" * 50)
try:
    r = requests.post(f"{base_url}/predict", json={"urls": test_urls})
    if r.status_code == 200:
        result = r.json()
        print(f"Received {len(result['predictions'])} predictions:")
        for pred in result['predictions']:
            print(f"\n  URL: {pred['url']}")
            print(f"    Is Phishing: {pred['is_phishing']}")
            print(f"    Probability: {pred['probability']:.4f}")
            print(f"    Confidence: {pred['confidence']}")
    else:
        print(f"Error: {r.status_code} - {r.text}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 50)
print("Testing complete!")

