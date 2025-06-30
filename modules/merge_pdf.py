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
merge_bp = Blueprint('merge', __name__)

def register_routes(app, socketio):
    """Register routes with the Flask app"""
    app.register_blueprint(merge_bp)
    
    @app.route('/merge', methods=['POST'])
    def merge_route():
        try:
            if 'files[]' not in request.files:
                socketio.emit('status_update', {
                    'status': 'error', 
                    'message': '⚠️ No PDF files were uploaded.',
                    'tool': 'merge'
                })
                response = jsonify({'status': 'error', 'message': 'No PDF files were uploaded.'})
                response.headers['Content-Type'] = 'application/json'
                return response
            
            files = request.files.getlist('files[]')
            if len(files) < 2:
                socketio.emit('status_update', {
                    'status': 'error', 
                    'message': '⚠️ At least 2 PDF files are required for merging.',
                    'tool': 'merge'
                })
                response = jsonify({'status': 'error', 'message': 'At least 2 PDF files are required for merging.'})
                response.headers['Content-Type'] = 'application/json'
                return response
            
            # Get file order if provided
            file_order = request.form.get('order', '')
            
            # Save uploaded files
            file_paths = []
            for file in files:
                if file.filename == '':
                    continue
                
                filename = secure_filename(file.filename)
                from app import UPLOAD_FOLDER
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                file_paths.append(file_path)
            
            if len(file_paths) < 2:
                socketio.emit('status_update', {
                    'status': 'error', 
                    'message': '⚠️ At least 2 valid PDF files are required for merging.',
                    'tool': 'merge'
                })
                response = jsonify({'status': 'error', 'message': 'At least 2 valid PDF files are required for merging.'})
                response.headers['Content-Type'] = 'application/json'
                return response
            
            # Start a background thread for processing
            thread = socketio.start_background_task(
                merge_pdfs, 
                file_paths=file_paths,
                file_order=file_order,
                socketio=socketio
            )
            
            # Return immediately with a processing message
            response = jsonify({'status': 'processing', 'message': 'Merging PDFs...'})
            response.headers['Content-Type'] = 'application/json'
            return response
            
        except Exception as e:
            logger.error(f"Error in merge route: {str(e)}")
            socketio.emit('status_update', {
                'status': 'error', 
                'message': f'⚠️ Error processing request: {str(e)}',
                'tool': 'merge'
            })
            response = jsonify({'status': 'error', 'message': f'Error processing request: {str(e)}'})
            response.headers['Content-Type'] = 'application/json'
            return response

