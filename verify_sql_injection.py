
import sys
from fastapi.testclient import TestClient
from secondmate.main import app, get_spark_session
from unittest.mock import MagicMock
import urllib.parse

# Mock Spark Session
mock_spark = MagicMock()
mock_spark.sql.return_value.collect.return_value = []

def override_get_spark_session():
    return mock_spark

app.dependency_overrides[get_spark_session] = override_get_spark_session

client = TestClient(app)

def test_get_namespaces_injection():
    # Try a malicious payload
    malicious_payload = "valid_name; DROP TABLE foo;"
    response = client.get(f"/api/catalogs/{malicious_payload}/namespaces")

    print(f"Payload: {malicious_payload}")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 400:
        print("SUCCESS: Malicious payload rejected.")
        return True
    else:
        print("FAILURE: Malicious payload accepted!")
        return False

def test_get_namespaces_newline():
    # Try a payload with newline (which passed before hardening)
    # Use urllib quote to encode newline
    raw_payload = "valid_name\n"
    encoded_payload = urllib.parse.quote(raw_payload)

    response = client.get(f"/api/catalogs/{encoded_payload}/namespaces")

    print(f"Payload: {encoded_payload} (decoded as {repr(raw_payload)})")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 400:
        print("SUCCESS: Newline payload rejected.")
        return True
    else:
        print(f"FAILURE: Newline payload accepted! Response: {response.json()}")
        return False

def test_get_namespaces_valid():
    valid_payload = "valid_catalog"
    response = client.get(f"/api/catalogs/{valid_payload}/namespaces")

    print(f"Payload: {valid_payload}")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print("SUCCESS: Valid payload accepted.")
        return True
    else:
        print(f"FAILURE: Valid payload rejected! {response.json()}")
        return False

if __name__ == "__main__":
    results = [
        test_get_namespaces_injection(),
        test_get_namespaces_newline(),
        test_get_namespaces_valid()
    ]

    if all(results):
        print("\nALL TESTS PASSED")
        sys.exit(0)
    else:
        print("\nSOME TESTS FAILED")
        sys.exit(1)
