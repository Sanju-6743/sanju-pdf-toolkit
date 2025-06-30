from flask import Blueprint, request, jsonify, current_app
import os
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter
import uuid
import time
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
protect_bp = Blueprint('protect', __name__)

def register_routes(app, socketio):
    """Register routes with the Flask app"""
    app.register_blueprint(protect_bp)
    
    @app.route('/protect', methods=['POST'])
    def protect_route():
        if 'pdf' not in request.files:
            socketio.emit('status_update', {
                'status': 'error', 
                'message': '⚠️ No PDF file was uploaded.',
                'tool': 'protect'
            })
            return jsonify({'status': 'error', 'message': 'No PDF file was uploaded.'})
        
        pdf_file = request.files['pdf']
        if pdf_file.filename == '':
            socketio.emit('status_update', {
                'status': 'error', 
                'message': '⚠️ No PDF file was selected.',
                'tool': 'protect'
            })
            return jsonify({'status': 'error', 'message': 'No PDF file was selected.'})
        
        # Get password and permissions
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not password:
            socketio.emit('status_update', {
                'status': 'error', 
                'message': '⚠️ Password is required.',
                'tool': 'protect'
            })
            return jsonify({'status': 'error', 'message': 'Password is required.'})
        
        if password != confirm_password:
            socketio.emit('status_update', {
                'status': 'error', 
                'message': '⚠️ Passwords do not match.',
                'tool': 'protect'
            })
            return jsonify({'status': 'error', 'message': 'Passwords do not match.'})
        
        # Get permissions
        allow_print = 'allow_print' in request.form
        allow_copy = 'allow_copy' in request.form
        allow_modify = 'allow_modify' in request.form
        
        # Save the uploaded file
        filename = secure_filename(pdf_file.filename)
        from app import UPLOAD_FOLDER
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        pdf_file.save(file_path)
        
        # Start a background thread for processing
        thread = socketio.start_background_task(
            protect_pdf, 
            file_path=file_path,
            password=password,
            allow_print=allow_print,
            allow_copy=allow_copy,
            allow_modify=allow_modify,
            socketio=socketio
        )
        
        # Return immediately with a processing message
        return jsonify({'status': 'processing', 'message': 'Protecting PDF...'})
    
    @app.route('/unlock', methods=['POST'])
    def unlock_route():
        if 'pdf' not in request.files:
            socketio.emit('status_update', {
                'status': 'error', 
                'message': '⚠️ No PDF file was uploaded.',
                'tool': 'unlock'
            })
            return jsonify({'status': 'error', 'message': 'No PDF file was uploaded.'})
        
        pdf_file = request.files['pdf']
        if pdf_file.filename == '':
            socketio.emit('status_update', {
                'status': 'error', 
                'message': '⚠️ No PDF file was selected.',
                'tool': 'unlock'
            })
            return jsonify({'status': 'error', 'message': 'No PDF file was selected.'})
        
        # Get password
        password = request.form.get('password', '')
        
        if not password:
            socketio.emit('status_update', {
                'status': 'error', 
                'message': '⚠️ Password is required.',
                'tool': 'unlock'
            })
            return jsonify({'status': 'error', 'message': 'Password is required.'})
        
        # Save the uploaded file
        filename = secure_filename(pdf_file.filename)
        from app import UPLOAD_FOLDER
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        pdf_file.save(file_path)
        
        # Start a background thread for processing
        thread = socketio.start_background_task(
            unlock_pdf, 
            file_path=file_path,
            password=password,
            socketio=socketio
        )
        
        # Return immediately with a processing message
        return jsonify({'status': 'processing', 'message': 'Unlocking PDF...'})

