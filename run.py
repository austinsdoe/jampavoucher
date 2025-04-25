import os
from app import create_app
from dotenv import load_dotenv

load_dotenv()

# Use FLASK_ENV to determine the environment
env = os.getenv("FLASK_ENV", "development")
debug = env == "development"

app = create_app()

if env == "development":
    app.debug = True
else:
    app.debug = False

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
    app.run(debug=debug, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
