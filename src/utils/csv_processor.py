"""
CSV processor for bike references.
Reads and processes bike references from Conway CSV file.
"""

import csv
import logging
from typing import List, Set, Dict, Any
from pathlib import Path
from config.settings import settings

logger = logging.getLogger(__name__)

class CSVProcessor:
    """
    Processes Conway bike references CSV file.
    Extracts bike references and provides filtering capabilities.
    """
    
    def __init__(self, csv_file_path: str = None):
        """
        Initialize CSV processor.
        
        Args:
            csv_file_path: Path to CSV file. Uses settings default if not provided.
        """
        self.csv_file_path = csv_file_path or settings.CSV_FILE_PATH
        self.bike_references: Set[str] = set()
        self.csv_data: List[Dict[str, str]] = []
        
        # Load bike references on initialization
        self._load_bike_references()
    
    def _load_bike_references(self) -> None:
        """
        Load bike references from CSV file.
        Extracts references from the 'Referencia' column.
        """
        try:
            csv_path = Path(self.csv_file_path)
            
            if not csv_path.exists():
                raise FileNotFoundError(f"CSV file not found: {self.csv_file_path}")
            
            logger.info(f"Loading bike references from: {self.csv_file_path}")
            
            with open(csv_path, 'r', encoding='utf-8') as file:
                # Try to detect delimiter (comma or semicolon)
                sample = file.read(1024)
                file.seek(0)
                
                # Determine delimiter based on frequency
                comma_count = sample.count(',')
                semicolon_count = sample.count(';')
                delimiter = ';' if semicolon_count > comma_count else ','
                
                reader = csv.DictReader(file, delimiter=delimiter)
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 since row 1 is header
                    try:
                        # Extract bike reference (handle different possible column names)
                        reference = row.get('Referencia') or row.get('Reference') or row.get('referencia')
                        
                        if reference and reference.strip():
                            # Clean and normalize the reference
                            clean_reference = reference.strip().upper()
                            self.bike_references.add(clean_reference)
                            
                            # Store full row data for potential future use
                            self.csv_data.append(row)
                        
                    except Exception as e:
                        logger.warning(f"Error processing row {row_num}: {e}")
                        continue
            
            logger.info(f"Loaded {len(self.bike_references)} bike references from CSV")
            
            # Log first few references for debugging (in test mode)
            if settings.TEST_MODE and self.bike_references:
                sample_refs = list(self.bike_references)[:5]
                logger.debug(f"Sample bike references: {sample_refs}")
                
        except Exception as e:
            logger.error(f"Failed to load bike references from CSV: {e}")
            raise
    
    def get_bike_references(self) -> Set[str]:
        """
        Get all loaded bike references.
        
        Returns:
            Set of bike reference strings (normalized to uppercase)
        """
        return self.bike_references.copy()
    
    def contains_bike_reference(self, text: str) -> bool:
        """
        Check if text contains any bike reference.
        
        Args:
            text: Text to search for bike references
            
        Returns:
            True if any bike reference is found in the text
        """
        if not text:
            return False
        
        # Normalize text for comparison
        normalized_text = text.upper()
        
        # Check if any bike reference is present in the text
        for reference in self.bike_references:
            if reference in normalized_text:
                return True
        
        return False
    
    def find_matching_references(self, text: str) -> List[str]:
        """
        Find all bike references present in the given text.
        
        Args:
            text: Text to search for bike references
            
        Returns:
            List of matching bike references found in the text
        """
        if not text:
            return []
        
        # Normalize text for comparison
        normalized_text = text.upper()
        
        # Find all matching references
        matches = []
        for reference in self.bike_references:
            if reference in normalized_text:
                matches.append(reference)
        
        return matches
    
    def filter_orders_by_references(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter orders to only include those containing bike references.
        
        Args:
            orders: List of order dictionaries from Holded API
            
        Returns:
            List of orders that contain bike references
        """
        filtered_orders = []
        
        for order in orders:
            try:
                # Check various fields where bike references might appear
                search_fields = [
                    order.get('desc', ''),
                    order.get('notes', ''),
                    order.get('custom', ''),
                ]
                
                # Also check products/line items if present
                if 'products' in order:
                    for product in order.get('products', []):
                        search_fields.extend([
                            product.get('name', ''),
                            product.get('desc', ''),
                            product.get('code', ''),
                            product.get('sku', ''),
                        ])
                elif 'items' in order:
                    for item in order.get('items', []):
                        search_fields.extend([
                            item.get('name', ''),
                            item.get('desc', ''),
                            item.get('code', ''),
                            item.get('sku', ''),
                        ])
                
                # Combine all searchable text
                combined_text = ' '.join(str(field) for field in search_fields if field)
                
                # Check if any bike reference is present
                if self.contains_bike_reference(combined_text):
                    # Add matching references to order data for logging
                    order['matching_references'] = self.find_matching_references(combined_text)
                    filtered_orders.append(order)
                    
            except Exception as e:
                logger.warning(f"Error processing order {order.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Filtered {len(filtered_orders)} orders containing bike references from {len(orders)} total orders")
        
        return filtered_orders
    
    def get_csv_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the loaded CSV data.
        
        Returns:
            Dictionary with CSV statistics
        """
        return {
            'file_path': self.csv_file_path,
            'total_references': len(self.bike_references),
            'total_rows': len(self.csv_data),
            'file_exists': Path(self.csv_file_path).exists(),
        } 