def protect_pdf(file_path, password, allow_print=True, allow_copy=True, allow_modify=True, socketio=None):
    """Protect PDF with password"""
    if socketio:
        socketio.emit('status_update', {
            'status': 'processing', 
            'message': 'Starting PDF protection process...',
            'tool': 'protect'
        })
    
    try:
        # Get paths
        from app import OUTPUT_FOLDER
        
        # Generate a unique ID for this operation
        operation_id = uuid.uuid4().hex[:8]
        base_filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(base_filename)[0]
        
        # Read the PDF
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing', 
                'message': 'Reading PDF...',
                'progress': 30,
                'tool': 'protect'
            })
        
        reader = PdfReader(file_path)
        writer = PdfWriter()
        
        # Add all pages to writer
        for page in reader.pages:
            writer.add_page(page)
        
        # Set up encryption
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing', 
                'message': 'Encrypting PDF...',
                'progress': 60,
                'tool': 'protect'
            })
        
        # Set permissions
        permissions = 0
        if allow_print:
            permissions |= 4  # Print document
        if allow_copy:
            permissions |= 16  # Extract content
        if allow_modify:
            permissions |= 8   # Modify contents
        
        # Encrypt the PDF
        writer.encrypt(password, password, use_128bit=True, permissions_flag=permissions)
        
        # Create output file
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing', 
                'message': 'Creating protected PDF...',
                'progress': 90,
                'tool': 'protect'
            })
        
        output_filename = f"{name_without_ext}_protected_{operation_id}.pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        # Prepare download links
        downloads = [
            {
                'name': output_filename,
                'url': f'/download/{output_filename}',
                'type': 'Protected PDF',
                'filename': output_filename
            }
        ]
        
        if socketio:
            socketio.emit('status_update', {
                'status': 'success', 
                'message': '✅ PDF protected successfully!',
                'downloads': downloads,
                'tool': 'protect'
            })
    
    except Exception as e:
        logger.error(f"Error protecting PDF: {str(e)}")
        if socketio:
            socketio.emit('status_update', {
                'status': 'error', 
                'message': f'❌ Error protecting PDF: {str(e)}',
                'tool': 'protect'
            })

def unlock_pdf(file_path, password, socketio=None):
    """Unlock PDF by removing password protection"""
    if socketio:
        socketio.emit('status_update', {
            'status': 'processing', 
            'message': 'Starting PDF unlocking process...',
            'tool': 'unlock'
        })
    
    try:
        # Get paths
        from app import OUTPUT_FOLDER
        
        # Generate a unique ID for this operation
        operation_id = uuid.uuid4().hex[:8]
        base_filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(base_filename)[0]
        
        # Read the PDF
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing', 
                'message': 'Reading PDF...',
                'progress': 30,
                'tool': 'unlock'
            })
        
        reader = PdfReader(file_path)
        
        # Check if PDF is encrypted
        if not reader.is_encrypted:
            if socketio:
                socketio.emit('status_update', {
                    'status': 'error', 
                    'message': '⚠️ The PDF is not password-protected.',
                    'tool': 'unlock'
                })
            return
        
        # Try to decrypt with password
        try:
            reader.decrypt(password)
        except:
            if socketio:
                socketio.emit('status_update', {
                    'status': 'error', 
                    'message': '❌ Incorrect password.',
                    'tool': 'unlock'
                })
            return
        
        # Create a new PDF without encryption
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing', 
                'message': 'Removing password protection...',
                'progress': 60,
                'tool': 'unlock'
            })
        
        writer = PdfWriter()
        
        # Add all pages to writer
        for page in reader.pages:
            writer.add_page(page)
        
        # Create output file
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing', 
                'message': 'Creating unlocked PDF...',
                'progress': 90,
                'tool': 'unlock'
            })
        
        output_filename = f"{name_without_ext}_unlocked_{operation_id}.pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        # Prepare download links
        downloads = [
            {
                'name': output_filename,
                'url': f'/download/{output_filename}',
                'type': 'Unlocked PDF',
                'filename': output_filename
            }
        ]
        
        if socketio:
            socketio.emit('status_update', {
                'status': 'success', 
                'message': '✅ PDF unlocked successfully!',
                'downloads': downloads,
                'tool': 'unlock'
            })
    
    except Exception as e:
        logger.error(f"Error unlocking PDF: {str(e)}")
        if socketio:
            socketio.emit('status_update', {
                'status': 'error', 
                'message': f'❌ Error unlocking PDF: {str(e)}',
                'tool': 'unlock'
            })