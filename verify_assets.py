
import os
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Mock the environment
os.environ["PROXY_PREFIX"] = "/user/test/proxy/4050"
os.environ["SECONDMATE_STATIC_DIR"] = "/workspaces/secondmate/secondmate/static"

try:
    from secondmate.main import app
    
    client = TestClient(app)
    
    # 1. Verify index.html content for relative paths
    if not os.path.exists("/workspaces/secondmate/secondmate/static/index.html"):
        print("Build not finished or index.html missing.")
        exit(1)
        
    with open("/workspaces/secondmate/secondmate/static/index.html", "r") as f:
        content = f.read()
        if 'src="./assets/' in content or 'src="assets/' in content:
             print("SUCCESS: index.html uses relative paths for scripts.")
        else:
             # It might use 'crossentropy src="/assets/' if base not applied correctly
             print("FAILURE: index.html might still use absolute paths.")
             print("Content snippet:", content[:300])

    # 2. Verify vite.svg serving
    # vite.svg is likely in public/vite.svg -> copied to secondmate/static/vite.svg
    # Requesting /vite.svg should return the SVG file, NOT index.html
    # But wait, did I check if vite.svg is in static dir?
    if not os.path.exists("/workspaces/secondmate/secondmate/static/vite.svg"):
         print("WARNING: vite.svg not found in static dir. Using another file check?")
    else:
        response = client.get("/vite.svg")
        if response.status_code == 200 and "svg" in response.headers.get("content-type", ""):
             print("SUCCESS: /vite.svg served correctly.")
        else:
             print(f"FAILURE: /vite.svg returned {response.status_code} type {response.headers.get('content-type')}")

    # 3. Verify fallback to index.html
    response = client.get("/some/random/route")
    if response.status_code == 200 and "<html" in response.text:
         print("SUCCESS: SPA fallback working.")
    else:
         print("FAILURE: SPA fallback not working.")

except Exception as e:
    print(f"Error: {e}")
