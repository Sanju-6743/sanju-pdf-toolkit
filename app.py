import os
import uuid
import logging
import shutil
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename

# Try to import SocketIO, but make it optional for Vercel deployment
try:
    from flask_socketio import SocketIO
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    SocketIO = None
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'pdf-toolkit-secret-key'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB max upload size

# Configure Socket.IO (optional for Vercel deployment)
if SOCKETIO_AVAILABLE:
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
else:
    # Create a mock socketio object for compatibility
    class MockSocketIO:
        def emit(self, *args, **kwargs):
            pass
        def start_background_task(self, func, *args, **kwargs):
            # Run the task directly instead of in background
            return func(*args, **kwargs)
        def on(self, event):
            def decorator(func):
                return func
            return decorator
        def run(self, app, *args, **kwargs):
            app.run(*args, **kwargs)
        @property
        def wsgi_app(self):
            return None
    
    socketio = MockSocketIO()

# Configure response headers for all responses
@app.after_request
def add_header(response):
    """Add headers to all responses"""
    # Ensure JSON responses have the correct content type
    if response.mimetype == 'application/json':
        response.headers['Content-Type'] = 'application/json'
    return response

# Configure upload and output folders
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'output')
TEMP_FOLDER = os.path.join(BASE_DIR, 'temp')

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

# Email configuration
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USER = os.environ.get('EMAIL_USER', '')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')
EMAIL_FROM = os.environ.get('EMAIL_FROM', 'pdf-toolkit@example.com')

# Import modules
from modules.merge_pdf import register_routes as register_merge_routes
from modules.split_pdf import register_routes as register_split_routes
from modules.compress_pdf import register_routes as register_compress_routes
from modules.convert_pdf import register_routes as register_convert_routes
from modules.extract_pdf import register_routes as register_extract_routes
from modules.ocr_pdf import register_routes as register_ocr_routes
from modules.protect_pdf import register_routes as register_protect_routes
from modules.organize_pdf import register_routes as register_organize_routes
from modules.edit_pdf import register_routes as register_edit_routes

# Register module routes
register_merge_routes(app, socketio)
register_split_routes(app, socketio)
register_compress_routes(app, socketio)
register_convert_routes(app, socketio)
register_extract_routes(app, socketio)
register_ocr_routes(app, socketio)
register_protect_routes(app, socketio)
register_organize_routes(app, socketio)
register_edit_routes(app, socketio)

# Start cleanup thread
def safe_remove_file(file_path):
    """Safely remove a file with retries for locked files"""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            os.remove(file_path)
            return True
        except PermissionError:
            if attempt < max_retries - 1:
                logger.info(f"File {file_path} is locked. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.warning(f"Could not remove locked file after {max_retries} attempts: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Error removing file {file_path}: {str(e)}")
            return False
    return False

def safe_remove_directory(dir_path):
    """Safely remove a directory with special handling for reparse points"""
    try:
        # Check if it's a reparse point/symlink
        if os.path.islink(dir_path) or os.path.ismount(dir_path):
            # For symlinks, use os.unlink instead of shutil.rmtree
            try:
                os.unlink(dir_path)
                return True
            except Exception as e:
                logger.error(f"Error removing symlink {dir_path}: {str(e)}")
                return False
        else:
            # For regular directories
            shutil.rmtree(dir_path, ignore_errors=True)
            return True
    except Exception as e:
        logger.error(f"Error removing directory {dir_path}: {str(e)}")
        return False

def cleanup_folder(folder_path):
    """Clean up a specific folder with improved error handling"""
    if not os.path.exists(folder_path):
        return
        
    now = datetime.now()
    
    try:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            
            try:
                # Skip if we can't access the file
                if not os.access(file_path, os.R_OK):
                    logger.warning(f"Skipping inaccessible file/directory: {file_path}")
                    continue
                    
                file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                # Only clean up files older than 15 minutes
                if now - file_modified > timedelta(minutes=15):
                    if os.path.isfile(file_path):
                        safe_remove_file(file_path)
                    elif os.path.isdir(file_path):
                        safe_remove_directory(file_path)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
    except Exception as e:
        logger.error(f"Error accessing folder {folder_path}: {str(e)}")

def cleanup_files():
    """Clean up old files periodically with improved error handling"""
    while True:
        try:
            # Clean up each folder
            cleanup_folder(UPLOAD_FOLDER)
            cleanup_folder(OUTPUT_FOLDER)
            cleanup_folder(TEMP_FOLDER)
            
            # Sleep for 5 minutes
            time.sleep(300)
        except Exception as e:
            logger.error(f"Error in cleanup thread: {str(e)}")
            time.sleep(300)

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_files, daemon=True)
cleanup_thread.start()

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/download/<path:filename>')
def download_file(filename):
    """Download a file from the output folder"""
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

