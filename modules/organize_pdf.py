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
organize_bp = Blueprint('organize', __name__)

def register_routes(app, socketio):
    """Register routes with the Flask app"""
    app.register_blueprint(organize_bp)
    
    @app.route('/rotate', methods=['POST'])
    def rotate_route():
        if 'pdf' not in request.files:
            socketio.emit('status_update', {
                'status': 'error', 
                'message': '⚠️ No PDF file was uploaded.',
                'tool': 'rotate'
            })
            return jsonify({'status': 'error', 'message': 'No PDF file was uploaded.'})
        
        pdf_file = request.files['pdf']
        if pdf_file.filename == '':
            socketio.emit('status_update', {
                'status': 'error', 
                'message': '⚠️ No PDF file was selected.',
                'tool': 'rotate'
            })
            return jsonify({'status': 'error', 'message': 'No PDF file was selected.'})
        
        # Get rotation parameters
        angle = int(request.form.get('angle', '90'))
        pages_option = request.form.get('pages', 'all')
        page_range = request.form.get('rotate_range', '')
        
        # Save the uploaded file
        filename = secure_filename(pdf_file.filename)
        from app import UPLOAD_FOLDER
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        pdf_file.save(file_path)
        
        # Start a background thread for processing
        thread = socketio.start_background_task(
            rotate_pdf, 
            file_path=file_path,
            angle=angle,
            pages_option=pages_option,
            page_range=page_range,
            socketio=socketio
        )
        
        # Return immediately with a processing message
        return jsonify({'status': 'processing', 'message': 'Rotating PDF...'})
    
    @app.route('/watermark', methods=['POST'])
    def watermark_route():
        if 'pdf' not in request.files:
            socketio.emit('status_update', {
                'status': 'error', 
                'message': '⚠️ No PDF file was uploaded.',
                'tool': 'watermark'
            })
            return jsonify({'status': 'error', 'message': 'No PDF file was uploaded.'})
        
        pdf_file = request.files['pdf']
        if pdf_file.filename == '':
            socketio.emit('status_update', {
                'status': 'error', 
                'message': '⚠️ No PDF file was selected.',
                'tool': 'watermark'
            })
            return jsonify({'status': 'error', 'message': 'No PDF file was selected.'})
        
        # Get watermark parameters
        watermark_type = request.form.get('watermark_type', 'text')
        watermark_text = request.form.get('watermark_text', '')
        opacity = int(request.form.get('opacity', '30'))
        position = request.form.get('position', 'middle-center')
        
        # Check if watermark image was uploaded
        watermark_image_path = None
        if watermark_type == 'image' and 'watermark_image' in request.files:
            watermark_image = request.files['watermark_image']
            if watermark_image.filename != '':
                image_filename = secure_filename(watermark_image.filename)
                from app import UPLOAD_FOLDER
                watermark_image_path = os.path.join(UPLOAD_FOLDER, image_filename)
                watermark_image.save(watermark_image_path)
        
        # Save the uploaded PDF file
        filename = secure_filename(pdf_file.filename)
        from app import UPLOAD_FOLDER
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        pdf_file.save(file_path)
        
        # Start a background thread for processing
        thread = socketio.start_background_task(
            add_watermark, 
            file_path=file_path,
            watermark_type=watermark_type,
            watermark_text=watermark_text,
            watermark_image_path=watermark_image_path,
            opacity=opacity,
            position=position,
            socketio=socketio
        )
        
        # Return immediately with a processing message
        return jsonify({'status': 'processing', 'message': 'Adding watermark...'})

def rotate_pdf(file_path, angle=90, pages_option='all', page_range='', socketio=None):
    """Rotate PDF pages"""
    if socketio:
        socketio.emit('status_update', {
            'status': 'processing', 
            'message': 'Starting PDF rotation process...',
            'tool': 'rotate'
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
                'tool': 'rotate'
            })
        
        reader = PdfReader(file_path)
        writer = PdfWriter()
        
        total_pages = len(reader.pages)
        
        if total_pages == 0:
            if socketio:
                socketio.emit('status_update', {
                    'status': 'error', 
                    'message': '❌ The PDF file is empty.',
                    'tool': 'rotate'
                })
            return
        
        # Determine which pages to rotate
        pages_to_rotate = []
        
        if pages_option == 'all':
            pages_to_rotate = list(range(total_pages))
        elif pages_option == 'custom' and page_range:
            # Parse page range
            ranges = page_range.split(',')
            
            for r in ranges:
                if '-' in r:
                    start, end = map(int, r.split('-'))
                    # Adjust for 0-based indexing
                    start = max(1, start) - 1
                    end = min(total_pages, end) - 1
                    pages_to_rotate.extend(range(start, end + 1))
                else:
                    try:
                        page = int(r) - 1  # Adjust for 0-based indexing
                        if 0 <= page < total_pages:
                            pages_to_rotate.append(page)
                    except ValueError:
                        continue
        
        if not pages_to_rotate:
            if socketio:
                socketio.emit('status_update', {
                    'status': 'error', 
                    'message': '❌ No valid pages to rotate.',
                    'tool': 'rotate'
                })
            return
        
        # Rotate pages
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing', 
                'message': 'Rotating pages...',
                'progress': 50,
                'tool': 'rotate'
            })
        
        # Add all pages to writer, rotating specified pages
        for i in range(total_pages):
            page = reader.pages[i]
            
            if i in pages_to_rotate:
                page.rotate(angle)
            
            writer.add_page(page)
        
        # Create output file
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing', 
                'message': 'Creating rotated PDF...',
                'progress': 90,
                'tool': 'rotate'
            })
        
        output_filename = f"{name_without_ext}_rotated_{operation_id}.pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        # Prepare download links
        downloads = [
            {
                'name': output_filename,
                'url': f'/download/{output_filename}',
                'type': 'Rotated PDF',
                'filename': output_filename
            }
        ]
        
        if socketio:
            socketio.emit('status_update', {
                'status': 'success', 
                'message': '✅ PDF rotated successfully!',
                'downloads': downloads,
                'tool': 'rotate'
            })
    
    except Exception as e:
        logger.error(f"Error rotating PDF: {str(e)}")
        if socketio:
            socketio.emit('status_update', {
                'status': 'error', 
                'message': f'❌ Error rotating PDF: {str(e)}',
                'tool': 'rotate'
            })

