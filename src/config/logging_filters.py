"""
Logging filters to prevent sensitive data from being logged.
"""

import re
import logging


class SensitiveDataFilter(logging.Filter):
    """
    Filter to redact sensitive data from log messages before they are written.
    """
    
    def __init__(self):
        super().__init__()
        # Define patterns for sensitive data
        self.sensitive_patterns = [
            # Email addresses
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', '[EMAIL_REDACTED]'),
            # API keys (common patterns)
            (r'\b[Aa]pi[_-]?[Kk]ey[:\s=]+[\'"]?([A-Za-z0-9_-]{20,})[\'"]?', r'api_key: [API_KEY_REDACTED]'),
            # Passwords
            (r'\b[Pp]assword[:\s=]+[\'"]?([^\s\'"]{3,})[\'"]?', r'password: [PASSWORD_REDACTED]'),
            # Tokens
            (r'\b[Tt]oken[:\s=]+[\'"]?([A-Za-z0-9_-]{10,})[\'"]?', r'token: [TOKEN_REDACTED]'),
            # Authorization headers
            (r'[Aa]uthorization[:\s=]+[\'"]?([^\s\'"]{10,})[\'"]?', r'Authorization: [AUTH_REDACTED]'),
            # Bearer tokens
            (r'[Bb]earer\s+([A-Za-z0-9_-]{10,})', r'Bearer [BEARER_REDACTED]'),
            # Generic secrets
            (r'\b[Ss]ecret[:\s=]+[\'"]?([^\s\'"]{5,})[\'"]?', r'secret: [SECRET_REDACTED]'),
            
            # Dropbox-specific sensitive data
            # File paths (especially with personal/company info)
            (r'/[A-Z][^/\s]*(?:/[^/\s]*)*\.(?:csv|xlsx|xls)\b', '[FILE_PATH_REDACTED]'),
            # Local temp file paths
            (r'/(?:var/folders|tmp)/[^\s]*(?:conway|ean)[^\s]*\.(?:csv|xlsx|xls)', '[TEMP_FILE_REDACTED]'),
            # File names with Conway or EAN info
            (r'\b(?:Información_EAN_Conway_\d+|conway_ean_\d+)[^\s]*\.(?:csv|xlsx|xls)', '[FILENAME_REDACTED]'),
            # File sizes (can reveal data volume)
            (r'\(size:\s*\d+\s*bytes\)', '(size: [SIZE_REDACTED])'),
            # Number of references loaded (both variants)
            (r'Loaded\s+\d+\s+bike\s+references(?:\s+from\s+CSV)?', 'Loaded [COUNT_REDACTED] bike references'),
            # Total references count patterns
            (r'\d+\s+bike\s+references\s+from\s+CSV', '[COUNT_REDACTED] bike references from CSV'),
            # Loading bike references from file path
            (r'Loading\s+bike\s+references\s+from:\s+[^\s]+', 'Loading bike references from: [FILE_PATH_REDACTED]'),
            
            # Order processing sensitive data
            # Order IDs (hexadecimal patterns)
            (r'\b[a-f0-9]{24}\b', '[ORDER_ID_REDACTED]'),
            # Customer names and company names (after "Customer: ")
            (r'Customer:\s+[^(]+\([^)]+\)', 'Customer: [CUSTOMER_REDACTED]'),
            # Financial amounts (prices, totals)
            (r'Total:\s+[\d.,]+', 'Total: [AMOUNT_REDACTED]'),
            (r'Price:\s+[\d.,]+', 'Price: [AMOUNT_REDACTED]'),
            (r'Subtotal:\s+[\d.,]+', 'Subtotal: [AMOUNT_REDACTED]'),
            # Product references (numeric patterns that could be SKUs)
            (r'References:\s+[\d\s,]+', 'References: [REFERENCES_REDACTED]'),
            # Order numbers in various formats
            (r'Order\s+#?\d+', 'Order [ORDER_NUMBER_REDACTED]'),
            # General numeric IDs that might be sensitive
            (r'ID:\s*\d+', 'ID: [ID_REDACTED]'),
        ]
    
    def filter(self, record):
        """
        Filter log record to redact sensitive data.
        
        Args:
            record: LogRecord object
            
        Returns:
            True to allow the record, False to drop it
        """
        # Apply sensitive data redaction to the log message
        if hasattr(record, 'msg') and record.msg:
            message = str(record.msg)
            
            # Apply all patterns
            for pattern, replacement in self.sensitive_patterns:
                message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
            
            record.msg = message
        
        # Also filter any arguments
        if hasattr(record, 'args') and record.args:
            filtered_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    filtered_arg = arg
                    for pattern, replacement in self.sensitive_patterns:
                        filtered_arg = re.sub(pattern, replacement, filtered_arg, flags=re.IGNORECASE)
                    filtered_args.append(filtered_arg)
                else:
                    filtered_args.append(arg)
            record.args = tuple(filtered_args)
        
        return True