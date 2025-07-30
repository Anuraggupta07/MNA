from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import tempfile
import logging
from typing import List, Dict, Any
import json
from datetime import datetime

# Import our custom modules
from models.document_processor import DocumentProcessor
from models.ai_orchestrator import AIOrchestrator
from models.sheet_writer import SheetWriter
from utils.classifier import DocumentClassifier
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="M&A Entry Tool API",
    description="Automated M&A document processing and data extraction",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processors
document_processor = DocumentProcessor()
ai_orchestrator = AIOrchestrator()
sheet_writer = SheetWriter()
classifier = DocumentClassifier()

@app.get("/")
async def root():
    return {"message": "M&A Entry Tool API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a PDF document
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        logger.info(f"Processing file: {file.filename}")
        
        # Step 1: Extract text from PDF
        extracted_text = document_processor.extract_text(tmp_file_path)
        
        # Step 2: Classify document type
        doc_type = classifier.classify_document(extracted_text)
        
        # Step 3: Process with AI
        structured_data = ai_orchestrator.process_document(extracted_text, doc_type)
        
        # Step 4: Generate processing ID
        processing_id = f"proc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
        return {
            "processing_id": processing_id,
            "filename": file.filename,
            "doc_type": doc_type,
            "extracted_data": structured_data,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        # Clean up temporary file if it exists
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.post("/export-to-sheets")
async def export_to_sheets(data: Dict[str, Any]):
    """
    Export processed data to Google Sheets
    """
    try:
        # Validate required fields
        if 'extracted_data' not in data:
            raise HTTPException(status_code=400, detail="Missing extracted_data")
        
        # Write to Google Sheets
        sheet_url = sheet_writer.write_to_sheet(data['extracted_data'])
        
        return {
            "status": "success",
            "sheet_url": sheet_url,
            "message": "Data exported to Google Sheets successfully"
        }
        
    except Exception as e:
        logger.error(f"Error exporting to sheets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting to sheets: {str(e)}")

@app.get("/supported-formats")
async def get_supported_formats():
    """
    Get list of supported document formats and types
    """
    return {
        "file_formats": ["pdf"],
        "document_types": [
            "press_release",
            "quarterly_report", 
            "annual_report",
            "investor_deck",
            "other"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)