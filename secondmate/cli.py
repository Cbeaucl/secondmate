import argparse
import uvicorn
import os

def main():
    parser = argparse.ArgumentParser(description="Run the SecondMate application.")
    parser.add_argument("--port", type=int, default=4050, help="Port to run the server on (default: 4050)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    # Set the static directory path relative to this file if not set
    # This allows the package to find its static assets
    package_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(package_dir, "static")
    os.environ["SECONDMATE_STATIC_DIR"] = static_dir

    print(f"Starting SecondMate on http://{args.host}:{args.port}")
    if args.reload:
        uvicorn.run("secondmate.main:app", host=args.host, port=args.port, reload=True)
    else:
        uvicorn.run("secondmate.main:app", host=args.host, port=args.port)

if __name__ == "__main__":
    main()