def add_watermark(file_path, watermark_type='text', watermark_text='CONFIDENTIAL', 
                 watermark_image_path=None, opacity=30, position='middle-center', socketio=None):
    """Add watermark to PDF"""
    if socketio:
        socketio.emit('status_update', {
            'status': 'processing', 
            'message': 'Starting watermark process...',
            'tool': 'watermark'
        })
    
    try:
        # Get paths
        from app import OUTPUT_FOLDER, TEMP_FOLDER
        
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
                'tool': 'watermark'
            })
        
        reader = PdfReader(file_path)
        writer = PdfWriter()
        
        total_pages = len(reader.pages)
        
        if total_pages == 0:
            if socketio:
                socketio.emit('status_update', {
                    'status': 'error', 
                    'message': '❌ The PDF file is empty.',
                    'tool': 'watermark'
                })
            return
        
        # Create watermark
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing', 
                'message': 'Creating watermark...',
                'progress': 40,
                'tool': 'watermark'
            })
        
        # Create watermark PDF
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.lib.colors import Color
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import math
        
        # Create temp file for watermark
        watermark_pdf_path = os.path.join(TEMP_FOLDER, f"watermark_{operation_id}.pdf")
        
        # Get page size from first page
        page = reader.pages[0]
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)
        
        # Create canvas with page size
        c = canvas.Canvas(watermark_pdf_path, pagesize=(page_width, page_height))
        
        # Set opacity
        opacity_float = opacity / 100.0
        c.setFillAlpha(opacity_float)
        c.setStrokeAlpha(opacity_float)
        
        # Calculate position
        x, y = 0, 0
        
        if position.startswith('top'):
            y = page_height * 0.8
        elif position.startswith('middle'):
            y = page_height * 0.5
        elif position.startswith('bottom'):
            y = page_height * 0.2
        
        if position.endswith('left'):
            x = page_width * 0.2
        elif position.endswith('center'):
            x = page_width * 0.5
        elif position.endswith('right'):
            x = page_width * 0.8
        
        # Add watermark
        if watermark_type == 'text' and watermark_text:
            # Set font and size
            font_size = min(page_width, page_height) * 0.1
            c.setFont("Helvetica", font_size)
            c.setFillColorRGB(0, 0, 0)  # Black color
            
            # Draw text
            c.saveState()
            c.translate(x, y)
            c.rotate(45)  # Rotate text 45 degrees
            text_width = c.stringWidth(watermark_text, "Helvetica", font_size)
            c.drawString(-text_width/2, 0, watermark_text)
            c.restoreState()
        
        elif watermark_type == 'image' and watermark_image_path:
            # Draw image
            from PIL import Image
            img = Image.open(watermark_image_path)
            img_width, img_height = img.size
            
            # Scale image to fit page (max 30% of page width)
            max_width = page_width * 0.3
            scale = min(1, max_width / img_width)
            
            # Calculate dimensions
            width = img_width * scale
            height = img_height * scale
            
            # Draw image
            c.drawImage(watermark_image_path, x - width/2, y - height/2, width=width, height=height)
        
        c.save()
        
        # Create watermark reader
        watermark_reader = PdfReader(watermark_pdf_path)
        watermark_page = watermark_reader.pages[0]
        
        # Add watermark to each page
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing', 
                'message': 'Adding watermark to pages...',
                'progress': 60,
                'tool': 'watermark'
            })
        
        for i in range(total_pages):
            page = reader.pages[i]
            page.merge_page(watermark_page)
            writer.add_page(page)
        
        # Create output file
        if socketio:
            socketio.emit('status_update', {
                'status': 'processing', 
                'message': 'Creating watermarked PDF...',
                'progress': 90,
                'tool': 'watermark'
            })
        
        output_filename = f"{name_without_ext}_watermarked_{operation_id}.pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        # Prepare download links
        downloads = [
            {
                'name': output_filename,
                'url': f'/download/{output_filename}',
                'type': 'Watermarked PDF',
                'filename': output_filename
            }
        ]
        
        if socketio:
            socketio.emit('status_update', {
                'status': 'success', 
                'message': '✅ Watermark added successfully!',
                'downloads': downloads,
                'tool': 'watermark'
            })
    
    except Exception as e:
        logger.error(f"Error adding watermark: {str(e)}")
        if socketio:
            socketio.emit('status_update', {
                'status': 'error', 
                'message': f'❌ Error adding watermark: {str(e)}',
                'tool': 'watermark'
            })