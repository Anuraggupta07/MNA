import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Google Cloud Configuration
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    GOOGLE_CLOUD_CREDENTIALS_PATH = os.getenv("GOOGLE_CLOUD_CREDENTIALS_PATH")
    
    # Google Sheets Configuration
    GOOGLE_SHEETS_CREDENTIALS_PATH = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
    GOOGLE_SHEETS_SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
    
    # Application Configuration
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    
    # Model Configuration
    PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "gpt-4-turbo")
    BACKUP_MODEL = os.getenv("BACKUP_MODEL", "gpt-3.5-turbo")
    
    # Validation
    def validate_config(self):
        """Validate that all required configurations are present"""
        required_configs = [
            ("OPENAI_API_KEY", self.OPENAI_API_KEY),
            ("GOOGLE_CLOUD_PROJECT", self.GOOGLE_CLOUD_PROJECT),
            ("GOOGLE_SHEETS_SPREADSHEET_ID", self.GOOGLE_SHEETS_SPREADSHEET_ID),
        ]
        
        missing_configs = []
        for config_name, config_value in required_configs:
            if not config_value:
                missing_configs.append(config_name)
        
        if missing_configs:
            raise ValueError(f"Missing required configuration: {', '.join(missing_configs)}")
        
        return True

# Create global settings instance
settings = Settings()

# Validate configuration on import
try:
    settings.validate_config()
    print("✅ Configuration validated successfully")
except ValueError as e:
    print(f"❌ Configuration error: {e}")
    print("Please check your .env file and ensure all required variables are set")