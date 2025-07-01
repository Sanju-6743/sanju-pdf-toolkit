from flask import Flask, render_template_string
import os

app = Flask(__name__)

# Simple HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Toolkit - Live!</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        .status {
            font-size: 1.2em;
            margin: 20px 0;
        }
        .success {
            color: #4CAF50;
            font-weight: bold;
        }
        .info {
            background: rgba(255, 255, 255, 0.2);
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎉 PDF Toolkit is Live!</h1>
        <div class="status success">✅ Deployment Successful!</div>
        
        <div class="info">
            <h3>🚀 Your PDF Toolkit is Working!</h3>
            <p>This confirms that your Flask application is properly deployed and running.</p>
            <p><strong>Platform:</strong> {{ platform }}</p>
            <p><strong>Status:</strong> Active and Responding</p>
            <p><strong>Time:</strong> <span id="time"></span></p>
        </div>
        
        <div class="info">
            <h3>📋 Next Steps:</h3>
            <p>✅ Basic deployment working</p>
            <p>🔄 Ready to add full PDF toolkit features</p>
            <p>🎯 All systems operational</p>
        </div>
        
        <div class="info">
            <h3>🔧 Available Soon:</h3>
            <ul style="text-align: left; display: inline-block;">
                <li>PDF Merge & Split</li>
                <li>PDF Compression</li>
                <li>Document Conversion</li>
                <li>File Upload/Download</li>
                <li>Real-time Processing</li>
            </ul>
        </div>
    </div>
    
    <script>
        document.getElementById('time').textContent = new Date().toLocaleString();
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    platform = os.environ.get('VERCEL', 'Unknown')
    if platform:
        platform = "Vercel Serverless"
    else:
        platform = "Web Server"
    
    return render_template_string(HTML_TEMPLATE, platform=platform)

@app.route('/health')
def health():
    return {
        'status': 'healthy',
        'message': 'PDF Toolkit is running successfully!',
        'platform': 'Vercel' if os.environ.get('VERCEL') else 'Other'
    }

@app.route('/test')
def test():
    return {
        'status': 'success',
        'message': 'API endpoint working!',
        'deployment': 'active'
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)