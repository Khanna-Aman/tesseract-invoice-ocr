#!/usr/bin/env python3
"""
Assignment-compliant invoice scanner using OCR
Converts scanned invoices (PDF/images) to structured CSV/JSON dataset

Usage:
    python scan2csv.py --in_dir "input_folder" --out_csv "output.csv" --out_json "output.json"
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime
import re

# OCR and image processing
import cv2
import numpy as np
from PIL import Image
import fitz  # PyMuPDF
import pytesseract
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InvoiceScanner:
    """Assignment-compliant invoice scanner"""
    
    def __init__(self, tesseract_path: str = None):
        """Initialize scanner with Tesseract path"""
        self.supported_formats = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.txt'}

        # Set Tesseract path
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        elif os.path.exists(r'D:\Tesseract-OCR\tesseract.exe'):
            pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract-OCR\tesseract.exe'
        elif os.path.exists(r'C:\Program Files\Tesseract-OCR\tesseract.exe'):
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

        logger.info("Invoice scanner initialized")
    
    def scan_directory(self, input_dir: str) -> List[str]:
        """Scan directory for supported invoice files"""
        files = []
        input_path = Path(input_dir)
        
        if not input_path.exists():
            logger.error(f"Input directory not found: {input_dir}")
            return files
        
        for file_path in input_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                files.append(str(file_path))
        
        logger.info(f"Found {len(files)} supported files")
        return files
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Enhanced image preprocessing for better OCR"""
        img_array = np.array(image)
        
        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Apply denoising and enhancement
        denoised = cv2.fastNlMeansDenoising(gray)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        thresh = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        return Image.fromarray(thresh)
    
    def perform_ocr(self, file_path: str) -> Optional[str]:
        """Perform OCR on file with error handling"""
        try:
            if not os.path.exists(file_path):
                return None

            # Handle text files directly
            if file_path.lower().endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()

            # Handle PDF files
            if file_path.lower().endswith('.pdf'):
                doc = fitz.open(file_path)
                if len(doc) == 0:
                    doc.close()
                    return None

                page = doc[0]
                mat = fitz.Matrix(3.0, 3.0)  # High resolution
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                doc.close()
            else:
                # Handle image files
                image = Image.open(file_path)

            # Preprocess image
            processed_image = self.preprocess_image(image)

            # Perform OCR
            config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(processed_image, config=config)

            return text.strip() if text.strip() else None

        except Exception as e:
            logger.error(f"OCR failed for {file_path}: {e}")
            return None
    
    def extract_vendor_name(self, text: str) -> str:
        """Extract vendor name from OCR text"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Look for company patterns
        patterns = [
            r'([A-Z][A-Za-z\s&\.]+(?:LIMITED|LTD|COMPANY|CORP|INC))',
            r'([A-Z][A-Za-z\s&\.]{10,50})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip().title()
        
        # Fallback to first substantial line
        for line in lines[:5]:
            if len(line) > 10 and not re.match(r'^[\d\s\-\.\,\/]+$', line):
                return line.title()
        
        return "UNKNOWN_VENDOR"
    
    def extract_invoice_number(self, text: str) -> str:
        """Extract invoice number from OCR text"""
        patterns = [
            r'INVOICE[#\s]*:?\s*([A-Z0-9\-]{3,20})',
            r'INV[#\s]*:?\s*([A-Z0-9\-]{3,20})',
            r'NO[#\s]*:?\s*([A-Z0-9\-]{3,20})',
            r'(?:^|\s)([A-Z]{2,4}-\d{4,8})(?:\s|$)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                clean_match = match.strip()
                if 3 <= len(clean_match) <= 20 and not re.match(r'^\d{8}$', clean_match):
                    return clean_match
        
        return "UNKNOWN_INVOICE_NO"
    
    def extract_date(self, text: str) -> str:
        """Extract invoice date from OCR text"""
        patterns = [
            r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})',
            r'(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})',
            r'([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if any(year in match for year in ['2020', '2021', '2022', '2023', '2024']):
                    return match.strip()
        
        return "UNKNOWN_DATE"
    
    def extract_currency(self, text: str) -> str:
        """Extract currency from OCR text"""
        if 'USD' in text or '$' in text:
            return 'USD'
        elif 'GBP' in text or '£' in text:
            return 'GBP'
        elif 'EUR' in text or '€' in text:
            return 'EUR'
        else:
            return 'USD'  # Default
    
    def extract_line_items(self, text: str) -> List[Dict[str, Any]]:
        """Extract line items table from OCR text"""
        line_items = []
        lines = text.split('\n')
        
        # Look for table-like structures
        for i, line in enumerate(lines):
            # Simple pattern matching for line items
            # Look for lines with description and amount
            amount_match = re.search(r'([\d,]+\.\d{2})', line)
            if amount_match and len(line.strip()) > 10:
                # Extract description (everything before the amount)
                amount_pos = line.find(amount_match.group(1))
                description = line[:amount_pos].strip()
                amount = float(amount_match.group(1).replace(',', ''))
                
                if description and amount > 0:
                    line_items.append({
                        'description': description,
                        'quantity': 1,  # Default
                        'unit_price': amount,
                        'amount': amount
                    })
        
        return line_items
    
    def extract_grand_total(self, text: str) -> float:
        """Extract grand total from OCR text"""
        patterns = [
            r'TOTAL[:\s]*([\d,]+\.?\d{0,2})',
            r'GRAND\s*TOTAL[:\s]*([\d,]+\.?\d{0,2})',
            r'([\d,]+\.\d{2})(?=\s*$)',  # End of line amounts
        ]
        
        amounts = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                try:
                    amount = float(match.replace(',', ''))
                    if 100 <= amount <= 50000000:  # Reasonable range
                        amounts.append(amount)
                except:
                    pass
        
        return max(amounts) if amounts else 0.0
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Process single invoice file"""
        filename = os.path.basename(file_path)
        logger.info(f"Processing: {filename}")
        
        # Perform OCR
        ocr_text = self.perform_ocr(file_path)
        if not ocr_text:
            logger.warning(f"No text extracted from {filename}")
            return self._create_error_result(filename, "OCR_FAILED")
        
        # Extract data
        try:
            result = {
                'filename': filename,
                'vendor_name': self.extract_vendor_name(ocr_text),
                'invoice_number': self.extract_invoice_number(ocr_text),
                'invoice_date': self.extract_date(ocr_text),
                'currency': self.extract_currency(ocr_text),
                'line_items': self.extract_line_items(ocr_text),
                'grand_total': self.extract_grand_total(ocr_text),
                'raw_ocr_text': ocr_text,
                'processing_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Successfully processed {filename}")
            return result
            
        except Exception as e:
            logger.error(f"Data extraction failed for {filename}: {e}")
            return self._create_error_result(filename, f"EXTRACTION_ERROR: {e}")
    
    def _create_error_result(self, filename: str, error: str) -> Dict[str, Any]:
        """Create error result structure"""
        return {
            'filename': filename,
            'vendor_name': 'ERROR',
            'invoice_number': 'ERROR',
            'invoice_date': 'ERROR',
            'currency': 'USD',
            'line_items': [],
            'grand_total': 0.0,
            'raw_ocr_text': '',
            'processing_timestamp': datetime.now().isoformat(),
            'error': error
        }
    
    def export_to_csv(self, results: List[Dict[str, Any]], output_csv: str):
        """Export results to CSV format as per assignment requirements"""
        # Create invoices_header.csv (one row per invoice)
        header_data = []
        lines_data = []
        
        for result in results:
            # Header data
            header_row = {
                'filename': result['filename'],
                'vendor_name': result['vendor_name'],
                'invoice_number': result['invoice_number'],
                'invoice_date': result['invoice_date'],
                'currency': result['currency'],
                'grand_total': result['grand_total'],
                'processing_timestamp': result['processing_timestamp']
            }
            header_data.append(header_row)
            
            # Line items data
            for i, item in enumerate(result['line_items']):
                line_row = {
                    'filename': result['filename'],  # Foreign key to header
                    'line_number': i + 1,
                    'description': item['description'],
                    'quantity': item['quantity'],
                    'unit_price': item['unit_price'],
                    'amount': item['amount']
                }
                lines_data.append(line_row)
        
        # Save header CSV
        header_df = pd.DataFrame(header_data)
        header_csv = output_csv.replace('.csv', '_header.csv')
        header_df.to_csv(header_csv, index=False)
        logger.info(f"Header data saved to: {header_csv}")
        
        # Save lines CSV
        if lines_data:
            lines_df = pd.DataFrame(lines_data)
            lines_csv = output_csv.replace('.csv', '_lines.csv')
            lines_df.to_csv(lines_csv, index=False)
            logger.info(f"Line items saved to: {lines_csv}")
        
        return header_csv, lines_csv if lines_data else None
    
    def export_to_json(self, results: List[Dict[str, Any]], output_json: str):
        """Export raw results to JSON for audit"""
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Raw data saved to: {output_json}")


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description='Convert scanned invoices to CSV/JSON')
    parser.add_argument('--in_dir', required=True, help='Input directory containing invoice files')
    parser.add_argument('--out_csv', required=True, help='Output CSV file path')
    parser.add_argument('--out_json', required=True, help='Output JSON file path')
    parser.add_argument('--tesseract_path', help='Path to Tesseract executable')
    
    args = parser.parse_args()
    
    # Initialize scanner
    scanner = InvoiceScanner(tesseract_path=args.tesseract_path)
    
    # Scan directory
    files = scanner.scan_directory(args.in_dir)
    if not files:
        logger.error("No supported files found")
        sys.exit(1)
    
    # Process files
    results = []
    for file_path in files:
        result = scanner.process_file(file_path)
        results.append(result)
    
    # Export results
    header_csv, lines_csv = scanner.export_to_csv(results, args.out_csv)
    scanner.export_to_json(results, args.out_json)
    
    # Summary
    successful = len([r for r in results if 'error' not in r])
    logger.info(f"Processing complete: {successful}/{len(results)} files successful")
    logger.info(f"Output files: {header_csv}, {lines_csv or 'No line items'}, {args.out_json}")


if __name__ == "__main__":
    main()
