# PDF Toolkit

A full-featured PDF Toolkit web application similar to ILovePDF.com with automation and multiple document tools.

## Features

### PDF Manipulation
- **Merge PDFs**: Combine multiple PDF files into a single document
- **Split PDF**: Split PDF by page ranges or extract odd/even pages
- **Compress PDF**: Reduce PDF file size with different compression levels
- **Rotate PDF**: Rotate PDF pages by 90, 180, or 270 degrees

### PDF Conversion
- **PDF to Images**: Convert PDF pages to JPG, PNG, or TIFF images
- **Images to PDF**: Convert JPG, PNG, or other image formats to PDF
- **PDF to Word**: Convert PDF documents to editable Word files
- **PDF to Excel**: Extract tables from PDF to Excel spreadsheets
- **PDF to PowerPoint**: Convert PDF to PowerPoint presentations
- **Word to PDF**: Convert Word documents to PDF
- **Excel to PDF**: Convert Excel spreadsheets to PDF
- **PowerPoint to PDF**: Convert PowerPoint presentations to PDF

### PDF Content Extraction
- **Extract Text**: Extract text content from PDF documents
- **OCR (Text Recognition)**: Extract text from scanned documents and images

### PDF Security
- **Protect PDF**: Add password protection to PDF files
- **Unlock PDF**: Remove password protection from PDF files

### PDF Editing
- **Add Watermark**: Add text or image watermarks to PDF files

## Tech Stack

- **Frontend**: HTML, CSS, JavaScript with modern animations
- **Backend**: Python with Flask
- **PDF Processing**: PyPDF2, pdf2image, img2pdf, pdfminer, and more
- **Real-time Updates**: Socket.IO for live progress updates
- **Email Integration**: Support for sending processed files via email

## Installation

### Local Development

1. Clone the repository:
```
git clone https://github.com/yourusername/pdf-toolkit.git
cd pdf-toolkit
```

2. Create a virtual environment:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Run the application:
```
python app.py
```

5. Open your browser and navigate to:
```
http://localhost:5000
```

### Deployment on Vercel

1. Fork or clone this repository to your GitHub account.

2. Sign in to [Vercel](https://vercel.com) using your GitHub account.

3. Click on "New Project" and import your GitHub repository.

4. Configure the project:
   - Framework Preset: Other
   - Root Directory: ./
   - Build Command: None
   - Output Directory: None

5. Add the following environment variables if needed:
   - EMAIL_HOST
   - EMAIL_PORT
   - EMAIL_USER
   - EMAIL_PASSWORD
   - EMAIL_FROM

6. Click "Deploy" and wait for the deployment to complete.

7. Your PDF Toolkit is now live on Vercel!

## Required Dependencies

- Flask
- Flask-SocketIO
- PyPDF2
- pdf2image
- img2pdf
- pdfminer.six
- Pillow
- python-docx
- tabula-py
- pandas
- python-pptx
- reportlab
- pytesseract (for OCR)

## Features

- **Responsive Design**: Works on desktop and mobile devices
- **Dark/Light Mode**: Toggle between dark and light themes
- **Real-time Updates**: See progress in real-time
- **Drag & Drop**: Easy file uploading with drag and drop
- **File Reordering**: Reorder files before merging
- **Email Integration**: Send processed files via email
- **Auto Cleanup**: Files are automatically deleted after 15 minutes

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [PyPDF2](https://github.com/py-pdf/PyPDF2) for PDF manipulation
- [pdf2image](https://github.com/Belval/pdf2image) for PDF to image conversion
- [img2pdf](https://github.com/josch/img2pdf) for image to PDF conversion
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [Socket.IO](https://socket.io/) for real-time communication