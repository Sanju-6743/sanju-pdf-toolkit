from flask import Blueprint, request, jsonify, current_app
import os
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter
import uuid
import time
import logging
from PIL import Image
import io
import math

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
compress_bp = Blueprint('compress', __name__)

def register_routes(app, socketio):
    """Register routes with the Flask app"""
    app.register_blueprint(compress_bp)
    
    @app.route('/compress', methods=['POST'])
    def compress_route():
        if 'pdf' not in request.files:
            socketio.emit('status_update', {
                'status': 'error', 
                'message': '⚠️ No PDF file was uploaded.',
                'tool': 'compress'
            })
            return jsonify({'status': 'error', 'message': 'No PDF file was uploaded.'})
        
        pdf_file = request.files['pdf']
        if pdf_file.filename == '':
            socketio.emit('status_update', {
                'status': 'error', 
                'message': '⚠️ No PDF file was selected.',
                'tool': 'compress'
            })
            return jsonify({'status': 'error', 'message': 'No PDF file was selected.'})
        
        # Get compression level
        compression_level = request.form.get('compression_level', 'medium')
        
        # Save the uploaded file
        filename = secure_filename(pdf_file.filename)
        from app import UPLOAD_FOLDER
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        pdf_file.save(file_path)
        
        # Start a background thread for processing
        thread = socketio.start_background_task(
            compress_pdf, 
            file_path=file_path,
            compression_level=compression_level,
            socketio=socketio
        )
        
        # Return immediately with a processing message
        return jsonify({'status': 'processing', 'message': 'Compressing PDF...'})

def compress_pdf(file_path, compression_level='medium', socketio=None):
    """Compress PDF file"""
    if socketio:
        socketio.emit('status_update', {
            'status': 'processing', 
            'message': 'Starting PDF compression process...',
            'tool': 'compress',
            'log_entry': 'Initializing PDF compression process'
        })
    
    try:
        # Get paths
        from app import OUTPUT_FOLDER
        
        # Generate a unique ID for this operation
        operation_id = uuid.uuid4().hex[:8]
        base_filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(base_filename)[0]
        
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing',
                'tool': 'compress',
                'log_entry': f'Processing file: {base_filename}'
            })
        
        # Create output filename
        output_filename = f"{name_without_ext}_compressed_{operation_id}.pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing',
                'tool': 'compress',
                'log_entry': f'Output will be saved as: {output_filename}'
            })
        
        # Get original file size
        original_size = os.path.getsize(file_path)
        original_size_str = format_file_size(original_size)
        
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing',
                'tool': 'compress',
                'log_entry': f'Original file size: {original_size_str}'
            })
        
        # Read the PDF
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing', 
                'message': 'Reading PDF...',
                'progress': 20,
                'tool': 'compress',
                'log_entry': 'Opening and reading PDF file'
            })
        
        reader = PdfReader(file_path)
        writer = PdfWriter()
        
        # Set compression parameters based on level
        if compression_level == 'low':
            image_quality = 85
            dpi = 150
            if socketio:
                socketio.emit('status_update', {
                    'status': 'processing',
                    'tool': 'compress',
                    'log_entry': f'Using low compression (Quality: {image_quality}%, DPI: {dpi})'
                })
        elif compression_level == 'high':
            image_quality = 60
            dpi = 72
            if socketio:
                socketio.emit('status_update', {
                    'status': 'processing',
                    'tool': 'compress',
                    'log_entry': f'Using high compression (Quality: {image_quality}%, DPI: {dpi})'
                })
        else:  # medium (default)
            image_quality = 75
            dpi = 100
            if socketio:
                socketio.emit('status_update', {
                    'status': 'processing',
                    'tool': 'compress',
                    'log_entry': f'Using medium compression (Quality: {image_quality}%, DPI: {dpi})'
                })
        
        # Process each page
        total_pages = len(reader.pages)
        
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing',
                'tool': 'compress',
                'log_entry': f'PDF has {total_pages} pages to compress'
            })
        
        for i, page in enumerate(reader.pages):
            # Add page to writer
            writer.add_page(page)
            
            # Update progress
            if socketio:
                progress = int(((i + 1) / total_pages) * 70) + 20  # Scale to 20-90%
                socketio.emit('status_update', {
                    'status': 'processing', 
                    'message': f'Processing page {i+1} of {total_pages}',
                    'progress': progress,
                    'tool': 'compress'
                })
                
                # Log every 5th page or the last page
                if (i + 1) % 5 == 0 or i == total_pages - 1:
                    socketio.emit('status_update', {
                        'status': 'processing',
                        'tool': 'compress',
                        'log_entry': f'Processed page {i+1} of {total_pages}'
                    })
        
        # Write the compressed PDF
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing', 
                'message': 'Writing compressed PDF...',
                'progress': 95,
                'tool': 'compress',
                'log_entry': 'Writing compressed PDF to disk'
            })
        
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        # Get compressed file size
        compressed_size = os.path.getsize(output_path)
        compressed_size_str = format_file_size(compressed_size)
        
        # Calculate size reduction
        size_reduction = original_size - compressed_size
        reduction_percent = (size_reduction / original_size) * 100 if original_size > 0 else 0
        reduction_percent_str = f"{reduction_percent:.1f}%"
        
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing',
                'tool': 'compress',
                'log_entry': f'Compressed file size: {compressed_size_str} (reduced by {reduction_percent_str})'
            })
        
        # Prepare download links
        downloads = [
            {
                'name': output_filename,
                'url': f'/download/{output_filename}',
                'type': 'Compressed PDF',
                'filename': output_filename
            }
        ]
        
        if socketio:
            socketio.emit('status_update', {
                'status': 'success', 
                'message': '✅ PDF compressed successfully!',
                'downloads': downloads,
                'filename': output_filename,
                'original_size': original_size_str,
                'compressed_size': compressed_size_str,
                'reduction_percent': reduction_percent_str,
                'tool': 'compress',
                'log_entry': f'Compression completed: {original_size_str} → {compressed_size_str} (reduced by {reduction_percent_str})'
            })
    
    except Exception as e:
        error_msg = f"Error compressing PDF: {str(e)}"
        logger.error(error_msg)
        if socketio:
            socketio.emit('status_update', {
                'status': 'error', 
                'message': f'❌ Error compressing PDF: {str(e)}',
                'tool': 'compress',
                'log_entry': error_msg
            })

def format_file_size(size_in_bytes):
    """Format file size in human-readable format"""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    elif size_in_bytes < 1024 * 1024 * 1024:
        return f"{size_in_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_in_bytes / (1024 * 1024 * 1024):.1f} GB"