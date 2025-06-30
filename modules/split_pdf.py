from flask import Blueprint, request, jsonify, current_app
import os
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter
import uuid
import time
import logging
import zipfile

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
split_bp = Blueprint('split', __name__)

def register_routes(app, socketio):
    """Register routes with the Flask app"""
    app.register_blueprint(split_bp)
    
    @app.route('/split', methods=['POST'])
    def split_route():
        if 'pdf' not in request.files:
            socketio.emit('status_update', {
                'status': 'error', 
                'message': '⚠️ No PDF file was uploaded.',
                'tool': 'split'
            })
            return jsonify({'status': 'error', 'message': 'No PDF file was uploaded.'})
        
        pdf_file = request.files['pdf']
        if pdf_file.filename == '':
            socketio.emit('status_update', {
                'status': 'error', 
                'message': '⚠️ No PDF file was selected.',
                'tool': 'split'
            })
            return jsonify({'status': 'error', 'message': 'No PDF file was selected.'})
        
        # Get split parameters
        split_method = request.form.get('split_method', 'all')
        page_range = request.form.get('page_range', '')
        odd_even = request.form.get('odd_even', 'all')
        
        # Save the uploaded file
        filename = secure_filename(pdf_file.filename)
        from app import UPLOAD_FOLDER
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        pdf_file.save(file_path)
        
        # Start a background thread for processing
        thread = socketio.start_background_task(
            split_pdf, 
            file_path=file_path,
            split_method=split_method,
            page_range=page_range,
            odd_even=odd_even,
            socketio=socketio
        )
        
        # Return immediately with a processing message
        return jsonify({'status': 'processing', 'message': 'Splitting PDF...'})

