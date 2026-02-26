import http.server
import socketserver
import threading
import time
import sys
import os
from playwright.sync_api import sync_playwright, expect

PORT = 5174
DIRECTORY = "secondmate/static"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    # Silencing logs for cleaner output
    def log_message(self, format, *args):
        return

def serve():
    # Use allow_reuse_address to avoid "Address already in use" errors
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

def test_workspace_initial_state():
    if not os.path.exists(DIRECTORY):
        print(f"Error: Directory {DIRECTORY} not found. Please build the frontend first.")
        sys.exit(1)

    # Start server in a background thread
    server_thread = threading.Thread(target=serve, daemon=True)
    server_thread.start()
    time.sleep(2) # Wait for server to start

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(f"http://localhost:{PORT}")

            # 1. Verify the "Run" button is present
            # The button contains a Play icon and "Run" or "Running..."
            run_button = page.get_by_role("button", name="Run")
            expect(run_button).to_be_visible()

            # 2. Verify the welcome message is present
            welcome_header = page.get_by_text("🫡Welcome Aboard Matey!")
            expect(welcome_header).to_be_visible()

            welcome_main = page.get_by_text("Welcome To Secondmate! Get started by entering your query above.")
            expect(welcome_main).to_be_visible()

            # 3. Verify Query Results header is present
            expect(page.get_by_text("Query Results")).to_be_visible()

            print("SUCCESS: Workspace initial state verified.")

        except Exception as e:
            print(f"FAILURE: {e}")
            page.screenshot(path="tests/e2e/failure_screenshot.png")
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    test_workspace_initial_state()
    sys.exit(0)
