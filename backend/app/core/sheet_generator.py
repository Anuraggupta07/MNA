import gspread
from google.oauth2.service_account import Credentials
import logging
from typing import Dict, Any, List
from datetime import datetime
import json
from config import settings

logger = logging.getLogger(__name__)

class SheetWriter:
    """
    Handles writing structured data to Google Sheets
    """
    
    def __init__(self):
        self.gc = None
        self.spreadsheet = None
        self._initialize_google_sheets()
    
    def _initialize_google_sheets(self):
        """Initialize Google Sheets client"""
        try:
            if not settings.GOOGLE_SHEETS_CREDENTIALS_PATH:
                logger.warning("Google Sheets credentials not configured")
                return
            
            # Define the scope
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Load credentials
            credentials = Credentials.from_service_account_file(
                settings.GOOGLE_SHEETS_CREDENTIALS_PATH,
                scopes=scope
            )
            
            # Initialize client
            self.gc = gspread.authorize(credentials)
            
            # Open the spreadsheet
            if settings.GOOGLE_SHEETS_SPREADSHEET_ID:
                self.spreadsheet = self.gc.open_by_key(settings.GOOGLE_SHEETS_SPREADSHEET_ID)
            
            logger.info("Google Sheets client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {e}")
            self.gc = None
    
    def write_to_sheet(self, data: Dict[str, Any]) -> str:
        """
        Write structured M&A data to Google Sheets
        """
        if not self.gc or not self.spreadsheet:
            raise Exception("Google Sheets not properly initialized")
        
        try:
            # Ensure all required worksheets exist
            self._ensure_worksheets_exist()
            
            # Write data to each worksheet
            self._write_deal_summary(data.get("deal_summary", {}))
            self._write_financials(data.get("financials", {}))
            self._write_advisors(data.get("advisors", {}))
            self._write_power_plant_details(data.get("power_plant_details", {}))
            self._write_metadata(data.get("metadata", {}))
            
            # Return the spreadsheet URL
            return self.spreadsheet.url
            
        except Exception as e:
            logger.error(f"Error writing to Google Sheets: {e}")
            raise
    
    def _ensure_worksheets_exist(self):
        """Ensure all required worksheets exist with proper headers"""
        
        worksheets_config = {
            "Deal Summary": [
                "Deal ID", "Deal Name", "Deal Type", "Target Company", "Buyer", 
                "Seller", "Country", "Announcement Date", "Signing Date", 
                "Closing Date", "Deal Size (USD)", "Currency", "Status"
            ],
            "Financials": [
                "Deal ID", "Revenue", "EBITDA", "Enterprise Value", 
                "EV/EBITDA Multiple", "Debt Assumed", "Other Key Metrics"
            ],
            "Advisors": [
                "Deal ID", "Buy-Side Advisor", "Sell-Side Advisor", 
                "Legal Counsel (Buyer)", "Legal Counsel (Seller)", "Other Advisors"
            ],
            "Power Plant Details": [
                "Deal ID", "Project Name", "Location", "Capacity (MW)", 
                "Technology Type", "COD"
            ],
            "Metadata": [
                "Deal ID", "Source File Name", "Date Processed", 
                "Extraction Confidence", "QC Status", "QC Analyst", "QC Date"
            ]
        }
        
        # Get existing worksheet names
        existing_worksheets = [ws.title for ws in self.spreadsheet.worksheets()]
        
        for worksheet_name, headers in worksheets_config.items():
            if worksheet_name not in existing_worksheets:
                # Create new worksheet
                worksheet = self.spreadsheet.add_worksheet(
                    title=worksheet_name, 
                    rows=1000, 
                    cols=len(headers)
                )
                # Add headers
                worksheet.insert_row(headers, 1)
                logger.info(f"Created worksheet: {worksheet_name}")
            else:
                # Check if headers exist
                worksheet = self.spreadsheet.worksheet(worksheet_name)
                existing_headers = worksheet.row_values(1)
                if not existing_headers:
                    worksheet.insert_row(headers, 1)
                    logger.info(f"Added headers to existing worksheet: {worksheet_name}")
    
    def _write_deal_summary(self, data: Dict[str, Any]):
        """Write deal summary data"""
        worksheet = self.spreadsheet.worksheet("Deal Summary")
        
        row_data = [
            data.get("deal_id", ""),
            data.get("deal_name", ""),
            data.get("deal_type", ""),
            data.get("target_company", ""),
            data.get("buyer", ""),
            data.get("seller", ""),
            data.get("country", ""),
            data.get("announcement_date", ""),
            data.get("signing_date", ""),
            data.get("closing_date", ""),
            data.get("deal_size_usd", ""),
            data.get("currency", ""),
            data.get("status", "")
        ]
        
        # Find the next empty row
        next_row = len(worksheet.get_all_values()) + 1
        worksheet.insert_row(row_data, next_row)
        
        logger.info(f"Wrote deal summary data to row {next_row}")
    
    def _write_financials(self, data: Dict[str, Any]):
        """Write financials data"""
        worksheet = self.spreadsheet.worksheet("Financials")
        
        row_data = [
            data.get("deal_id", ""),  # This should come from metadata
            data.get("revenue", ""),
            data.get("ebitda", ""),
            data.get("enterprise_value", ""),
            data.get("ev_ebitda_multiple", ""),
            data.get("debt_assumed", ""),
            data.get("other_key_metrics", "")
        ]
        
        next_row = len(worksheet.get_all_values()) + 1
        worksheet.insert_row(row_data, next_row)
        
        logger.info(f"Wrote financials data to row {next_row}")
    
    def _write_advisors(self, data: Dict[str, Any]):
        """Write advisors data"""
        worksheet = self.spreadsheet.worksheet("Advisors")
        
        row_data = [
            data.get("deal_id", ""),
            data.get("buy_side_advisor", ""),
            data.get("sell_side_advisor", ""),
            data.get("legal_counsel_buyer", ""),
            data.get("legal_counsel_seller", ""),
            data.get("other_advisors", "")
        ]
        
        next_row = len(worksheet.get_all_values()) + 1
        worksheet.insert_row(row_data, next_row)
        
        logger.info(f"Wrote advisors data to row {next_row}")
    
    def _write_power