def merge_pdfs(file_paths, file_order='', socketio=None):
    """Merge multiple PDFs into one"""
    if socketio:
        socketio.emit('status_update', {
            'status': 'processing', 
            'message': 'Starting PDF merge process...',
            'tool': 'merge',
            'log_entry': 'Initializing PDF merge process'
        })
    
    try:
        # Get paths
        from app import OUTPUT_FOLDER
        
        # Generate a unique ID for this merge
        merge_id = uuid.uuid4().hex[:8]
        
        # Create output filename
        output_filename = f"merged_{merge_id}.pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing',
                'tool': 'merge',
                'log_entry': f'Created output file: {output_filename}'
            })
        
        # Create PDF writer
        writer = PdfWriter()
        
        # Reorder files if order is provided
        if file_order:
            try:
                order_indices = [int(i) for i in file_order.split(',')]
                # Validate indices
                if len(order_indices) == len(file_paths) and all(0 <= i < len(file_paths) for i in order_indices):
                    if socketio:
                        socketio.emit('status_update', {
                            'status': 'processing',
                            'tool': 'merge',
                            'log_entry': f'Reordering files according to specified order'
                        })
                    file_paths = [file_paths[i] for i in order_indices]
            except (ValueError, IndexError):
                # If order is invalid, use original order
                if socketio:
                    socketio.emit('status_update', {
                        'status': 'warning',
                        'tool': 'merge',
                        'log_entry': f'Invalid file order provided, using default order'
                    })
        
        # Process each PDF
        total_files = len(file_paths)
        total_pages = 0
        
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing',
                'tool': 'merge',
                'log_entry': f'Starting to process {total_files} PDF files'
            })
        
        for i, file_path in enumerate(file_paths):
            try:
                # Get filename from path
                filename = os.path.basename(file_path)
                
                # Update status
                if socketio:
                    progress = int((i / total_files) * 90)  # Scale to 0-90%
                    socketio.emit('status_update', {
                        'status': 'processing', 
                        'message': f'Processing file {i+1} of {total_files}',
                        'progress': progress,
                        'tool': 'merge',
                        'log_entry': f'Processing file {i+1} of {total_files}: {filename}'
                    })
                
                # Check if file is a valid PDF
                if not file_path.lower().endswith('.pdf'):
                    logger.warning(f"Skipping non-PDF file: {file_path}")
                    if socketio:
                        socketio.emit('status_update', {
                            'status': 'warning',
                            'tool': 'merge',
                            'log_entry': f'Skipping non-PDF file: {filename}'
                        })
                    continue
                
                # Open PDF
                reader = PdfReader(file_path)
                page_count = len(reader.pages)
                
                if socketio:
                    socketio.emit('status_update', {
                        'status': 'processing',
                        'tool': 'merge',
                        'log_entry': f'File {filename} has {page_count} pages'
                    })
                
                # Add all pages to writer
                for j, page in enumerate(reader.pages):
                    writer.add_page(page)
                    
                    # Update status for every 10th page or last page
                    if (j + 1) % 10 == 0 or j == page_count - 1:
                        if socketio:
                            socketio.emit('status_update', {
                                'status': 'processing',
                                'tool': 'merge',
                                'log_entry': f'Added page {j+1} of {page_count} from {filename}'
                            })
                
                total_pages += page_count
                
                if socketio:
                    socketio.emit('status_update', {
                        'status': 'processing',
                        'tool': 'merge',
                        'log_entry': f'Successfully processed {filename} ({page_count} pages)'
                    })
            
            except Exception as e:
                error_msg = f"Error processing file {os.path.basename(file_path)}: {str(e)}"
                logger.error(error_msg)
                if socketio:
                    socketio.emit('status_update', {
                        'status': 'error',
                        'tool': 'merge',
                        'log_entry': error_msg
                    })
                # Continue with next file
                continue
        
        # Check if any pages were added
        if len(writer.pages) == 0:
            if socketio:
                socketio.emit('status_update', {
                    'status': 'error', 
                    'message': '❌ No valid PDF pages found in the uploaded files.',
                    'tool': 'merge',
                    'log_entry': 'Error: No valid PDF pages found in the uploaded files'
                })
            return
        
        # Write merged PDF
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing', 
                'message': 'Writing merged PDF...',
                'progress': 95,
                'tool': 'merge',
                'log_entry': f'Writing merged PDF with {total_pages} pages to {output_filename}'
            })
        
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        # Get file size
        file_size = os.path.getsize(output_path)
        file_size_str = format_file_size(file_size)
        
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing',
                'tool': 'merge',
                'log_entry': f'Successfully created merged PDF: {output_filename} ({file_size_str})'
            })
        
        # Prepare download links
        downloads = [
            {
                'name': output_filename,
                'url': f'/download/{output_filename}',
                'type': 'Merged PDF',
                'filename': output_filename
            }
        ]
        
        if socketio:
            socketio.emit('status_update', {
                'status': 'success', 
                'message': '✅ PDFs merged successfully!',
                'downloads': downloads,
                'filename': output_filename,
                'tool': 'merge',
                'log_entry': f'PDF merge completed successfully: {total_files} files merged into {output_filename} with {total_pages} pages ({file_size_str})'
            })
    
    except Exception as e:
        error_msg = f"Error merging PDFs: {str(e)}"
        logger.error(error_msg)
        if socketio:
            socketio.emit('status_update', {
                'status': 'error', 
                'message': f'❌ Error merging PDFs: {str(e)}',
                'tool': 'merge',
                'log_entry': error_msg
            })

def format_file_size(size_bytes):
    """Format file size in human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"