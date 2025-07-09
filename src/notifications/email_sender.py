"""
Email notification system for Conway bike orders.
Handles email template generation and sending notifications.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any
from datetime import datetime
import pytz
from config.settings import settings

logger = logging.getLogger(__name__)

class EmailSender:
    """
    Handles email notifications for Conway bike orders.
    Creates standardized email templates and sends notifications.
    """
    
    def __init__(self):
        """Initialize email sender with configuration from settings."""
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.EMAIL_USERNAME
        self.password = settings.EMAIL_PASSWORD
        self.from_email = settings.EMAIL_FROM
        self.target_email = settings.TARGET_EMAIL
        self.subject_prefix = settings.EMAIL_SUBJECT_PREFIX
        
        logger.info("Email sender initialized")
    
    def _create_order_summary_html(self, orders: List[Dict[str, Any]]) -> str:
        """
        Create HTML formatted order summary.
        
        Args:
            orders: List of filtered orders containing bike references
            
        Returns:
            HTML formatted string with order details
        """
        # Calculate summary statistics
        total_orders = len(orders)
        total_items = 0
        unique_references = set()
        
        # Collect statistics from all orders
        for order in orders:
            if 'products' in order:
                total_items += len(order.get('products', []))
            elif 'items' in order:
                total_items += len(order.get('items', []))
            if 'matching_references' in order:
                unique_references.update(order['matching_references'])
        
        # Create HTML content
        html_content = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .summary {{
                    background-color: #ecf0f1;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .order {{
                    border: 1px solid #bdc3c7;
                    margin-bottom: 20px;
                    border-radius: 5px;
                    overflow: hidden;
                }}
                .order-header {{
                    background-color: #3498db;
                    color: white;
                    padding: 10px 15px;
                    font-weight: bold;
                }}
                .order-content {{
                    padding: 15px;
                }}
                .item {{
                    background-color: #f8f9fa;
                    margin: 5px 0;
                    padding: 10px;
                    border-left: 4px solid #27ae60;
                }}
                .bike-reference {{
                    background-color: #e74c3c;
                    color: white;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 0.9em;
                    margin: 2px;
                    display: inline-block;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #bdc3c7;
                    font-size: 0.9em;
                    color: #7f8c8d;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚴 Conway Bikes Order Alert</h1>
                <p>New sales orders containing Conway bike references have been detected</p>
            </div>
            
            <div class="summary">
                <h2>📊 Summary</h2>
                <ul>
                    <li><strong>Total Orders:</strong> {total_orders}</li>
                    <li><strong>Total Items:</strong> {total_items}</li>
                    <li><strong>Unique Bike References Found:</strong> {len(unique_references)}</li>
                    <li><strong>Time Period:</strong> Last 24 hours (since yesterday 9:00 AM Madrid time)</li>
                </ul>
                
                <h3>🏷️ Bike References Found:</h3>
                <div>
                    {' '.join(f'<span class="bike-reference">{ref}</span>' for ref in sorted(unique_references))}
                </div>
            </div>
        """
        
        # Add detailed order information
        for i, order in enumerate(orders, 1):
            order_id = order.get('id', 'Unknown')
            order_date = order.get('date', 'Unknown')
            # Handle contact field - can be string ID or dict
            contact = order.get('contact', {})
            contact_name = contact.get('name', 'Unknown Customer') if isinstance(contact, dict) else 'Unknown Customer'
            customer_name = order.get('contactName', contact_name)
            order_total = order.get('total', 'N/A')
            
            html_content += f"""
            <div class="order">
                <div class="order-header">
                    Order #{i}: {order_id}
                </div>
                <div class="order-content">
                    <p><strong>Customer:</strong> {customer_name}</p>
                    <p><strong>Date:</strong> {order_date}</p>
                    <p><strong>Total:</strong> {order_total}</p>
                    
                    <h4>📦 Items:</h4>
            """
            
            # Add order items/products
            items = order.get('products', order.get('items', []))
            if items:
                for item in items:
                    item_name = item.get('name', 'Unknown Item')
                    item_code = item.get('code', item.get('sku', ''))
                    item_qty = item.get('units', item.get('quantity', 1))
                    item_price = item.get('price', 'N/A')
                    
                    html_content += f"""
                    <div class="item">
                        <strong>{item_name}</strong>
                        {f'<br>Code: {item_code}' if item_code else ''}
                        <br>Quantity: {item_qty} | Price: {item_price}
                    </div>
                    """
            else:
                # If no items/products array, show order description
                order_desc = order.get('desc', order.get('description', 'No description available'))
                html_content += f"""
                <div class="item">
                    <strong>Order Description:</strong><br>
                    {order_desc}
                </div>
                """
            
            # Show matching bike references for this order
            matching_refs = order.get('matching_references', [])
            if matching_refs:
                html_content += f"""
                <p><strong>🎯 Matching Bike References:</strong></p>
                <div>
                    {' '.join(f'<span class="bike-reference">{ref}</span>' for ref in matching_refs)}
                </div>
                """
            
            html_content += """
                </div>
            </div>
            """
        
        # Add footer
        madrid_tz = pytz.timezone(settings.TIMEZONE)
        current_time = datetime.now(madrid_tz).strftime("%Y-%m-%d %H:%M:%S %Z")
        
        html_content += f"""
            <div class="footer">
                <p>This alert was generated automatically by the Conway Bikes monitoring system.</p>
                <p>Generated on: {current_time}</p>
                <p>For questions or issues, please contact your system administrator.</p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _create_plain_text_summary(self, orders: List[Dict[str, Any]]) -> str:
        """
        Create plain text formatted order summary.
        
        Args:
            orders: List of filtered orders containing bike references
            
        Returns:
            Plain text formatted string with order details
        """
        # Calculate summary statistics
        total_orders = len(orders)
        total_items = 0
        unique_references = set()
        
        for order in orders:
            if 'products' in order:
                total_items += len(order.get('products', []))
            elif 'items' in order:
                total_items += len(order.get('items', []))
            if 'matching_references' in order:
                unique_references.update(order['matching_references'])
        
        # Create plain text content
        text_content = f"""
