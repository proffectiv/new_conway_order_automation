"""
Processed orders tracking system for Conway bike order monitoring.
Prevents duplicate notifications by maintaining a record of processed orders.
"""

import json
import logging
from pathlib import Path
from typing import Set, List, Dict, Any
from datetime import datetime, timedelta
import pytz
from config.settings import settings

logger = logging.getLogger(__name__)

class ProcessedOrdersTracker:
    """
    Tracks processed orders to prevent duplicate notifications.
    Maintains a persistent record of order IDs that have been processed.
    """
    
    def __init__(self, storage_file: str = "logs/processed_orders.json"):
        """
        Initialize the processed orders tracker.
        
        Args:
            storage_file: Path to file for storing processed order records
        """
        self.storage_file = Path(storage_file)
        self.processed_orders = {}  # {order_id: timestamp}
        
        # Ensure storage directory exists
        self.storage_file.parent.mkdir(exist_ok=True)
        
        # Load existing processed orders
        self._load_processed_orders()
        
        logger.info(f"Processed orders tracker initialized with {len(self.processed_orders)} existing records")
    
    def _load_processed_orders(self):
        """Load processed orders from storage file."""
        try:
            if self.storage_file.exists():
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    self.processed_orders = data.get('processed_orders', {})
                    logger.debug(f"Loaded {len(self.processed_orders)} processed order records")
            else:
                logger.debug("No existing processed orders file found, starting fresh")
                
        except Exception as e:
            logger.warning(f"Could not load processed orders file: {e}")
            self.processed_orders = {}
    
    def _save_processed_orders(self):
        """Save processed orders to storage file."""
        try:
            data = {
                'processed_orders': self.processed_orders,
                'last_updated': datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
            }
            
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.debug(f"Saved {len(self.processed_orders)} processed order records")
            
        except Exception as e:
            logger.error(f"Could not save processed orders file: {e}")
    
    def cleanup_old_records(self, retention_hours: int = 48):
        """
        Remove old processed order records to prevent file from growing indefinitely.
        
        Args:
            retention_hours: Hours to keep processed order records (default: 48 hours)
        """
        try:
            madrid_tz = pytz.timezone(settings.TIMEZONE)
            cutoff_time = datetime.now(madrid_tz) - timedelta(hours=retention_hours)
            
            old_count = len(self.processed_orders)
            
            # Filter out old records
            self.processed_orders = {
                order_id: timestamp 
                for order_id, timestamp in self.processed_orders.items()
                if datetime.fromisoformat(timestamp.replace('Z', '+00:00')) > cutoff_time
            }
            
            removed_count = old_count - len(self.processed_orders)
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old processed order records (older than {retention_hours} hours)")
                self._save_processed_orders()
            
        except Exception as e:
            logger.error(f"Error during cleanup of old records: {e}")
    
    def is_order_processed(self, order_id: str) -> bool:
        """
        Check if an order has already been processed.
        
        Args:
            order_id: Order ID to check
            
        Returns:
            True if order has been processed, False otherwise
        """
        return str(order_id) in self.processed_orders
    
    def mark_order_processed(self, order_id: str):
        """
        Mark an order as processed.
        
        Args:
            order_id: Order ID to mark as processed
        """
        madrid_tz = pytz.timezone(settings.TIMEZONE)
        timestamp = datetime.now(madrid_tz).isoformat()
        
        self.processed_orders[str(order_id)] = timestamp
        logger.debug(f"Marked order {order_id} as processed at {timestamp}")
    
    def mark_orders_processed(self, order_ids: List[str]):
        """
        Mark multiple orders as processed.
        
        Args:
            order_ids: List of order IDs to mark as processed
        """
        madrid_tz = pytz.timezone(settings.TIMEZONE)
        timestamp = datetime.now(madrid_tz).isoformat()
        
        for order_id in order_ids:
            self.processed_orders[str(order_id)] = timestamp
        
        logger.info(f"Marked {len(order_ids)} orders as processed")
        self._save_processed_orders()
    
    def filter_unprocessed_orders(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out orders that have already been processed.
        
        Args:
            orders: List of order dictionaries from Holded API
            
        Returns:
            List of orders that have not been processed yet
        """
        unprocessed_orders = []
        processed_count = 0
        
        for order in orders:
            order_id = order.get('id')
            if not order_id:
                logger.warning("Order found without ID, skipping")
                continue
            
            if not self.is_order_processed(order_id):
                unprocessed_orders.append(order)
            else:
                processed_count += 1
                logger.debug(f"Skipping already processed order: {order_id}")
        
        if processed_count > 0:
            logger.info(f"Filtered out {processed_count} already processed orders, {len(unprocessed_orders)} new orders remain")
        
        return unprocessed_orders
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about processed orders.
        
        Returns:
            Dictionary with tracker statistics
        """
        return {
            'total_processed_orders': len(self.processed_orders),
            'storage_file': str(self.storage_file),
            'storage_file_exists': self.storage_file.exists(),
            'oldest_record': min(self.processed_orders.values()) if self.processed_orders else None,
            'newest_record': max(self.processed_orders.values()) if self.processed_orders else None
        } 