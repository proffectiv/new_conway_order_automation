"""
Dropbox handler module for secure Conway CSV file retrieval.

This module handles:
- Connecting to Dropbox API
- Downloading the Conway CSV file from Dropbox
- Using refresh token for secure authentication
"""

import dropbox
import os
import tempfile
from typing import Optional
import logging
from datetime import datetime
import requests

from config.settings import settings


class DropboxHandler:
    """Handles Dropbox file retrieval for the Conway CSV file."""
    
    def __init__(self):
        """Initialize Dropbox handler with configuration."""
        self.app_key = settings.DROPBOX_APP_KEY
        self.app_secret = settings.DROPBOX_APP_SECRET
        self.refresh_token = settings.DROPBOX_REFRESH_TOKEN
        self.file_path = settings.DROPBOX_FILE_PATH
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize Dropbox client with refresh token handling
        self.dbx = self._get_dropbox_client()
    
    def _get_access_token(self) -> Optional[str]:
        """
        Get a valid access token by refreshing the refresh token.
        Always refreshes - no token caching to avoid storing sensitive data.
        
        Returns:
            Valid access token or None if refresh fails
        """
        try:
            # Always refresh token (no persistent storage of sensitive tokens)
            return self._refresh_access_token()
            
        except Exception as e:
            self.logger.error(f"Error getting access token: {e}")
            return None
    
    def _refresh_access_token(self) -> Optional[str]:
        """
        Refresh the access token using the refresh token.
        
        Returns:
            New access token or None if refresh fails
        """
        try:
            url = 'https://api.dropboxapi.com/oauth2/token'
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': self.app_key,
                'client_secret': self.app_secret
            }
            
            self.logger.debug(f"Refreshing token with app_key: {self.app_key[:8]}...")
            response = requests.post(url, data=data)
            
            if response.status_code != 200:
                self.logger.error(f"Token refresh failed with status {response.status_code}: {response.text}")
                
            response.raise_for_status()
            
            token_data = response.json()
            access_token = token_data['access_token']
            expires_in = token_data.get('expires_in', 14400)  # Default 4 hours
            expires_at = datetime.now().timestamp() + expires_in
            
            # No token storage - always refresh for security
            
            self.logger.info("Successfully refreshed Dropbox access token")
            return access_token
            
        except Exception as e:
            self.logger.error(f"Error refreshing access token: {e}")
            return None
    
    def _get_dropbox_client(self) -> Optional[dropbox.Dropbox]:
        """
        Get a Dropbox client with a valid access token.
        
        Returns:
            Dropbox client or None if authentication fails
        """
        access_token = self._get_access_token()
        if access_token:
            return dropbox.Dropbox(access_token)
        else:
            self.logger.error("Failed to get valid access token")
            return None
    
    def _ensure_valid_client(self) -> bool:
        """
        Ensure we have a valid Dropbox client, refreshing token if needed.
        
        Returns:
            True if client is valid, False otherwise
        """
        if not self.dbx:
            self.dbx = self._get_dropbox_client()
        
        if not self.dbx:
            return False
            
        try:
            # Test the connection
            self.dbx.users_get_current_account()
            return True
        except dropbox.exceptions.AuthError:
            # Token might be expired, try to refresh
            self.logger.info("Access token expired, refreshing...")
            self.dbx = self._get_dropbox_client()
            if self.dbx:
                try:
                    self.dbx.users_get_current_account()
                    return True
                except Exception as e:
                    self.logger.error(f"Failed to authenticate with new token: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error checking client: {e}")
            return False
    
    def download_csv_file(self) -> Optional[str]:
        """
        Download the Conway CSV file from Dropbox to local temporary directory.
        
        Returns:
            Local file path if successful, None otherwise
        """
        try:
            # Ensure we have a valid client
            if not self._ensure_valid_client():
                self.logger.error("Failed to authenticate with Dropbox")
                return None
            
            # Create temporary file path with correct extension
            temp_dir = tempfile.gettempdir()
            file_extension = os.path.splitext(self.file_path)[1] or '.xlsx'
            local_filename = f"conway_ean_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
            local_path = os.path.join(temp_dir, local_filename)
            
            # Download the file
            self.logger.info(f"Downloading Conway CSV file from: {self.file_path}")
            
            try:
                with open(local_path, 'wb') as f:
                    metadata, response = self.dbx.files_download(self.file_path)
                    f.write(response.content)
                
                self.logger.info(f"Downloaded Conway CSV file to: {local_path}")
                return local_path
                
            except dropbox.exceptions.ApiError as e:
                # Handle file not found error
                if hasattr(e.error, 'get_path') and e.error.get_path() and hasattr(e.error.get_path(), 'is_not_found'):
                    if e.error.get_path().is_not_found():
                        self.logger.error(f"Conway CSV file not found at: {self.file_path}")
                        return None
                # Handle other path lookup errors
                elif 'path_lookup' in str(e.error) and 'not_found' in str(e.error):
                    self.logger.error(f"Conway CSV file not found at: {self.file_path}")
                    return None
                else:
                    self.logger.error(f"Dropbox API error downloading file: {e}")
                    return None
            
        except Exception as e:
            self.logger.error(f"Error downloading Conway CSV file: {e}")
            return None
    
    def cleanup_temp_file(self, file_path: str):
        """
        Clean up temporary file.
        
        Args:
            file_path: File path to delete
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            self.logger.warning(f"Could not delete temporary file {file_path}: {e}")
    
    def test_connection(self) -> bool:
        """
        Test the Dropbox connection and file access.
        
        Returns:
            True if connection and file access is successful
        """
        if not self._ensure_valid_client():
            return False
            
        try:
            account_info = self.dbx.users_get_current_account()
            self.logger.info(f"Connected to Dropbox account: {account_info.email}")
            
            # Test file access
            try:
                metadata = self.dbx.files_get_metadata(self.file_path)
                self.logger.info(f"Conway CSV file found: {metadata.name} (size: {metadata.size} bytes)")
                return True
            except dropbox.exceptions.ApiError as e:
                if hasattr(e.error, 'get_path') and e.error.get_path() and hasattr(e.error.get_path(), 'is_not_found'):
                    if e.error.get_path().is_not_found():
                        self.logger.error(f"Conway CSV file not found at: {self.file_path}")
                        return False
                elif 'path_lookup' in str(e.error) and 'not_found' in str(e.error):
                    self.logger.error(f"Conway CSV file not found at: {self.file_path}")
                    return False
                else:
                    self.logger.error(f"Error accessing Conway CSV file: {e}")
                    return False
            
        except Exception as e:
            self.logger.error(f"Dropbox connection failed: {e}")
            return False


def get_conway_csv_file() -> Optional[str]:
    """
    Main function to download the Conway CSV file from Dropbox.
    
    Returns:
        Path to the downloaded CSV file if successful, None otherwise
    """
    handler = DropboxHandler()
    
    try:
        # Test connection first
        if not handler.test_connection():
            logging.error("Dropbox connection or file access failed")
            return None
        
        # Download the file
        file_path = handler.download_csv_file()
        
        return file_path
        
    except Exception as e:
        logging.error(f"Error retrieving Conway CSV file from Dropbox: {e}")
        return None