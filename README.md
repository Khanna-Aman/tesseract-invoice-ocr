# Invoice Scanner - scan2csv.py

A Python utility that converts scanned invoices (PDF, images, or text files) into structured CSV/JSON data using OCR technology.

## Problem Statement

Manual processing of scanned invoices is time-consuming and error-prone. This tool automates the extraction of key invoice information including vendor details, line items, and totals from PDF documents, images, and text files, outputting structured data for further processing.

## Approach

The solution uses a robust OCR-based approach with Tesseract OCR:

1. **Document Processing**: PDF files are converted to high-resolution images using PyMuPDF
2. **Image Enhancement**: Images are preprocessed with denoising and adaptive thresholding for better OCR accuracy
3. **OCR Processing**: Tesseract OCR extracts text with optimized configurations for invoice documents
4. **Data Extraction**: Smart parsing logic uses regex patterns to extract structured invoice data
5. **Validation & Output**: Results are validated and exported to CSV and JSON formats

### Key Features

- Multi-format Support: Processes PDF files, images (PNG, JPG, JPEG, TIFF, BMP), and text files
- Intelligent Extraction: Extracts vendor name, invoice number, date, currency, and total amounts
- Image Enhancement: Advanced preprocessing for improved OCR accuracy
- Robust Error Handling: Graceful handling of corrupted files, missing fields, and OCR failures
- Dual Output Formats: Generates both CSV files and JSON with extracted data
- Tesseract Integration: Uses industry-standard Tesseract OCR engine
- Smart Pattern Matching: Advanced regex patterns for accurate data extraction

## Flow Diagram

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Input Files   │───▶│  File Validation │───▶│   Load Image    │
│ (PDF/Images)    │    │   & Filtering    │    │   Processing    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Data Validation│◀───│  Data Extraction │◀───│  Dolphin OCR    │
│   & Cleaning    │    │    & Parsing     │    │   Processing    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐    ┌──────────────────┐
│   CSV Output    │    │   JSON Output    │
│ (Header/Lines)  │    │  (Raw + Meta)    │
└─────────────────┘    └──────────────────┘
```

## Installation

1. **Clone or download this repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Tesseract OCR**:
   - Download from: https://github.com/UB-Mannheim/tesseract/wiki
   - Install the Windows executable to default location
   - Or install to custom location and update the path in the code

## Usage

### Basic Usage

```bash
# Process all invoices in a directory
python scan2csv.py --in_dir "Sample Documents/Sample Documents" --out_csv results.csv --out_json results.json

# Process with custom Tesseract path
python scan2csv.py --in_dir invoices --out_csv results.csv --out_json results.json --tesseract_path "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### Command Line Arguments

- `--in_dir`: Required. Directory containing invoice files (PDF, PNG, JPG, etc.)
- `--out_csv`: Output CSV file path (creates `_header.csv` and `_lines.csv` variants)
- `--out_json`: Output JSON file path for raw OCR results
- `--tesseract_path`: Optional. Path to Tesseract executable if not in default location

### Output Format

#### CSV Files

**invoices_header.csv** - One row per invoice:
```csv
invoice_id,file_name,vendor_name,invoice_number,invoice_date,currency,grand_total,line_items_count,source_file
1,invoice1.pdf,ACME Corp,INV-001,2024-01-15,USD,1250.00,3,/path/to/invoice1.pdf
```

**invoices_lines.csv** - One row per line item:
```csv
invoice_id,line_number,description,quantity,unit_price,amount
1,1,Product A,2,100.00,200.00
1,2,Product B,1,150.00,150.00
```

#### JSON File

Contains raw OCR results, extracted data, and validation metadata:
```json
{
  "metadata": {
    "total_invoices": 5,
    "processing_timestamp": "2024-01-15T10:30:00",
    "tool_version": "1.0.0"
  },
  "invoices": [
    {
      "vendor_name": "ACME Corp",
      "invoice_number": "INV-001",
      "invoice_date": "2024-01-15",
      "currency": "USD",
      "grand_total": "1250.00",
      "line_items": [...],
      "validation": {
        "completeness_score": 0.85,
        "is_valid": true,
        "missing_fields": []
      },
      "raw_ocr_text": "..."
    }
  ]
}
```

## Sample Run

The repository includes three sample invoices and their processing results:

### Sample Invoices
- `sample_invoices/invoice_001.txt`: ACME Consulting LLC - Business consulting services ($6,510.00)
- `sample_invoices/invoice_002.txt`: Tech Supplies Inc - Computer equipment order ($3,147.05)
- `sample_invoices/invoice_003.txt`: Global Solutions Group - Professional services ($11,500.00)

### Sample Results
- `sample_results_header.csv`: Invoice header data (3 invoices processed)
- `sample_results_lines.csv`: Line item details (7 line items extracted)
- `sample_results.json`: Complete raw data with OCR text for audit

The sample demonstrates successful extraction of vendor names, invoice numbers, dates, currencies, line items, and totals from diverse invoice formats.

## Performance

- **Processing Speed**: < 3 minutes for typical invoice batches on CPU
- **GPU Acceleration**: Significantly faster processing with CUDA-compatible GPUs
- **Memory Usage**: Optimized for batch processing with configurable memory management

## Error Handling

The tool includes comprehensive error handling for:
- Corrupted or unreadable PDF files
- Invalid image formats
- Missing or incomplete invoice data
- OCR processing failures
- Network issues during model download

## Requirements

- Python >= 3.9
- Tesseract OCR executable
- See `requirements.txt` for complete dependency list

## License

MIT License - See LICENSE file for details.

## Troubleshooting

### Common Issues

1. **Model Download Fails**: Ensure internet connection and try manual download
2. **GPU Not Detected**: Install CUDA-compatible PyTorch version
3. **PDF Processing Errors**: Ensure PyMuPDF is properly installed
4. **Memory Issues**: Reduce batch size or use CPU mode

### Getting Help

For issues or questions:
1. Check the log files for detailed error messages
2. Ensure all dependencies are properly installed
3. Verify input file formats are supported
4. Try processing a single file first to isolate issues
