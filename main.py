"""
Entry point for the Team BEMG Geographic Database API.
Run this script to start the Flask development server.
"""

from server.app import app

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)
