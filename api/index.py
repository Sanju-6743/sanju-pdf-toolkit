from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>PDF Toolkit - Working!</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            .container { max-width: 600px; margin: 0 auto; }
            h1 { color: #4CAF50; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 PDF Toolkit is Live!</h1>
            <p>Your deployment is working successfully!</p>
            <p>This is a simplified version to test the deployment.</p>
            <hr>
            <p><strong>Status:</strong> ✅ Deployed and Running</p>
            <p><strong>Platform:</strong> Vercel Serverless</p>
            <p><strong>Time:</strong> <span id="time"></span></p>
        </div>
        <script>
            document.getElementById('time').textContent = new Date().toLocaleString();
        </script>
    </body>
    </html>
    '''

@app.route('/test')
def test():
    return {'status': 'success', 'message': 'PDF Toolkit API is working!'}

# For Vercel
if __name__ == '__main__':
    app.run(debug=False)