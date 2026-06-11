
import os
import json
from fastapi.testclient import TestClient

# Mock the environment
os.environ["PROXY_PREFIX"] = "/user/test/proxy/4050"
os.environ["SECONDMATE_STATIC_DIR"] = os.path.join(os.getcwd(), "secondmate/static")

# Import the app after setting env
try:
    from secondmate.main import app
    
    client = TestClient(app)
    
    # We need to make sure index.html exists. It should be there after build.
    if not os.path.exists(os.path.join(os.getcwd(), "secondmate/static/index.html")):
        os.makedirs("secondmate/static", exist_ok=True)
        with open("secondmate/static/index.html", "w") as f:
            f.write("<html><head></head><body></body></html>")
        
    response = client.get("/some/random/path")
    
    if response.status_code == 200:
        content = response.text
        # New expected format is JSON serialized
        expected = 'window.SECONDMATE_CONFIG = {"apiBaseUrl": "/user/test/proxy/4050/api"};'
        if expected in content:
            print("SUCCESS: Config injection verified.")
        else:
            print("FAILURE: Config not found in response.")
            print("Content start:", content[:500])
            exit(1)
    else:
        print(f"FAILURE: Status code {response.status_code}")
        print(response.text)
        exit(1)

except Exception as e:
    print(f"Error: {e}")
    exit(1)
