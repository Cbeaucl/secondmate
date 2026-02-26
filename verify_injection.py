
import os
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
        print("Build not finished or index.html missing.")
        exit(1)
        
    response = client.get("/some/random/path")
    
    if response.status_code == 200:
        content = response.text
        expected = 'window.SECONDMATE_CONFIG = { apiBaseUrl: "/user/test/proxy/4050/api" };'
        if expected in content:
            print("SUCCESS: Config injection verified.")
        else:
            print("FAILURE: Config not found in response.")
            print("Content start:", content[:500])
    else:
        print(f"FAILURE: Status code {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"Error: {e}")
