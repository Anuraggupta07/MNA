import openai
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
import re
from config import settings

logger = logging.getLogger(__name__)

class AIOrchestrator:
    """
    Orchestrates AI models for data extraction from documents
    """
    
    def __init__(self):
        # Initialize OpenAI client
        openai.api_key = settings.OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Define the M&A data schema
        self.mna_schema = {
            "deal_summary": {
                "deal_name": "",
                "deal_type": "",  # Asset/Corporate
                "target_company": "",
                "buyer": "",
                "seller": "",
                "country": "",
                "announcement_date": "",
                "signing_date": "",
                "closing_date": "",
                "deal_size_usd": "",
                "currency": "",
                "status": ""
            },
            "financials": {
                "revenue": "",
                "ebitda": "",
                "enterprise_value": "",
                "ev_ebitda_multiple": "",
                "debt_assumed": "",
                "other_key_metrics": ""
            },
            "advisors": {
                "buy_side_advisor": "",
                "sell_side_advisor": "",
                "legal_counsel_buyer": "",
                "legal_counsel_seller": "",
                "other_advisors": ""
            },
            "power_plant_details": {
                "project_name": "",
                "location": "",
                "capacity_mw": "",
                "technology_type": "",
                "cod": ""
            },
            "metadata": {
                "deal_id": "",
                "source_file_name": "",
                "date_processed": datetime.now().isoformat(),
                "extraction_confidence": ""
            }
        }
    
    def process_document(self, text: str, doc_type: str) -> Dict[str, Any]:
        """
        Process document text and extract structured M&A data
        """
        try:
            # Create the extraction prompt
            extraction_prompt = self._create_extraction_prompt(text, doc_type)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=settings.PRIMARY_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert M&A analyst. Extract structured data from documents with high accuracy. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": extraction_prompt
                    }
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            # Parse the response
            extracted_data = self._parse_ai_response(response.choices[0].message.content)
            
            # Validate and clean the data
            cleaned_data = self._validate_and_clean_data(extracted_data)
            
            # Add metadata
            cleaned_data["metadata"]["date_processed"] = datetime.now().isoformat()
            cleaned_data["metadata"]["deal_id"] = self._generate_deal_id(cleaned_data)
            
            logger.info("Successfully processed document with AI")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Error in AI processing: {e}")
            # Return empty schema with error info
            error_data = self.mna_schema.copy()
            error_data["metadata"]["extraction_error"] = str(e)
            return error_data
    
    def _create_extraction_prompt(self, text: str, doc_type: str) -> str:
        """Create the extraction prompt for the AI model"""
        
        prompt = f"""
Extract M&A deal information from this {doc_type} document. Return data in the exact JSON format specified below.

Document Text:
{text[:4000]}  # Truncate to avoid token limits

Required JSON Format:
{json.dumps(self.mna_schema, indent=2)}

Instructions:
1. Extract only information that is explicitly stated in the document
2. Use "N/A" for fields that cannot be determined
3. For dates, use format: YYYY-MM-DD
4. For monetary values, include only numbers (no currency symbols)
5. For deal_type, use "Asset" or "Corporate"
6. For technology_type, use: Solar, Wind, BESS, Hydro, Gas, etc.
7. Return only valid JSON, no additional text

JSON Response:
"""
        return prompt
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response and extract JSON"""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # If no JSON found, try parsing the entire response
                return json.loads(response_text)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"Response was: {response_text}")
            return self.mna_schema.copy()
    
    def _validate_and_clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted data"""
        cleaned_data = self.mna_schema.copy()
        
        # Merge extracted data with schema
        for section, fields in cleaned_data.items():
            if section in data and isinstance(data[section], dict):
                for field, default_value in fields.items():
                    if field in data[section]:
                        value = data[section][field]
                        # Clean the value
                        if isinstance(value, str):
                            value = value.strip()
                            if value.lower() in ['', 'n/a', 'null', 'none']:
                                value = ""
                        cleaned_data[section][field] = value
        
        # Validate dates
        cleaned_data = self._validate_dates(cleaned_data)
        
        # Validate monetary values
        cleaned_data = self._validate_monetary_values(cleaned_data)
        
        return cleaned_data
    
    def _validate_dates(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate date formats"""
        date_fields = [
            ("deal_summary", "announcement_date"),
            ("deal_summary", "signing_date"),
            ("deal_summary", "closing_date"),
            ("power_plant_details", "cod")
        ]
        
        for section, field in date_fields:
            if section in data and field in data[section]:
                date_str = data[section][field]
                if date_str and date_str != "N/A":
                    try:
                        # Try to parse and reformat the date
                        # This is a simple validation - you might want to make it more robust
                        if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                            continue  # Already in correct format
                        else:
                            # Try to parse various formats and convert to YYYY-MM-DD
                            # For now, leave as-is if it doesn't match
                            pass
                    except:
                        data[section][field] = ""
        
        return data
    
    def _validate_monetary_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean monetary values"""
        monetary_fields = [
            ("deal_summary", "deal_size_usd"),
            ("financials", "revenue"),
            ("financials", "ebitda"),
            ("financials", "enterprise_value"),
            ("financials", "debt_assumed")
        ]
        
        for section, field in monetary_fields:
            if section in data and field in data[section]:
                value = data[section][field]
                if value and value != "N/A":
                    # Remove currency symbols and clean
                    cleaned_value = re.sub(r'[^\d.]', '', str(value))
                    data[section][field] = cleaned_value
        
        return data
    
    def _generate_deal_id(self, data: Dict[str, Any]) -> str:
        """Generate a unique deal ID"""
        try:
            # Use target company and date to create ID
            target = data.get("deal_summary", {}).get("target_company", "")
            date = data.get("deal_summary", {}).get("announcement_date", "")
            
            if target:
                # Clean target company name
                target_clean = re.sub(r'[^\w]', '', target)[:10]
                date_clean = re.sub(r'[^\d]', '', date)[:8]
                return f"DEAL_{target_clean}_{date_clean}"
            else:
                # Fallback to timestamp
                return f"DEAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
        except:
            return f"DEAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"