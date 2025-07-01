from app import app

# This file is used by Vercel as the entry point
# The app is imported from app.py

# For Vercel, we need to export the app
# For other platforms, we can run it directly
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)