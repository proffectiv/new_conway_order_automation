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