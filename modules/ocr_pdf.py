from flask import Blueprint, request, jsonify, current_app
import os
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from werkzeug.utils import secure_filename
import uuid
import time
import logging
from docx import Document
from PyPDF2 import PdfReader, PdfWriter
import io

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
ocr_bp = Blueprint('ocr', __name__)

def register_routes(app, socketio):
    """Register routes with the Flask app"""
    app.register_blueprint(ocr_bp)
    
    @app.route('/ocr', methods=['POST'])
    def ocr_route():
        if 'file' not in request.files:
            socketio.emit('status_update', {
                'status': 'error', 
                'message': '⚠️ No file was uploaded.',
                'tool': 'ocr'
            })
            return jsonify({'status': 'error', 'message': 'No file was uploaded.'})
        
        file = request.files['file']
        if file.filename == '':
            socketio.emit('status_update', {
                'status': 'error', 
                'message': '⚠️ No file was selected.',
                'tool': 'ocr'
            })
            return jsonify({'status': 'error', 'message': 'No file was selected.'})
        
        # Get parameters
        language = request.form.get('language', 'eng')
        output_format = request.form.get('output_format', 'txt')
        
        # Save the uploaded file
        filename = secure_filename(file.filename)
        from app import UPLOAD_FOLDER
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Start a background thread for processing
        thread = socketio.start_background_task(
            perform_ocr, 
            file_path=file_path,
            language=language,
            output_format=output_format,
            socketio=socketio
        )
        
        # Return immediately with a processing message
        return jsonify({'status': 'processing', 'message': 'Performing OCR...'})

def perform_ocr(file_path, language='eng', output_format='txt', socketio=None):
    """Perform OCR on PDF or image"""
    if socketio:
        socketio.emit('status_update', {
            'status': 'processing', 
            'message': 'Starting OCR process...',
            'tool': 'ocr'
        })
    
    try:
        # Get paths
        from app import OUTPUT_FOLDER, TEMP_FOLDER
        
        # Generate a unique ID for this operation
        operation_id = uuid.uuid4().hex[:8]
        base_filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(base_filename)[0]
        
        # Check file type
        is_pdf = file_path.lower().endswith('.pdf')
        
        # Convert PDF to images if needed
        if is_pdf:
            if socketio:
                socketio.emit('status_update', {
                    'status': 'processing', 
                    'message': 'Converting PDF to images...',
                    'progress': 20,
                    'tool': 'ocr'
                })
            
            # Create temp directory for images
            temp_dir = os.path.join(TEMP_FOLDER, f"ocr_{operation_id}")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Convert PDF to images
            images = convert_from_path(file_path)
            image_paths = []
            
            for i, image in enumerate(images):
                image_path = os.path.join(temp_dir, f"page_{i+1}.png")
                image.save(image_path, 'PNG')
                image_paths.append(image_path)
        else:
            # Single image file
            image_paths = [file_path]
        
        # Perform OCR on each image
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing', 
                'message': 'Performing OCR...',
                'progress': 40,
                'tool': 'ocr'
            })
        
        text_parts = []
        total_images = len(image_paths)
        
        for i, image_path in enumerate(image_paths):
            if socketio:
                progress = int(40 + (i / total_images) * 40)  # Scale from 40% to 80%
                socketio.emit('status_update', {
                    'status': 'processing', 
                    'message': f'Processing image {i+1} of {total_images}...',
                    'progress': progress,
                    'tool': 'ocr'
                })
            
            # Perform OCR
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang=language)
            text_parts.append(text)
        
        # Combine text from all pages
        extracted_text = "\n\n".join(text_parts)
        
        if not extracted_text.strip():
            if socketio:
                socketio.emit('status_update', {
                    'status': 'error', 
                    'message': '❌ No text could be extracted from the file.',
                    'tool': 'ocr'
                })
            return
        
        # Create output files
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing', 
                'message': 'Creating output files...',
                'progress': 90,
                'tool': 'ocr'
            })
        
        # Create text file
        txt_filename = f"{name_without_ext}_ocr_{operation_id}.txt"
        txt_path = os.path.join(OUTPUT_FOLDER, txt_filename)
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        
        # Create additional output formats if requested
        docx_path = None
        pdf_path = None
        
        if output_format == 'docx':
            docx_filename = f"{name_without_ext}_ocr_{operation_id}.docx"
            docx_path = os.path.join(OUTPUT_FOLDER, docx_filename)
            
            doc = Document()
            doc.add_paragraph(extracted_text)
            doc.save(docx_path)
        
        elif output_format == 'pdf' and is_pdf:
            # Create searchable PDF
            pdf_filename = f"{name_without_ext}_searchable_{operation_id}.pdf"
            pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)
            
            # Read original PDF
            reader = PdfReader(file_path)
            writer = PdfWriter()
            
            # Add each page with OCR text
            for i, page in enumerate(reader.pages):
                if i < len(text_parts):
                    page.add_text_as_invisible(text_parts[i])
                writer.add_page(page)
            
            # Write searchable PDF
            with open(pdf_path, 'wb') as f:
                writer.write(f)
        
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
            docx_filename = os.path.basename(docx_path)
            downloads.append({
                'name': docx_filename,
                'url': f'/download/{docx_filename}',
                'type': 'Word Document (.docx)',
                'filename': docx_filename
            })
        
        if pdf_path:
            pdf_filename = os.path.basename(pdf_path)
            downloads.append({
                'name': pdf_filename,
                'url': f'/download/{pdf_filename}',
                'type': 'Searchable PDF',
                'filename': pdf_filename
            })
        
        # Send a preview of the extracted text (first 1000 characters)
        preview_text = extracted_text[:1000] + ('...' if len(extracted_text) > 1000 else '')
        
        if socketio:
            socketio.emit('status_update', {
                'status': 'success', 
                'message': '✅ OCR completed successfully!',
                'downloads': downloads,
                'preview_text': preview_text,
                'tool': 'ocr'
            })
    
    except Exception as e:
        logger.error(f"Error performing OCR: {str(e)}")
        if socketio:
            socketio.emit('status_update', {
                'status': 'error', 
                'message': f'❌ Error performing OCR: {str(e)}',
                'tool': 'ocr'
            })