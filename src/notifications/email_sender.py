"""
Email notification system for Conway bike orders.
Handles email template generation and sending notifications.
"""

import smtplib
import logging
import base64
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any, Union, Set
from datetime import datetime
import pytz
from config.settings import settings

logger = logging.getLogger(__name__)

class EmailSender:
    """
    Handles email notifications for Conway bike orders.
    Creates standardized email templates and sends notifications.
    """
    
    def __init__(self, bike_references: Set[str] = None):
        """
        Initialize email sender with configuration from settings.
        
        Args:
            bike_references: Set of Conway bike references for filtering items. 
                           Can be set later via set_bike_references method.
        """
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.EMAIL_USERNAME
        self.password = settings.EMAIL_PASSWORD
        self.from_email = settings.EMAIL_FROM
        self.target_email = settings.TARGET_EMAIL
        
        # Store bike references for item filtering
        self.bike_references = bike_references or set()
        
        logger.info("Email sender initialized")
    
    def set_bike_references(self, bike_references: Set[str]) -> None:
        """
        Set the bike references for filtering Conway items in orders.
        
        Args:
            bike_references: Set of Conway bike references from CSV
        """
        self.bike_references = bike_references or set()
        logger.debug(f"Bike references set for filtering: {len(self.bike_references)} references")
    
    def _contains_bike_reference(self, text: str) -> bool:
        """
        Check if text contains any Conway bike reference.
        
        Args:
            text: Text to search for bike references
            
        Returns:
            True if any bike reference is found in the text
        """
        if not text or not self.bike_references:
            return False
        
        # Normalize text for comparison (remove extra spaces, but keep original case for numbers)
        normalized_text = ' '.join(text.split())
        
        # Check if any bike reference is present in the text
        for reference in self.bike_references:
            if reference in normalized_text:
                return True
        
        return False
    
    def _find_matching_references_in_text(self, text: str) -> List[str]:
        """
        Find all Conway bike references present in the given text.
        
        Args:
            text: Text to search for bike references
            
        Returns:
            List of matching bike references found in the text
        """
        if not text or not self.bike_references:
            return []
        
        # Normalize text for comparison (remove extra spaces, but keep original case for numbers)
        normalized_text = ' '.join(text.split())
        
        # Find all matching references (avoid duplicates by using set)
        matches = set()
        for reference in self.bike_references:
            if reference in normalized_text:
                matches.add(reference)
        
        return list(matches)
    
    def _filter_conway_items_from_order(self, order: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Filter order items to only include those containing Conway bike references.
        
        Args:
            order: Order dictionary containing products or items
            
        Returns:
            List of items that contain Conway bike references
        """
        if not self.bike_references:
            logger.warning("No bike references available for filtering items")
            return []
        
        conway_items = []
        
        # Check products/items in the order
        items = order.get('products', order.get('items', []))
        
        for item in items:
            # Check various fields where bike references might appear
            search_fields = [
                item.get('name', ''),
                item.get('desc', ''),
                item.get('description', ''),
                item.get('code', ''),
                item.get('sku', ''),
            ]
            
            # Combine all searchable text for this item
            combined_text = ' '.join(str(field) for field in search_fields if field)
            
            # Check if this item contains any Conway bike reference
            if self._contains_bike_reference(combined_text):
                # Add matching references to item data for display
                item_copy = item.copy()
                item_copy['matching_references'] = self._find_matching_references_in_text(combined_text)
                conway_items.append(item_copy)
        
        logger.debug(f"Filtered {len(conway_items)} Conway items from {len(items)} total items in order")
        
        return conway_items
    
    def _format_date(self, date_input: Union[str, int, float, None]) -> str:
        """
        Format various date inputs to DD/MM/YYYY HH:MM format.
        
        Args:
            date_input: Date in various formats (ISO string, Unix timestamp, etc.)
            
        Returns:
            Formatted date string in DD/MM/YYYY HH:MM format, or 'Unknown' if parsing fails
        """
        if not date_input:
            return 'Unknown'
        
        try:
            madrid_tz = pytz.timezone(settings.TIMEZONE)
            
            # Handle Unix timestamp (int or float)
            if isinstance(date_input, (int, float)):
                dt = datetime.fromtimestamp(date_input, tz=madrid_tz)
                return dt.strftime("%d/%m/%Y %H:%M")
            
            # Handle string inputs
            if isinstance(date_input, str):
                # Try different parsing approaches
                dt = None
                
                # Try ISO format with timezone (e.g., "2024-01-15T10:30:00Z")
                try:
                    if date_input.endswith('Z'):
                        dt = datetime.fromisoformat(date_input.replace('Z', '+00:00'))
                    elif 'T' in date_input:
                        dt = datetime.fromisoformat(date_input)
                    else:
                        # Try parsing as YYYY-MM-DD HH:MM:SS format
                        dt = datetime.strptime(date_input, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass
                
                # Try Unix timestamp as string
                if dt is None:
                    try:
                        timestamp = float(date_input)
                        dt = datetime.fromtimestamp(timestamp, tz=madrid_tz)
                    except ValueError:
                        pass
                
                # Try other common formats
                if dt is None:
                    common_formats = [
                        "%Y-%m-%d",
                        "%d/%m/%Y",
                        "%d-%m-%Y",
                        "%Y/%m/%d",
                        "%d/%m/%Y %H:%M",
                        "%d-%m-%Y %H:%M",
                        "%Y-%m-%d %H:%M"
                    ]
                    
                    for fmt in common_formats:
                        try:
                            dt = datetime.strptime(date_input, fmt)
                            break
                        except ValueError:
                            continue
                
                if dt:
                    # Convert to Madrid timezone if not timezone-aware
                    if dt.tzinfo is None:
                        dt = madrid_tz.localize(dt)
                    else:
                        dt = dt.astimezone(madrid_tz)
                    
                    return dt.strftime("%d/%m/%Y %H:%M")
            
            return 'Unknown'
            
        except Exception as e:
            logger.warning(f"Failed to parse date '{date_input}': {e}")
            return 'Unknown'
    
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
        total_conway_items = 0
        unique_references = set()
        
        # Collect statistics from all orders - only count Conway items
        for order in orders:
            conway_items = self._filter_conway_items_from_order(order)
            total_conway_items += len(conway_items)
            if 'matching_references' in order:
                unique_references.update(order['matching_references'])
        
        # Get the logo as base64 for embedding
        logo_src = self._get_logo_base64()
        
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
                    background-color: #ecf0f1;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                    color: #000000;
                }}
                .summary {{
                    background-color: #ecf0f1;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                    color: #000000;
                }}
                .order {{
                    border: 1px solid #bdc3c7;
                    margin-bottom: 20px;
                    border-radius: 5px;
                    overflow: hidden;
                    color: #000000;
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
                    color: #000000;
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
                .footer-text {{
                    color: #7f8c8d;
                }}
                span {{
                    color: #000000;
                }}
                div {{
                    color: #000000;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Proffectiv - Conway Bikes Order Alert</h1>
                <p>New sales orders containing Conway bike references have been detected</p>
            </div>
            
            <div class="summary">
                <h2>Summary</h2>
                <ul>
                    <li><strong>Total Orders:</strong> {total_orders}</li>
                    <li><strong>Conway Items:</strong> {total_conway_items}</li>
                    <li><strong>Unique Bike References Found:</strong> {len(unique_references)}</li>
                </ul>
                
                <h3>Bike References Found:</h3>
                <div>
                    {' '.join(f'<div class="bike-reference">{ref}</div>' for ref in sorted(unique_references))}
                </div>
            </div>
        """
        
        # Add detailed order information
        for i, order in enumerate(orders, 1):
            order_date = self._format_date(order.get('date'))
            # Handle contact field - can be string ID or dict
            contact = order.get('contact', {})
            contact_name = contact.get('name', 'Unknown Customer') if isinstance(contact, dict) else 'Unknown Customer'
            customer_name = order.get('contactName', contact_name)
            order_total = round(float(order.get('total', 'N/A')),2)
            
            html_content += f"""
            <div class="order">
                <div class="order-header">
                    Order #{i}
                </div>
                <div class="order-content">
                    <p><strong>Customer:</strong> {customer_name}</p>
                    <p><strong>Date:</strong> {order_date}</p>
                    <p><strong>Total:</strong> {order_total} €</p>
                    
                    <h4>Conway Items:</h4>
            """
            
            # Add only Conway items from the order
            conway_items = self._filter_conway_items_from_order(order)
            if conway_items:
                for item in conway_items:
                    item_name = item.get('name', 'Unknown Item')
                    item_code = item.get('code', item.get('sku', ''))
                    item_qty = item.get('units', item.get('quantity', 1))
                    item_price = round(float(item.get('price', 'N/A')),2)
                    
                    # Get matching references for this specific item
                    item_refs = item.get('matching_references', [])
                    refs_display = f" - References: {', '.join(item_refs)}" if item_refs else ""
                    
                    html_content += f"""
                    <div class="item">
                        <strong>{item_name}</strong>{refs_display}
                        {f'<br>Code: {item_code}' if item_code else ''}
                        <br>Quantity: {item_qty} | Price: {item_price} €
                    </div>
                    """
            else:
                # If no Conway items found, show message
                html_content += f"""
                <div class="item">
                    <strong>No Conway items found in this order.</strong><br>
                    (Conway references detected in order description or other fields)
                </div>
                """
            
            # Show matching bike references for this order
            matching_refs = order.get('matching_references', [])
            if matching_refs:
                html_content += f"""
                <p><strong>Matching Bike References:</strong></p>
                <div>
                    {' '.join(f'<div class="bike-reference">{ref}</div>' for ref in matching_refs)}
                </div>
                """
            
            html_content += """
                </div>
            </div>
            """
        
        # Add footer
        madrid_tz = pytz.timezone(settings.TIMEZONE)
        current_time = datetime.now(madrid_tz).strftime("%d/%m/%Y %H:%M")
        
        html_content += f"""
            <div class="footer">
                <p class="footer-text">This alert was generated automatically by the Proffectiv - Conway Bikes monitoring system.</p>
                <p class="footer-text">Generated on: {current_time}</p>
                <p class="footer-text">For questions or issues, please contact miguel@proffectiv.com.</p>
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
        total_conway_items = 0
        unique_references = set()
        
        for order in orders:
            conway_items = self._filter_conway_items_from_order(order)
            total_conway_items += len(conway_items)
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
• Conway Items: {total_conway_items}  
• Unique Bike References Found: {len(unique_references)}

BIKE REFERENCES FOUND:
---------------------
{', '.join(sorted(unique_references))}

DETAILED ORDERS:
===============
"""
        
        # Add detailed order information
        for i, order in enumerate(orders, 1):
            order_date = self._format_date(order.get('date'))
            # Handle contact field - can be string ID or dict
            contact = order.get('contact', {})
            contact_name = contact.get('name', 'Unknown Customer') if isinstance(contact, dict) else 'Unknown Customer'
            customer_name = order.get('contactName', contact_name)
            order_total = round(float(order.get('total', 'N/A')),2)
            
            text_content += f"""
Order #{i}
--------------------
Customer: {customer_name}
Date: {order_date}
Total: {order_total} €

Conway Items:
"""
            
            # Add only Conway items from the order
            conway_items = self._filter_conway_items_from_order(order)
            if conway_items:
                for item in conway_items:
                    item_name = item.get('name', 'Unknown Item')
                    item_code = item.get('code', item.get('sku', ''))
                    item_qty = item.get('units', item.get('quantity', 1))
                    item_price = round(float(item.get('price', 'N/A')),2)
                    
                    # Get matching references for this specific item
                    item_refs = item.get('matching_references', [])
                    refs_display = f" - References: {', '.join(item_refs)}" if item_refs else ""
                    
                    text_content += f"  • {item_name}{refs_display}"
                    if item_code:
                        text_content += f" (SKU: {item_code})"
                    text_content += f" | Qty: {item_qty} | Price: {item_price} €\n"
            else:
                # If no Conway items found, show message
                text_content += "  No Conway items found in this order.\n"
                text_content += "  (Conway references detected in order description or other fields)\n"
            
            # Show matching bike references for this order
            matching_refs = order.get('matching_references', [])
            if matching_refs:
                text_content += f"\nMatching Bike References: {', '.join(matching_refs)}\n"
            
            text_content += "\n"
        
        # Add footer
        madrid_tz = pytz.timezone(settings.TIMEZONE)
        current_time = datetime.now(madrid_tz).strftime("%d/%m/%Y %H:%M")
        
        text_content += f"""
---
<div class="footer">
<p class="footer-text">This alert was generated automatically by the Proffectiv - Conway Bikes monitoring system.</p>
<p class="footer-text">Generated on: {current_time}</p>
<p class="footer-text">For questions or issues, please contact miguel@proffectiv.com.</p>
</div>
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
            subject = f"[Proffectiv - New Orders] {order_count} New Conway Bike Order{'s' if order_count != 1 else ''} Detected"
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
        Send a test email using the actual email template with sample data.
        This allows testing the full email styling and logo display.
        
        Returns:
            True if test email was sent successfully, False otherwise
        """
        try:
            # Set up test bike references for filtering demo
            test_bike_references = {'EMR627', 'CS527', 'Conway'}
            original_bike_references = self.bike_references
            self.bike_references = test_bike_references
            
            # Create sample order data to test the template
            # Using different date formats to test the parser
            sample_orders = [
                {
                    'id': 'TEST-ORDER-001',
                    'date': '2024-01-15T10:30:00Z',  # ISO format with Z
                    'contact': {
                        'name': 'Test Customer A'
                    },
                    'total': '1299.99',
                    'products': [
                        {
                            'name': 'Conway EMR 627 2024',
                            'code': 'EMR627-2024',
                            'units': 1,
                            'price': '1299.99'
                        }
                    ],
                    'matching_references': ['EMR627']
                },
                {
                    'id': 'TEST-ORDER-002', 
                    'date': 1705320900,  # Unix timestamp (15/01/2024 14:15)
                    'contactName': 'Test Customer B',
                    'total': '2899.50',
                    'items': [
                        {
                            'name': 'Conway Cairon S 527 2024',
                            'sku': 'CS527-2024-L',
                            'quantity': 1,
                            'price': '2499.00'
                        },
                        {
                            'name': 'Conway Helmet Pro',
                            'sku': 'HELM-PRO-001',
                            'quantity': 1,
                            'price': '89.99'
                        },
                        {
                            'name': 'Non-Conway Item Regular Helmet',
                            'sku': 'REG-HELM-001',
                            'quantity': 1,
                            'price': '49.99'
                        }
                    ],
                    'matching_references': ['CS527']
                }
            ]
            
            # Create email message using the actual template
            msg = MIMEMultipart('alternative')
            
            # Email subject with TEST prefix
            subject = f"[Proffectiv - New Orders] [TEST] 2 New Conway Bike Orders Detected - Template Preview"
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = self.target_email
            
            # Create both plain text and HTML versions using actual templates
            text_content = self._create_plain_text_summary(sample_orders)
            html_content = self._create_order_summary_html(sample_orders)
            
            # Add test notice to both versions
            test_notice_text = """
*** THIS IS A TEST EMAIL ***
This email demonstrates the actual template and styling that will be used for Conway bike order notifications.
The orders shown above are sample data for testing purposes only.
===========================================

"""
            
            test_notice_html = """
            <div style="background-color: #f39c12; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; text-align: center; font-weight: bold;">
                ⚠️ THIS IS A TEST EMAIL ⚠️<br>
                This email demonstrates the actual template and styling that will be used for Conway bike order notifications.<br>
                The orders shown below are sample data for testing purposes only.
            </div>
            """
            
            # Prepend test notice to content
            text_content = test_notice_text + text_content
            html_content = html_content.replace('<div class="header">', test_notice_html + '<div class="header">')
            
            # Attach both versions
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Send test email
            logger.info(f"Sending template test email to {self.target_email}")
            
            if settings.TEST_EMAIL_ONLY:
                logger.info("TEST_EMAIL_ONLY mode: Template test email content prepared but not sent")
                logger.debug(f"Email subject: {subject}")
                logger.debug(f"Email content preview: {text_content[:300]}...")
                return True
            
            # Connect to SMTP server and send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                text = msg.as_string()
                server.sendmail(self.from_email, self.target_email, text)
            
            logger.info(f"Template test email sent successfully to {self.target_email}")
            
            # Restore original bike references
            self.bike_references = original_bike_references
            return True
            
        except Exception as e:
            logger.error(f"Failed to send template test email: {e}")
            # Restore original bike references even on error
            if 'original_bike_references' in locals():
                self.bike_references = original_bike_references
            return False 