@app.route('/send_email', methods=['POST'])
def send_email():
    """Send an email with the processed file"""
    try:
        # Check if the request has JSON content
        if request.is_json:
            data = request.json
        else:
            # Handle form data if not JSON
            data = request.form.to_dict()
            
        filename = data.get('filename')
        email = data.get('email')
        subject = data.get('subject')
        message = data.get('message')
        
        if not filename or not email:
            response = jsonify({'status': 'error', 'message': 'Filename and email are required.'})
            response.headers['Content-Type'] = 'application/json'
            return response
        
        # Find the file in the output folder
        for file in os.listdir(OUTPUT_FOLDER):
            if filename in file:
                file_path = os.path.join(OUTPUT_FOLDER, file)
                break
        else:
            response = jsonify({'status': 'error', 'message': 'File not found.'})
            response.headers['Content-Type'] = 'application/json'
            return response
        
        # Start a background thread for sending email
        thread = socketio.start_background_task(
            send_email_task, 
            file_path=file_path,
            email=email,
            subject=subject,
            message=message
        )
        
        response = jsonify({'status': 'processing', 'message': 'Sending email...'})
        response.headers['Content-Type'] = 'application/json'
        return response
    
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        response = jsonify({'status': 'error', 'message': f'Error sending email: {str(e)}'})
        response.headers['Content-Type'] = 'application/json'
        return response

def send_email_task(file_path, email, subject, message):
    """Send email with attachment"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = email
        msg['Subject'] = subject
        
        # Add message body
        msg.attach(MIMEText(message, 'plain'))
        
        # Add attachment
        with open(file_path, 'rb') as f:
            attachment = MIMEApplication(f.read(), _subtype='pdf')
            attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file_path))
            msg.attach(attachment)
        
        # Send email
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            if EMAIL_USER and EMAIL_PASSWORD:
                server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        # Emit success event
        socketio.emit('email_status', {
            'status': 'success',
            'message': 'Email sent successfully!'
        })
    
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        socketio.emit('email_status', {
            'status': 'error',
            'message': f'Error sending email: {str(e)}'
        })

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    if request.path.startswith('/api/') or request.headers.get('Accept', '').find('application/json') != -1:
        return jsonify({'status': 'error', 'message': 'File too large. Maximum size is 500 MB.'}), 413
    return render_template('index.html'), 413

@app.errorhandler(500)
def internal_server_error(error):
    """Handle internal server error"""
    if request.path.startswith('/api/') or request.headers.get('Accept', '').find('application/json') != -1:
        return jsonify({'status': 'error', 'message': 'Internal server error. Please try again later.'}), 500
    return render_template('index.html'), 500

@app.errorhandler(404)
def not_found_error(error):
    """Handle not found error"""
    if request.path.startswith('/api/') or request.headers.get('Accept', '').find('application/json') != -1:
        return jsonify({'status': 'error', 'message': 'Page not found.'}), 404
    return render_template('index.html'), 404

# Socket.IO connection events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

if __name__ == '__main__':
    # Run the app locally
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    
# For Vercel deployment
# Only set wsgi_app for production deployment, not for local development
if not app.debug:
    try:
        app.wsgi_app = socketio.wsgi_app
    except AttributeError:
        # Handle case where socketio doesn't have wsgi_app attribute
        pass