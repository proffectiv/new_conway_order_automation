"""
Configuration settings for Holded API automation system.
Loads environment variables and provides validated configuration.
"""

import os
import logging
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)  # Force reload environment variables

class Settings:
    """
    Application settings loaded from environment variables.
    Provides validation and default values for all configuration options.
    """
    
    def __init__(self):
        # Reload environment variables to pick up any changes
        load_dotenv(override=True)
        
        # Holded API Configuration
        self.HOLDED_API_KEY = self._get_required_env("HOLDED_API_KEY")
        self.HOLDED_BASE_URL = os.getenv("HOLDED_BASE_URL", "https://api.holded.com/api/invoicing/v1")
        
        # Dropbox Configuration
        self.DROPBOX_APP_KEY = self._get_required_env("DROPBOX_APP_KEY")
        self.DROPBOX_APP_SECRET = self._get_required_env("DROPBOX_APP_SECRET")
        self.DROPBOX_REFRESH_TOKEN = self._get_required_env("DROPBOX_REFRESH_TOKEN")
        self.DROPBOX_FILE_PATH = os.getenv("DROPBOX_FILE_PATH")
        
        # Email Configuration - Updated to use Strato SMTP
        self.SMTP_SERVER = os.getenv("SMTP_SERVER")
        self.SMTP_PORT = int(os.getenv("SMTP_PORT"))
        self.EMAIL_USERNAME = self._get_required_env("EMAIL_USERNAME")
        self.EMAIL_PASSWORD = self._get_required_env("EMAIL_PASSWORD")
        self.EMAIL_FROM = os.getenv("EMAIL_FROM", self.EMAIL_USERNAME)
        
        # Notification Configuration
        self.TARGET_EMAIL = self._get_required_env("TARGET_EMAIL")
        self.EMAIL_SUBJECT_PREFIX = os.getenv("EMAIL_SUBJECT_PREFIX")
        
        # Timezone Configuration
        self.TIMEZONE = os.getenv("TIMEZONE", "Europe/Madrid")
        
        # Application Configuration
        # Note: CSV file is now retrieved from Dropbox using DROPBOX_FILE_PATH
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE = os.getenv("LOG_FILE", "logs/holded_automation.log")
        
        # Schedule Configuration
        self.SCHEDULE_HOUR = int(os.getenv("SCHEDULE_HOUR", "9"))
        self.SCHEDULE_MINUTE = int(os.getenv("SCHEDULE_MINUTE", "0"))
        
        # Frequent Check Configuration
        self.OPERATION_START_HOUR = int(os.getenv("OPERATION_START_HOUR", "7"))
        self.OPERATION_END_HOUR = int(os.getenv("OPERATION_END_HOUR", "23"))
        
        # Development/Testing Configuration
        self.TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
        self.TEST_EMAIL_ONLY = os.getenv("TEST_EMAIL_ONLY", "false").lower() == "true"
        
        # Validate configuration
        self._validate_settings()
    
    def _get_required_env(self, key: str) -> str:
        """
        Get required environment variable.
        Raises ValueError if not found.
        """
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} not found")
        return value
    
    def _validate_settings(self):
        """
        Validate configuration settings.
        Ensures all required values are present and valid.
        """
        # Note: CSV file validation removed since we now use Dropbox for secure file access
        
        # Validate schedule time
        if not (0 <= self.SCHEDULE_HOUR <= 23):
            raise ValueError("SCHEDULE_HOUR must be between 0 and 23")
        
        if not (0 <= self.SCHEDULE_MINUTE <= 59):
            raise ValueError("SCHEDULE_MINUTE must be between 0 and 59")
        
        # Validate frequent check configuration
        if not (0 <= self.OPERATION_START_HOUR <= 23):
            raise ValueError("OPERATION_START_HOUR must be between 0 and 23")
        
        if not (0 <= self.OPERATION_END_HOUR <= 23):
            raise ValueError("OPERATION_END_HOUR must be between 0 and 23")
        
        if self.OPERATION_START_HOUR >= self.OPERATION_END_HOUR:
            raise ValueError("OPERATION_START_HOUR must be less than OPERATION_END_HOUR")
        
        # Validate SMTP port
        if not (1 <= self.SMTP_PORT <= 65535):
            raise ValueError("SMTP_PORT must be between 1 and 65535")
        
        # Create logs directory if it doesn't exist
        log_dir = Path(self.LOG_FILE).parent
        log_dir.mkdir(exist_ok=True)
    
    def get_log_config(self) -> dict:
        """
        Get logging configuration dictionary.
        Returns structured logging configuration with sensitive data filtering.
        """
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                },
            },
            'filters': {
                'sensitive_data_filter': {
                    '()': 'config.logging_filters.SensitiveDataFilter'
                }
            },
            'handlers': {
                'default': {
                    'level': self.LOG_LEVEL,
                    'formatter': 'standard',
                    'class': 'logging.StreamHandler',
                    'filters': ['sensitive_data_filter']
                },
                'file': {
                    'level': self.LOG_LEVEL,
                    'formatter': 'standard',
                    'class': 'logging.FileHandler',
                    'filename': self.LOG_FILE,
                    'mode': 'a',
                    'filters': ['sensitive_data_filter']
                },
            },
            'loggers': {
                '': {
                    'handlers': ['default', 'file'],
                    'level': self.LOG_LEVEL,
                    'propagate': False
                }
            }
        }

# Global settings instance
settings = Settings() 