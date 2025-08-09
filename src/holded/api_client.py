"""
Holded API client for sales order retrieval.
Handles authentication and API communication with Holded API.
"""

import requests
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pytz
from src.config import settings
import json

logger = logging.getLogger(__name__)

class HoldedAPIClient:
    """
    Client for interacting with Holded API.
    Handles authentication and sales order retrieval.
    """
    
    def __init__(self, api_key: str = None, base_url: str = None):
        """
        Initialize Holded API client.
        
        Args:
            api_key: Holded API key. Uses settings default if not provided.
            base_url: Base URL for Holded API. Uses settings default if not provided.
        """
        self.api_key = api_key or settings.HOLDED_API_KEY
        self.base_url = (base_url or settings.HOLDED_BASE_URL).rstrip('/')
        
        # Setup session with authentication headers
        self.session = requests.Session()
        self.session.headers.update({
            'key': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Request timeout (seconds)
        self.timeout = 30
        
        logger.info("Holded API client initialized")
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request to Holded API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for requests
            
        Returns:
            JSON response as dictionary
            
        Raises:
            requests.RequestException: If API request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Set default timeout if not provided
        kwargs.setdefault('timeout', self.timeout)
        
        try:
            logger.debug(f"Making {method} request to: {url}")
            
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            # Try to parse JSON response
            try:
                return response.json()
            except ValueError:
                logger.warning(f"Non-JSON response received from {url}")
                return {'raw_response': response.text}
                
        except requests.RequestException as e:
            logger.error(f"API request failed: {method} {url} - {e}")
            raise
    
    def get_documents(self, 
                     doc_type: str = 'salesorder',
                     start_date: datetime = None, 
                     end_date: datetime = None) -> List[Dict[str, Any]]:
        """
        Get documents (sales orders) from Holded API.
        
        Args:
            doc_type: Type of document to retrieve ('salesorder', 'invoice', etc.)
            start_date: Start date for filtering (timezone aware)
            end_date: End date for filtering (timezone aware)
            limit: Maximum number of documents to retrieve
            
        Returns:
            List of document dictionaries
        """
        try:
            # Build query parameters
            params = {
            }
            
            # Add date filtering if provided
            if start_date:
                # Convert to Unix timestamp - Holded API uses starttmp for start time filtering
                params['starttmp'] = int(start_date.timestamp())
                logger.debug(f"Start time filter: {start_date} → starttmp={params['starttmp']}")
            
            if end_date:
                # Convert to Unix timestamp - Holded API uses endtmp for end time filtering
                params['endtmp'] = int(end_date.timestamp())
                logger.debug(f"End time filter: {end_date} → endtmp={params['endtmp']}")
            
            logger.debug(f"API request parameters: {params}")
            
            # Make API request to documents endpoint
            endpoint = f"documents/{doc_type}"
            response = self._make_request('GET', endpoint, params=params)
            
            # Handle different response formats
            if isinstance(response, list):
                documents = response
            elif isinstance(response, dict):
                # Response might be wrapped in a data field or similar
                documents = response.get('data', response.get('documents', [response]))
            else:
                logger.warning(f"Unexpected response format: {type(response)}")
                documents = []
            
            logger.info(f"Retrieved {len(documents)} {doc_type} documents from Holded API")
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to retrieve documents: {e}")
            raise
    
    def get_sales_orders_since_yesterday(self, reference_time: datetime = None) -> List[Dict[str, Any]]:
        """
        Get sales orders created since yesterday at 9 AM Madrid time.
        
        Args:
            reference_time: Reference time for calculating "yesterday". 
                          Uses current Madrid time if not provided.
            
        Returns:
            List of sales order dictionaries
        """
        try:
            # Setup Madrid timezone
            madrid_tz = pytz.timezone(settings.TIMEZONE)
            
            # Use provided reference time or current Madrid time
            if reference_time is None:
                reference_time = datetime.now(madrid_tz)
            elif reference_time.tzinfo is None:
                reference_time = madrid_tz.localize(reference_time)
            else:
                reference_time = reference_time.astimezone(madrid_tz)
            
            # Calculate yesterday at 9 AM Madrid time
            yesterday = reference_time.date() - timedelta(days=1)
            start_time = madrid_tz.localize(
                datetime.combine(yesterday, datetime.min.time())
            ).replace(hour=settings.SCHEDULE_HOUR, minute=settings.SCHEDULE_MINUTE)
            
            # End time is current reference time
            end_time = reference_time
            
            logger.info(f"Fetching sales orders from {start_time} to {end_time}")
            
            # Get sales orders from the API
            orders = self.get_documents(
                doc_type='salesorder',
                start_date=start_time,
                end_date=end_time,
            )
            
            return orders
            
        except Exception as e:
            logger.error(f"Failed to retrieve sales orders since yesterday: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test connection to Holded API.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to make a simple API call to test authentication
            # Using a lightweight endpoint like getting company info or limits
            endpoint = "documents/salesorder"
            params = {'limit': 1}  # Minimal request
            
            response = self._make_request('GET', endpoint, params=params)
            
            logger.info("Holded API connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"Holded API connection test failed: {e}")
            return False
    
    def get_api_info(self) -> Dict[str, Any]:
        """
        Get API information and limits.
        
        Returns:
            Dictionary with API information
        """
        try:
            # Attempt to get basic API info
            # This might vary depending on available endpoints
            response = self._make_request('GET', 'info')
            return response
            
        except Exception as e:
            logger.warning(f"Could not retrieve API info: {e}")
            return {
                'error': str(e),
                'base_url': self.base_url,
                'authenticated': self.test_connection()
            }
    
    def get_customer_nif(self, customer_id: str) -> Dict[str, Any]:
        """
        Get customer information from Holded API.
        
        Args:
            customer_id: ID of the customer to retrieve
            
        Returns:
            Customer NIF
        """
        try:
            # Make API request to get customer info
            url = f"{self.base_url}/contacts/{customer_id}"
            response = requests.get(url, headers={'key': self.api_key})
            response_json = response.json()
            return response_json['code'] if response_json['code'] else 'N/A'
        except Exception as e:
            logger.error(f"Failed to retrieve customer nif: {e}")
            raise