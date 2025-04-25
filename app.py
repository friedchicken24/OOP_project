import os
import logging
from flask import Flask

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
# 👇 chỉ định thư mục hiện tại chứa template + static file
app = Flask(__name__, template_folder='.', static_folder="static")

app.secret_key = os.environ.get("SESSION_SECRET", "memory_match_secret_key")

# Initialize the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)