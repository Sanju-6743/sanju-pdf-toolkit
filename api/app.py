from flask import Flask, render_template_string, jsonify, request
import os

app = Flask(__name__)

# HTML template for the main page
MAIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Toolkit - Live & Working!</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            max-width: 900px;
            margin: 20px;
            background: rgba(255, 255, 255, 0.1);
            padding: 40px;
            border-radius: 20px;
            backdrop-filter: blur(15px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        .success-icon { font-size: 4em; margin-bottom: 20px; }
        .status-badge {
            display: inline-block;
            background: #4CAF50;
            padding: 10px 20px;
            border-radius: 25px;
            font-weight: bold;
            margin: 10px 0;
        }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .feature {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 15px;
            border-left: 4px solid #4CAF50;
        }
        .btn {
            display: inline-block;
            padding: 15px 30px;
            background: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 25px;
            font-weight: bold;
            margin: 10px;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
        }
        .btn:hover { background: #45a049; transform: translateY(-2px); }
        .btn.secondary { background: #2196F3; }
        .btn.secondary:hover { background: #1976D2; }
        .api-demo {
            background: rgba(0, 0, 0, 0.2);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: left;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="success-icon">🎉</div>
        <h1>PDF Toolkit is Live!</h1>
        <div class="status-badge">✅ DEPLOYMENT SUCCESSFUL</div>
        
        <p style="font-size: 1.2em; margin: 20px 0;">
            Your PDF processing application is now running on Vercel!
        </p>
        
        <div class="feature-grid">
            <div class="feature">
                <h3>🚀 Serverless Ready</h3>
                <p>Running on Vercel's edge network with global CDN</p>
            </div>
            <div class="feature">
                <h3>⚡ Fast & Scalable</h3>
                <p>Auto-scaling serverless functions for optimal performance</p>
            </div>
            <div class="feature">
                <h3>🔧 API Endpoints</h3>
                <p>RESTful API ready for PDF processing operations</p>
            </div>
            <div class="feature">
                <h3>📱 Responsive UI</h3>
                <p>Mobile-friendly interface for all devices</p>
            </div>
        </div>
        
        <div class="api-demo">
            <h3>🔗 API Endpoints Available:</h3>
            <ul>
                <li><strong>GET /</strong> - Main application page</li>
                <li><strong>GET /health</strong> - Health check endpoint</li>
                <li><strong>GET /api/status</strong> - API status information</li>
                <li><strong>POST /api/upload</strong> - File upload endpoint (coming soon)</li>
            </ul>
        </div>
        
        <div style="margin-top: 30px;">
            <button onclick="testAPI()" class="btn">Test API</button>
            <button onclick="checkHealth()" class="btn secondary">Health Check</button>
        </div>
        
        <div id="result" style="margin-top: 20px; padding: 15px; background: rgba(0,0,0,0.2); border-radius: 10px; display: none;"></div>
        
        <div style="margin-top: 30px; font-size: 0.9em; opacity: 0.8;">
            <p>Deployed on: <span id="timestamp"></span></p>
            <p>Platform: Vercel Serverless | Status: Active</p>
        </div>
    </div>
    
    <script>
        document.getElementById('timestamp').textContent = new Date().toLocaleString();
        
        async function testAPI() {
            const result = document.getElementById('result');
            result.style.display = 'block';
            result.innerHTML = '🔄 Testing API...';
            
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                result.innerHTML = `
                    <h4>✅ API Test Successful!</h4>
                    <pre>${JSON.stringify(data, null, 2)}</pre>
                `;
            } catch (error) {
                result.innerHTML = `<h4>❌ API Test Failed:</h4><p>${error.message}</p>`;
            }
        }
        
        async function checkHealth() {
            const result = document.getElementById('result');
            result.style.display = 'block';
            result.innerHTML = '🔄 Checking health...';
            
            try {
                const response = await fetch('/health');
                const data = await response.json();
                result.innerHTML = `
                    <h4>✅ Health Check Passed!</h4>
                    <pre>${JSON.stringify(data, null, 2)}</pre>
                `;
            } catch (error) {
                result.innerHTML = `<h4>❌ Health Check Failed:</h4><p>${error.message}</p>`;
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(MAIN_TEMPLATE)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'message': 'PDF Toolkit is running successfully!',
        'platform': 'Vercel Serverless',
        'timestamp': str(os.environ.get('VERCEL_REGION', 'unknown')),
        'version': '1.0.0'
    })

@app.route('/api/status')
def api_status():
    return jsonify({
        'api': 'PDF Toolkit API',
        'status': 'active',
        'endpoints': {
            'health': '/health',
            'status': '/api/status',
            'upload': '/api/upload (coming soon)'
        },
        'deployment': {
            'platform': 'Vercel',
            'region': os.environ.get('VERCEL_REGION', 'unknown'),
            'url': os.environ.get('VERCEL_URL', 'localhost')
        }
    })

@app.route('/test')
def test():
    return jsonify({
        'message': 'Test endpoint working!',
        'status': 'success',
        'timestamp': str(os.environ.get('VERCEL_REGION', 'unknown'))
    })

# For Vercel, we need to export the app
# This is the key fix for the serverless function
if __name__ == '__main__':
    app.run(debug=False)
else:
    # This is what Vercel will use
    application = app