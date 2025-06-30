from flask import Blueprint, request, jsonify, current_app
import os
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from pdfminer.high_level import extract_text
import uuid
import time
import logging
from docx import Document

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
extract_bp = Blueprint('extract', __name__)

def register_routes(app, socketio):
    """Register routes with the Flask app"""
    app.register_blueprint(extract_bp)
    
    @app.route('/extract_text', methods=['POST'])
    def extract_text_route():
        if 'pdf' not in request.files:
            socketio.emit('status_update', {
                'status': 'error', 
                'message': '⚠️ No PDF file was uploaded.',
                'tool': 'extract-text'
            })
            return jsonify({'status': 'error', 'message': 'No PDF file was uploaded.'})
        
        pdf_file = request.files['pdf']
        if pdf_file.filename == '':
            socketio.emit('status_update', {
                'status': 'error', 
                'message': '⚠️ No PDF file was selected.',
                'tool': 'extract-text'
            })
            return jsonify({'status': 'error', 'message': 'No PDF file was selected.'})
        
        # Get output format
        output_format = request.form.get('output_format', 'txt')
        
        # Save the uploaded file
        filename = secure_filename(pdf_file.filename)
        from app import UPLOAD_FOLDER
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        pdf_file.save(file_path)
        
        # Start a background thread for processing
        thread = socketio.start_background_task(
            extract_text_from_pdf, 
            file_path=file_path,
            output_format=output_format,
            socketio=socketio
        )
        
        # Return immediately with a processing message
        return jsonify({'status': 'processing', 'message': 'Extracting text...'})

def extract_text_from_pdf(file_path, output_format='txt', socketio=None):
    """Extract text from PDF"""
    if socketio:
        socketio.emit('status_update', {
            'status': 'processing', 
            'message': 'Starting text extraction process...',
            'tool': 'extract-text'
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
                'progress': 20,
                'tool': 'extract-text'
            })
        
        # Extract text using pdfminer
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing', 
                'message': 'Extracting text...',
                'progress': 40,
                'tool': 'extract-text'
            })
        
        extracted_text = extract_text(file_path)
        
        if not extracted_text.strip():
            # Try PyPDF2 as a fallback
            reader = PdfReader(file_path)
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text())
            extracted_text = "\n\n".join(text_parts)
        
        if not extracted_text.strip():
            if socketio:
                socketio.emit('status_update', {
                    'status': 'error', 
                    'message': '❌ No text could be extracted from the PDF.',
                    'tool': 'extract-text'
                })
            return
        
        # Create output files
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing', 
                'message': 'Creating output files...',
                'progress': 80,
                'tool': 'extract-text'
            })
        
        # Create text file
        txt_filename = f"{name_without_ext}_text_{operation_id}.txt"
        txt_path = os.path.join(OUTPUT_FOLDER, txt_filename)
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        
        # Create Word document if requested
        docx_path = None
        if output_format == 'docx':
            docx_filename = f"{name_without_ext}_text_{operation_id}.docx"
            docx_path = os.path.join(OUTPUT_FOLDER, docx_filename)
            
            doc = Document()
            doc.add_paragraph(extracted_text)
            doc.save(docx_path)
        
        # Prepare download links
        downloads = [
            {
                'name': txt_filename,
                'url': f'/download/{txt_filename}',
                'type': 'Text File (.txt)',
                'filename': txt_filename
            }
        ]
        
        if docx_path:
            downloads.append({
                'name': docx_filename,
                'url': f'/download/{docx_filename}',
                'type': 'Word Document (.docx)',
                'filename': docx_filename
            })
        
        # Send a preview of the extracted text (first 1000 characters)
        preview_text = extracted_text[:1000] + ('...' if len(extracted_text) > 1000 else '')
        
        if socketio:
            socketio.emit('status_update', {
                'status': 'success', 
                'message': '✅ Text extracted successfully!',
                'downloads': downloads,
                'preview_text': preview_text,
                'tool': 'extract-text'
            })
    
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}")
        if socketio:
            socketio.emit('status_update', {
                'status': 'error', 
                'message': f'❌ Error extracting text: {str(e)}',
                'tool': 'extract-text'
            })