def split_pdf(file_path, split_method='all', page_range='', odd_even='all', socketio=None):
    """Split PDF into multiple files"""
    if socketio:
        socketio.emit('status_update', {
            'status': 'processing', 
            'message': 'Starting PDF split process...',
            'tool': 'split',
            'log_entry': 'Initializing PDF split process'
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
                'tool': 'split',
                'log_entry': f'Processing file: {base_filename}'
            })
        
        # Read the PDF
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing', 
                'message': 'Reading PDF...',
                'progress': 20,
                'tool': 'split',
                'log_entry': 'Opening and reading PDF file'
            })
        
        reader = PdfReader(file_path)
        total_pages = len(reader.pages)
        
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing',
                'tool': 'split',
                'log_entry': f'PDF has {total_pages} pages'
            })
        
        if total_pages == 0:
            if socketio:
                socketio.emit('status_update', {
                    'status': 'error', 
                    'message': '❌ The PDF file is empty.',
                    'tool': 'split',
                    'log_entry': 'Error: The PDF file is empty'
                })
            return
        
        # Determine pages to extract based on split method
        pages_to_extract = []
        
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing',
                'tool': 'split',
                'log_entry': f'Split method: {split_method}'
            })
        
        if split_method == 'all':
            # Extract each page as a separate file
            pages_to_extract = [(i, i) for i in range(total_pages)]
            if socketio:
                socketio.emit('status_update', {
                    'status': 'processing',
                    'tool': 'split',
                    'log_entry': f'Will extract all {total_pages} pages individually'
                })
        
        elif split_method == 'range' and page_range:
            # Parse page range
            ranges = page_range.split(',')
            
            if socketio:
                socketio.emit('status_update', {
                    'status': 'processing',
                    'tool': 'split',
                    'log_entry': f'Parsing page range: {page_range}'
                })
            
            for r in ranges:
                if '-' in r:
                    try:
                        start, end = map(int, r.split('-'))
                        # Adjust for 0-based indexing
                        start = max(1, start) - 1
                        end = min(total_pages, end) - 1
                        pages_to_extract.append((start, end))
                        
                        if socketio:
                            socketio.emit('status_update', {
                                'status': 'processing',
                                'tool': 'split',
                                'log_entry': f'Added range: pages {start+1} to {end+1}'
                            })
                    except ValueError:
                        if socketio:
                            socketio.emit('status_update', {
                                'status': 'warning',
                                'tool': 'split',
                                'log_entry': f'Invalid range format: {r}'
                            })
                else:
                    try:
                        page = int(r) - 1  # Adjust for 0-based indexing
                        if 0 <= page < total_pages:
                            pages_to_extract.append((page, page))
                            if socketio:
                                socketio.emit('status_update', {
                                    'status': 'processing',
                                    'tool': 'split',
                                    'log_entry': f'Added single page: {page+1}'
                                })
                        else:
                            if socketio:
                                socketio.emit('status_update', {
                                    'status': 'warning',
                                    'tool': 'split',
                                    'log_entry': f'Page {r} is out of range (1-{total_pages})'
                                })
                    except ValueError:
                        if socketio:
                            socketio.emit('status_update', {
                                'status': 'warning',
                                'tool': 'split',
                                'log_entry': f'Invalid page number: {r}'
                            })
        
        elif split_method == 'odd_even':
            if socketio:
                socketio.emit('status_update', {
                    'status': 'processing',
                    'tool': 'split',
                    'log_entry': f'Odd/Even extraction mode: {odd_even}'
                })
                
            if odd_even == 'odd':
                # Extract odd pages
                pages_to_extract = [(i, i) for i in range(total_pages) if i % 2 == 0]  # 0-based indexing
                if socketio:
                    socketio.emit('status_update', {
                        'status': 'processing',
                        'tool': 'split',
                        'log_entry': f'Will extract {len(pages_to_extract)} odd pages'
                    })
            elif odd_even == 'even':
                # Extract even pages
                pages_to_extract = [(i, i) for i in range(total_pages) if i % 2 == 1]  # 0-based indexing
                if socketio:
                    socketio.emit('status_update', {
                        'status': 'processing',
                        'tool': 'split',
                        'log_entry': f'Will extract {len(pages_to_extract)} even pages'
                    })
            else:  # 'all'
                # Extract odd and even pages separately
                pages_to_extract = [
                    (0, total_pages - 1, 'odd'),  # All odd pages
                    (0, total_pages - 1, 'even')  # All even pages
                ]
                if socketio:
                    socketio.emit('status_update', {
                        'status': 'processing',
                        'tool': 'split',
                        'log_entry': 'Will extract odd and even pages as separate files'
                    })
        
        if not pages_to_extract:
            if socketio:
                socketio.emit('status_update', {
                    'status': 'error', 
                    'message': '❌ No valid pages to extract.',
                    'tool': 'split',
                    'log_entry': 'Error: No valid pages to extract'
                })
            return
        
        # Create output directory
        output_dir = os.path.join(OUTPUT_FOLDER, f"{name_without_ext}_split_{operation_id}")
        os.makedirs(output_dir, exist_ok=True)
        
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing',
                'tool': 'split',
                'log_entry': f'Created output directory: {os.path.basename(output_dir)}'
            })
        
        # Extract pages
        output_files = []
        
        for i, page_range_item in enumerate(pages_to_extract):
            if socketio:
                progress = int((i / len(pages_to_extract)) * 70) + 20  # Scale to 20-90%
                socketio.emit('status_update', {
                    'status': 'processing', 
                    'message': f'Processing page range {i+1} of {len(pages_to_extract)}',
                    'progress': progress,
                    'tool': 'split'
                })
            
            # Create a new PDF writer
            writer = PdfWriter()
            
            if len(page_range_item) == 2:
                start, end = page_range_item
                
                if socketio:
                    if start == end:
                        socketio.emit('status_update', {
                            'status': 'processing',
                            'tool': 'split',
                            'log_entry': f'Extracting page {start+1}'
                        })
                    else:
                        socketio.emit('status_update', {
                            'status': 'processing',
                            'tool': 'split',
                            'log_entry': f'Extracting pages {start+1} to {end+1}'
                        })
                
                # Add pages to writer
                for page_num in range(start, end + 1):
                    writer.add_page(reader.pages[page_num])
                
                # Create output filename
                if start == end:
                    output_filename = f"{name_without_ext}_page_{start + 1}.pdf"
                else:
                    output_filename = f"{name_without_ext}_pages_{start + 1}-{end + 1}.pdf"
            
            else:  # odd/even case
                start, end, page_type = page_range_item
                
                if socketio:
                    socketio.emit('status_update', {
                        'status': 'processing',
                        'tool': 'split',
                        'log_entry': f'Extracting {page_type} pages'
                    })
                
                # Add pages to writer
                pages_added = 0
                for page_num in range(start, end + 1):
                    if page_type == 'odd' and page_num % 2 == 0:  # 0-based indexing
                        writer.add_page(reader.pages[page_num])
                        pages_added += 1
                    elif page_type == 'even' and page_num % 2 == 1:  # 0-based indexing
                        writer.add_page(reader.pages[page_num])
                        pages_added += 1
                
                if socketio:
                    socketio.emit('status_update', {
                        'status': 'processing',
                        'tool': 'split',
                        'log_entry': f'Added {pages_added} {page_type} pages'
                    })
                
                # Create output filename
                output_filename = f"{name_without_ext}_{page_type}_pages.pdf"
            
            # Write the output PDF
            output_path = os.path.join(output_dir, output_filename)
            with open(output_path, 'wb') as f:
                writer.write(f)
            
            # Get file size
            file_size = os.path.getsize(output_path)
            file_size_str = format_file_size(file_size)
            
            if socketio:
                socketio.emit('status_update', {
                    'status': 'processing',
                    'tool': 'split',
                    'log_entry': f'Created: {output_filename} ({file_size_str})'
                })
            
            # Add to output files
            output_files.append({
                'path': output_path,
                'name': output_filename,
                'url': f'/download/{os.path.basename(output_dir)}/{output_filename}',
                'size': file_size_str
            })
        
        # Create ZIP file with all split PDFs
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing', 
                'message': 'Creating ZIP file...',
                'progress': 95,
                'tool': 'split',
                'log_entry': f'Creating ZIP archive with {len(output_files)} files'
            })
        
        zip_filename = f"{name_without_ext}_split_{operation_id}.zip"
        zip_path = os.path.join(OUTPUT_FOLDER, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file_info in output_files:
                zipf.write(file_info['path'], arcname=file_info['name'])
        
        # Get ZIP file size
        zip_size = os.path.getsize(zip_path)
        zip_size_str = format_file_size(zip_size)
        
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing',
                'tool': 'split',
                'log_entry': f'Created ZIP archive: {zip_filename} ({zip_size_str})'
            })
        
        # Prepare download links
        downloads = [
            {
                'name': zip_filename,
                'url': f'/download/{zip_filename}',
                'type': 'All Pages (ZIP)',
                'filename': zip_filename
            }
        ]
        
        # Add individual page downloads
        for file_info in output_files:
            downloads.append({
                'name': file_info['name'],
                'url': f'/download/{os.path.basename(output_dir)}/{file_info["name"]}',
                'type': file_info['name'],
                'filename': file_info['name']
            })
        
        if socketio:
            socketio.emit('status_update', {
                'status': 'success', 
                'message': f'✅ PDF split successfully into {len(output_files)} files!',
                'downloads': downloads,
                'filename': zip_filename,
                'pages': output_files,
                'tool': 'split',
                'log_entry': f'PDF split completed successfully: {len(output_files)} files created'
            })
    
    except Exception as e:
        error_msg = f"Error splitting PDF: {str(e)}"
        logger.error(error_msg)
        if socketio:
            socketio.emit('status_update', {
                'status': 'error', 
                'message': f'❌ Error splitting PDF: {str(e)}',
                'tool': 'split',
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