"""
Main workflow orchestrator for Conway bike order monitoring.
Coordinates all components to check for new orders and send notifications.
"""

import json
import logging
import logging.config
from typing import List, Dict, Any
from datetime import datetime
import pytz

# Import our modules
from src.config import settings
from utils.csv_processor import CSVProcessor
from utils.processed_orders import ProcessedOrdersTracker
from holded.api_client import HoldedAPIClient
from notifications.email_sender import EmailSender

# Setup logging
logging.config.dictConfig(settings.get_log_config())
logger = logging.getLogger(__name__)

class WorkflowOrchestrator:
    """
    Main workflow orchestrator for Conway bike order monitoring.
    Coordinates CSV processing, API calls, and email notifications.
    """
    
    def __init__(self):
        """Initialize all components of the workflow."""
        logger.info("Initializing Conway Bikes workflow orchestrator")
        
        try:
            # Initialize all components
            self.csv_processor = CSVProcessor()
            self.holded_client = HoldedAPIClient()
            self.processed_orders_tracker = ProcessedOrdersTracker()
            
            # Initialize email sender with bike references for item filtering
            bike_references = self.csv_processor.get_bike_references()
            self.email_sender = EmailSender(bike_references=bike_references)
            
            logger.info("All workflow components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize workflow components: {e}")
            # Clean up any temporary files if initialization fails
            if hasattr(self, 'csv_processor'):
                self.csv_processor.cleanup()
            raise
    
    def _is_within_operation_hours(self, reference_time: datetime = None) -> bool:
        """
        Check if current time is within configured operation hours.
        
        Args:
            reference_time: Reference time to check. Uses current Madrid time if not provided.
            
        Returns:
            True if within operation hours, False otherwise
        """
        # Setup Madrid timezone
        madrid_tz = pytz.timezone(settings.TIMEZONE)
        
        if reference_time is None:
            reference_time = datetime.now(madrid_tz)
        elif reference_time.tzinfo is None:
            reference_time = madrid_tz.localize(reference_time)
        else:
            reference_time = reference_time.astimezone(madrid_tz)
        
        current_hour = reference_time.hour
        
        # Check if current hour is within operation window
        return settings.OPERATION_START_HOUR <= current_hour < settings.OPERATION_END_HOUR
    
    def run_daily_check(self, reference_time: datetime = None) -> Dict[str, Any]:
        """
        Run the daily check for Conway bike orders.
        
        Args:
            reference_time: Reference time for the check. Uses current Madrid time if not provided.
            
        Returns:
            Dictionary with workflow execution results
        """
        # Setup Madrid timezone
        madrid_tz = pytz.timezone(settings.TIMEZONE)
        
        if reference_time is None:
            reference_time = datetime.now(madrid_tz)
        elif reference_time.tzinfo is None:
            reference_time = madrid_tz.localize(reference_time)
        else:
            reference_time = reference_time.astimezone(madrid_tz)
        
        logger.info(f"Starting Conway bike order check at {reference_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Initialize result tracking
        result = {
            'timestamp': reference_time.isoformat(),
            'success': False,
            'total_orders_retrieved': 0,
            'duplicate_orders_filtered': 0,
            'filtered_orders_count': 0,
            'email_sent': False,
            'bike_references_loaded': 0,
            'errors': [],
            'orders_with_bikes': [],
            'within_operation_hours': self._is_within_operation_hours(reference_time)
        }
        
        try:
            # Step 0: Check if within operation hours (for automated runs)
            if not result['within_operation_hours']:
                skip_msg = f"Outside operation hours ({settings.OPERATION_START_HOUR}:00-{settings.OPERATION_END_HOUR}:00). Skipping check."
                logger.info(skip_msg)
                result['skipped'] = True
                result['skip_reason'] = "outside_operation_hours"
                result['success'] = True  # Consider this successful (intentional skip)
                return result
            
            # Step 0.5: Cleanup old processed order records (maintenance)
            self.processed_orders_tracker.cleanup_old_records(retention_hours=48)
            
            # Step 1: Load bike references from CSV
            logger.info("Step 1: Loading bike references from CSV")
            bike_references = self.csv_processor.get_bike_references()
            result['bike_references_loaded'] = len(bike_references)
            
            if not bike_references:
                error_msg = "No bike references loaded from CSV file"
                logger.error(error_msg)
                result['errors'].append(error_msg)
                return result
            
            logger.info(f"Loaded {len(bike_references)} bike references")
            
            # Step 2: Retrieve sales orders from Holded API (last 24 hours)
            logger.info("Step 2: Retrieving sales orders from Holded API (last 24 hours)")
            
            try:
                sales_orders = self.holded_client.get_sales_orders_since_yesterday(reference_time)
                result['total_orders_retrieved'] = len(sales_orders)
                
                logger.info(f"Retrieved {len(sales_orders)} sales orders from Holded API")
                
                # Early exit if no orders retrieved
                if not sales_orders:
                    skip_msg = "No orders found. Skipping further processing."
                    logger.info(skip_msg)
                    result['skipped'] = True
                    result['skip_reason'] = "no_orders_found"
                    result['success'] = True  # Consider this successful (no orders to process)
                    return result
                
            except Exception as e:
                error_msg = f"Failed to retrieve sales orders from Holded API: {e}"
                logger.error(error_msg)
                result['errors'].append(error_msg)
                return result
            
            # Step 2.5: Filter out already processed orders (DUPLICATE PREVENTION)
            logger.info("Step 2.5: Filtering out already processed orders")
            
            try:
                unprocessed_orders = self.processed_orders_tracker.filter_unprocessed_orders(sales_orders)
                result['duplicate_orders_filtered'] = len(sales_orders) - len(unprocessed_orders)
                
                logger.info(f"Filtered out {result['duplicate_orders_filtered']} already processed orders, {len(unprocessed_orders)} new orders to check")
                
                # Early exit if no unprocessed orders
                if not unprocessed_orders:
                    skip_msg = "All orders have already been processed. Skipping further processing."
                    logger.info(skip_msg)
                    result['skipped'] = True
                    result['skip_reason'] = "all_orders_already_processed"
                    result['success'] = True  # Consider this successful (intentional skip)
                    return result
                
                # Use unprocessed orders for further processing
                sales_orders = unprocessed_orders
                
            except Exception as e:
                error_msg = f"Failed to filter processed orders: {e}"
                logger.error(error_msg)
                result['errors'].append(error_msg)
                # Continue with all orders if filtering fails (better to have duplicates than miss orders)
            
            # Step 3: Filter orders containing bike references
            logger.info("Step 3: Filtering orders for bike references")
            
            try:
                filtered_orders = self.csv_processor.filter_orders_by_references(sales_orders)
                result['filtered_orders_count'] = len(filtered_orders)
                result['orders_with_bikes'] = filtered_orders
                
                logger.info(f"Found {len(filtered_orders)} orders containing bike references")
                
            except Exception as e:
                error_msg = f"Failed to filter orders: {e}"
                logger.error(error_msg)
                result['errors'].append(error_msg)
                return result
            
            # Step 4: Send email notification if orders found
            if filtered_orders:
                logger.info("Step 4: Sending email notification")
                
                try:
                    email_success = self.email_sender.send_order_notification(filtered_orders)
                    result['email_sent'] = email_success
                    
                    if email_success:
                        logger.info("Email notification sent successfully")
                        
                        # Mark all retrieved orders as processed (DUPLICATE PREVENTION)
                        all_order_ids = [order.get('id') for order in sales_orders if order.get('id')]
                        if all_order_ids:
                            self.processed_orders_tracker.mark_orders_processed(all_order_ids)
                            logger.info(f"Marked {len(all_order_ids)} orders as processed to prevent duplicates")
                        
                    else:
                        error_msg = "Email notification failed to send"
                        logger.error(error_msg)
                        result['errors'].append(error_msg)
                        return result
                        
                except Exception as e:
                    error_msg = f"Failed to send email notification: {e}"
                    logger.error(error_msg)
                    result['errors'].append(error_msg)
                    return result
            else:
                logger.info("Step 4: No bike orders found - no email notification needed")
                result['email_sent'] = True  # Consider this successful (no email needed)
                result['skipped'] = True
                result['skip_reason'] = "no_bike_orders"
                
                # Mark all retrieved orders as processed (even though no bikes found)
                all_order_ids = [order.get('id') for order in sales_orders if order.get('id')]
                if all_order_ids:
                    self.processed_orders_tracker.mark_orders_processed(all_order_ids)
                    logger.info(f"Marked {len(all_order_ids)} non-bike orders as processed")
            
            # Mark workflow as successful
            result['success'] = True
            logger.info("Check completed successfully")
            
        except Exception as e:
            error_msg = f"Unexpected error during workflow execution: {e}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
        
        return result
    
    def test_all_components(self) -> Dict[str, Any]:
        """
        Test all workflow components to verify functionality.
        
        Returns:
            Dictionary with test results for each component
        """
        logger.info("Testing all workflow components")
        
        test_results = {
            'csv_processor': {'success': False, 'error': None},
            'holded_api': {'success': False, 'error': None},
            'email_sender': {'success': False, 'error': None},
            'overall_success': False
        }
        
        # Test CSV processor
        try:
            csv_stats = self.csv_processor.get_csv_stats()
            test_results['csv_processor']['success'] = csv_stats['file_exists'] and csv_stats['total_references'] > 0
            test_results['csv_processor']['stats'] = csv_stats
            
            if test_results['csv_processor']['success']:
                logger.info(f"CSV processor test passed: {csv_stats['total_references']} references loaded")
            else:
                logger.warning("CSV processor test failed: No references loaded or file missing")
                
        except Exception as e:
            test_results['csv_processor']['error'] = str(e)
            logger.error(f"CSV processor test failed: {e}")
        
        # Test Holded API connection
        try:
            api_success = self.holded_client.test_connection()
            test_results['holded_api']['success'] = api_success
            
            if api_success:
                logger.info("Holded API test passed: Connection successful")
                # Try to get API info
                try:
                    api_info = self.holded_client.get_api_info()
                    test_results['holded_api']['info'] = api_info
                except:
                    pass  # API info is optional
            else:
                logger.warning("Holded API test failed: Connection unsuccessful")
                
        except Exception as e:
            test_results['holded_api']['error'] = str(e)
            logger.error(f"Holded API test failed: {e}")
        
        # Test email sender
        try:
            if settings.TEST_EMAIL_ONLY:
                # In test mode, just test connection
                email_success = self.email_sender.test_email_connection()
                test_results['email_sender']['success'] = email_success
                
                if email_success:
                    logger.info("Email sender test passed: Connection successful (test mode)")
                else:
                    logger.warning("Email sender test failed: Connection unsuccessful")
            else:
                # In production mode, send a test email
                email_success = self.email_sender.send_test_email()
                test_results['email_sender']['success'] = email_success
                
                if email_success:
                    logger.info("Email sender test passed: Test email sent successfully")
                else:
                    logger.warning("Email sender test failed: Test email not sent")
                    
        except Exception as e:
            test_results['email_sender']['error'] = str(e)
            logger.error(f"Email sender test failed: {e}")
        
        # Determine overall success
        test_results['overall_success'] = all(
            test_results[component]['success'] 
            for component in ['csv_processor', 'holded_api', 'email_sender']
        )
        
        if test_results['overall_success']:
            logger.info("All component tests passed successfully")
        else:
            logger.warning("Some component tests failed")
        
        return test_results
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get current system status and configuration.
        
        Returns:
            Dictionary with system status information
        """
        madrid_tz = pytz.timezone(settings.TIMEZONE)
        current_time = datetime.now(madrid_tz)
        
        status = {
            'timestamp': current_time.isoformat(),
            'timezone': settings.TIMEZONE,
            'schedule': {
                'hour': settings.SCHEDULE_HOUR,
                'minute': settings.SCHEDULE_MINUTE,
                'next_run_description': f"Daily at {settings.SCHEDULE_HOUR:02d}:{settings.SCHEDULE_MINUTE:02d} Madrid time"
            },
            'configuration': {
                'dropbox_file_path': settings.DROPBOX_FILE_PATH,
                'api_base_url': settings.HOLDED_BASE_URL,
                'target_email': settings.TARGET_EMAIL,
                'test_mode': settings.TEST_MODE,
                'test_email_only': settings.TEST_EMAIL_ONLY
            },
            'csv_stats': None,
            'errors': []
        }
        
        try:
            # Get CSV statistics
            status['csv_stats'] = self.csv_processor.get_csv_stats()
        except Exception as e:
            status['errors'].append(f"Failed to get CSV stats: {e}")
        
        return status
    
    def cleanup(self):
        """Clean up temporary files and resources."""
        if hasattr(self, 'csv_processor'):
            self.csv_processor.cleanup()
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.cleanup() 