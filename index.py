from app import app
import os

# This file is used as the entry point for various platforms
# The app is imported from app.py

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)