CONWAY BIKES ORDER ALERT
========================

New sales orders containing Conway bike references have been detected.

SUMMARY:
--------
• Total Orders: {total_orders}
• Total Items: {total_items}  
• Unique Bike References Found: {len(unique_references)}
• Time Period: Last 24 hours (since yesterday 9:00 AM Madrid time)

BIKE REFERENCES FOUND:
---------------------
{', '.join(sorted(unique_references))}

DETAILED ORDERS:
===============
"""
        
        # Add detailed order information
        for i, order in enumerate(orders, 1):
            order_id = order.get('id', 'Unknown')
            order_date = order.get('date', 'Unknown')
            # Handle contact field - can be string ID or dict
            contact = order.get('contact', {})
            contact_name = contact.get('name', 'Unknown Customer') if isinstance(contact, dict) else 'Unknown Customer'
            customer_name = order.get('contactName', contact_name)
            order_total = order.get('total', 'N/A')
            
            text_content += f"""
Order #{i}: {order_id}
--------------------
Customer: {customer_name}
Date: {order_date}
Total: {order_total}

Items:
"""
            
            # Add order items/products
            items = order.get('products', order.get('items', []))
            if items:
                for item in items:
                    item_name = item.get('name', 'Unknown Item')
                    item_code = item.get('code', item.get('sku', ''))
                    item_qty = item.get('units', item.get('quantity', 1))
                    item_price = item.get('price', 'N/A')
                    
                    text_content += f"  • {item_name}"
                    if item_code:
                        text_content += f" (Code: {item_code})"
                    text_content += f" | Qty: {item_qty} | Price: {item_price}\n"
            else:
                # If no items/products array, show order description
                order_desc = order.get('desc', order.get('description', 'No description available'))
                text_content += f"  Order Description: {order_desc}\n"
            
            # Show matching bike references for this order
            matching_refs = order.get('matching_references', [])
            if matching_refs:
                text_content += f"\nMatching Bike References: {', '.join(matching_refs)}\n"
            
            text_content += "\n"
        
        # Add footer
        madrid_tz = pytz.timezone(settings.TIMEZONE)
        current_time = datetime.now(madrid_tz).strftime("%Y-%m-%d %H:%M:%S %Z")
        
        text_content += f"""
---
This alert was generated automatically by the Conway Bikes monitoring system.
Generated on: {current_time}
For questions or issues, please contact your system administrator.
"""
        
        return text_content
    
    def send_order_notification(self, orders: List[Dict[str, Any]]) -> bool:
        """
        Send email notification about Conway bike orders.
        
        Args:
            orders: List of filtered orders containing bike references
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            if not orders:
                logger.info("No orders to send notification for")
                return True
            
            # Create email message
            msg = MIMEMultipart('alternative')
            
            # Email subject
            order_count = len(orders)
            subject = f"{self.subject_prefix} {order_count} New Conway Bike Order{'s' if order_count != 1 else ''} Detected"
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = self.target_email
            
            # Create both plain text and HTML versions
            text_content = self._create_plain_text_summary(orders)
            html_content = self._create_order_summary_html(orders)
            
            # Attach both versions
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            logger.info(f"Sending email notification to {self.target_email}")
            
            if settings.TEST_EMAIL_ONLY:
                logger.info("TEST_EMAIL_ONLY mode: Email content prepared but not sent")
                logger.debug(f"Email subject: {subject}")
                logger.debug(f"Email content preview: {text_content[:200]}...")
                return True
            
            # Connect to SMTP server and send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Enable TLS encryption
                server.login(self.username, self.password)
                
                # Send email
                text = msg.as_string()
                server.sendmail(self.from_email, self.target_email, text)
            
            logger.info(f"Email notification sent successfully to {self.target_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False
    
    def test_email_connection(self) -> bool:
        """
        Test email server connection and authentication.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            logger.info("Testing email server connection...")
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
            
            logger.info("Email server connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"Email server connection test failed: {e}")
            return False
    
    def send_test_email(self) -> bool:
        """
        Send a test email to verify email functionality.
        
        Returns:
            True if test email was sent successfully, False otherwise
        """
        try:
            # Create a simple test message
            msg = MIMEText("This is a test email from the Conway Bikes monitoring system.", 'plain', 'utf-8')
            msg['Subject'] = f"{self.subject_prefix} Test Email"
            msg['From'] = self.from_email
            msg['To'] = self.target_email
            
            # Send test email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                text = msg.as_string()
                server.sendmail(self.from_email, self.target_email, text)
            
            logger.info(f"Test email sent successfully to {self.target_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send test email: {e}")
            return False 