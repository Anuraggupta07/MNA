import re
import logging
from typing import Dict, List, Tuple
from collections import Counter

logger = logging.getLogger(__name__)

class DocumentClassifier:
    """
    Classifies documents based on content patterns
    """
    
    def __init__(self):
        # Define keyword patterns for each document type
        self.patterns = {
            "press_release": {
                "keywords": [
                    "press release", "announces", "acquisition", "merger",
                    "transaction", "closing", "signing", "agreement",
                    "forward-looking statements", "safe harbor"
                ],
                "phrases": [
                    "for immediate release",
                    "announced today",
                    "pleased to announce",
                    "has agreed to acquire",
                    "has completed the acquisition"
                ]
            },
            "quarterly_report": {
                "keywords": [
                    "quarterly report", "q1", "q2", "q3", "q4",
                    "quarterly results", "earnings", "fiscal quarter",
                    "three months ended", "quarterly financial"
                ],
                "phrases": [
                    "quarterly report",
                    "financial results",
                    "quarterly earnings",
                    "fiscal quarter ended"
                ]
            },
            "annual_report": {
                "keywords": [
                    "annual report", "form 10-k", "fiscal year",
                    "annual results", "yearly results", "12 months ended",
                    "annual financial", "year ended"
                ],
                "phrases": [
                    "annual report",
                    "fiscal year ended",
                    "year ended december",
                    "twelve months ended"
                ]
            },
            "investor_deck": {
                "keywords": [
                    "investor presentation", "company overview",
                    "investment highlights", "business strategy",
                    "market opportunity", "financial projections",
                    "slide", "presentation"
                ],
                "phrases": [
                    "investor presentation",
                    "company overview",
                    "investment thesis",
                    "business highlights"
                ]
            }
        }
    
    def classify_document(self, text: str) -> str:
        """
        Classify document type based on content
        """
        try:
            # Convert to lowercase for matching
            text_lower = text.lower()
            
            # Calculate scores for each document type
            scores = {}
            
            for doc_type, patterns in self.patterns.items():
                score = 0
                
                # Check keywords
                for keyword in patterns["keywords"]:
                    count = text_lower.count(keyword.lower())
                    score += count * 1  # Weight of 1 for keywords
                
                # Check phrases (higher weight)
                for phrase in patterns["phrases"]:
                    count = text_lower.count(phrase.lower())
                    score += count * 2  # Weight of 2 for phrases
                
                scores[doc_type] = score
            
            # Find the document type with highest score
            if max(scores.values()) > 0:
                best_match = max(scores, key=scores.get)
                confidence = scores[best_match]
                
                logger.info(f"Document classified as: {best_match} (score: {confidence})")
                return best_match
            else:
                logger.info("Document classified as: other (no clear match)")
                return "other"
                
        except Exception as e:
            logger.error(f"Error classifying document: {e}")
            return "other"
    
    def get_classification_confidence(self, text: str) -> Dict[str, float]:
        """
        Get confidence scores for all document types
        """
        try:
            text_lower = text.lower()
            scores = {}
            
            for doc_type, patterns in self.patterns.items():
                score = 0
                
                # Check keywords
                for keyword in patterns["keywords"]:
                    count = text_lower.count(keyword.lower())
                    score += count * 1
                
                # Check phrases
                for phrase in patterns["phrases"]:
                    count = text_lower.count(phrase.lower())
                    score += count * 2
                
                scores[doc_type] = score
            
            # Normalize scores to percentages
            total_score = sum(scores.values())
            if total_score > 0:
                for doc_type in scores:
                    scores[doc_type] = (scores[doc_type] / total_score) * 100
            
            return scores
            
        except Exception as e:
            logger.error(f"Error getting classification confidence: {e}")
            return {}
    
    def extract_key_indicators(self, text: str) -> Dict[str, List[str]]:
        """
        Extract key indicators that suggest document type
        """
        try:
            text_lower = text.lower()
            indicators = {}
            
            for doc_type, patterns in self.patterns.items():
                found_indicators = []
                
                # Find matching keywords
                for keyword in patterns["keywords"]:
                    if keyword.lower() in text_lower:
                        found_indicators.append(keyword)
                
                # Find matching phrases
                for phrase in patterns["phrases"]:
                    if phrase.lower() in text_lower:
                        found_indicators.append(phrase)
                
                if found_indicators:
                    indicators[doc_type] = found_indicators
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error extracting key indicators: {e}")
            return {}
    
    def is_financial_document(self, text: str) -> bool:
        """
        Check if document contains financial information
        """
        financial_keywords = [
            "revenue", "ebitda", "earnings", "profit", "loss",
            "financial results", "income statement", "balance sheet",
            "cash flow", "financial performance", "million", "billion"
        ]
        
        text_lower = text.lower()
        financial_count = sum(1 for keyword in financial_keywords if keyword in text_lower)
        
        return financial_count >= 3  # At least 3 financial keywords
    
    def is_mna_document(self, text: str) -> bool:
        """
        Check if document is related to M&A activity
        """
        mna_keywords = [
            "acquisition", "merger", "buyout", "transaction", "deal",
            "acquire", "purchase", "buy", "sell", "divestiture",
            "target", "buyer", "seller", "closing", "completion"
        ]
        
        text_lower = text.lower()
        mna_count = sum(1 for keyword in mna_keywords if keyword in text_lower)
        
        return mna_count >= 2  # At least 2 M&A keywords