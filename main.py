#!/usr/bin/env python3
"""
Conway Bikes Order Monitoring Automation
Main entry point for the Holded API monitoring system.

This script provides command-line interface for:
- Running daily checks manually
- Testing all system components
- Running the scheduler for automated daily execution
- Getting system status

Usage:
    python main.py check        # Run daily check manually
    python main.py test         # Test all components
    python main.py schedule     # Run continuous scheduler
    python main.py status       # Get system status
    python main.py --help       # Show help
"""

import sys
import os
import argparse
import json
import time
import signal
from datetime import datetime, timedelta
from pathlib import Path
import pytz

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import our modules
from src.main_workflow import WorkflowOrchestrator
from src.config.settings import settings

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print("\n🛑 Shutdown signal received. Exiting gracefully...")
    sys.exit(0)

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

def print_banner():
    """Print application banner."""
    print("=" * 60)
    print("🚴 Conway Bikes Order Monitoring Automation")
    print("   Holded API Integration System")
    print("=" * 60)

def print_result_summary(result: dict):
    """Print a formatted summary of workflow results."""
    print("\n📊 Execution Summary:")
    print("-" * 40)
    print(f"✅ Success: {'Yes' if result['success'] else 'No'}")
    print(f"📦 Total Orders Retrieved: {result['total_orders_retrieved']}")
    
    # Show duplicate prevention info
    duplicates_filtered = result.get('duplicate_orders_filtered', 0)
    if duplicates_filtered > 0:
        print(f"🔄 Duplicates Filtered: {duplicates_filtered}")
    
    print(f"🚴 Orders with Bikes: {result['filtered_orders_count']}")
    print(f"📧 Email Sent: {'Yes' if result['email_sent'] else 'No'}")
    print(f"🏷️  Bike References Loaded: {result['bike_references_loaded']}")
    
    if result['errors']:
        print(f"\n❌ Errors ({len(result['errors'])}):")
        for error in result['errors']:
            print(f"   • {error}")
    
    if result['orders_with_bikes']:
        print(f"\n🎯 Found Conway Bike Orders:")
        for i, order in enumerate(result['orders_with_bikes'], 1):
            order_id = order.get('id', 'Unknown')
            customer = order.get('contactName', 'Unknown Customer')
            matching_refs = order.get('matching_references', [])
            print(f"   {i}. Order {order_id} - {customer}")
            if matching_refs:
                print(f"      References: {', '.join(matching_refs)}")

def print_frequent_result_summary(result: dict):
    """Print a formatted summary of frequent workflow results."""
    print("\n📊 Frequent Check Summary:")
    print("-" * 40)
    print(f"✅ Success: {'Yes' if result['success'] else 'No'}")
    print(f"⏰ Within Operation Hours: {'Yes' if result['within_operation_hours'] else 'No'}")
    
    if result.get('skipped'):
        skip_reason_map = {
            'outside_operation_hours': '🕐 Outside operation hours',
            'no_recent_orders': '📦 No recent orders found',
            'no_bike_orders': '🚴 No bike orders found',
            'all_orders_already_processed': '🔄 All orders already processed (no duplicates)'
        }
        skip_reason = skip_reason_map.get(result.get('skip_reason'), 'Unknown reason')
        print(f"⏭️ Skipped: {skip_reason}")
    else:
        print(f"📈 Orders Retrieved: {result.get('total_orders_retrieved', 0)}")
        
        # Show duplicate prevention info
        duplicates_filtered = result.get('duplicate_orders_filtered', 0)
        if duplicates_filtered > 0:
            print(f"🔄 Duplicates Filtered: {duplicates_filtered}")
        
        print(f"🚴 Bike Orders Found: {result.get('filtered_orders_count', 0)}")
        print(f"📧 Email Sent: {'Yes' if result.get('email_sent') else 'No'}")
        print(f"📚 Bike References Loaded: {result.get('bike_references_loaded', 0)}")
    
    # Show any errors
    errors = result.get('errors', [])
    if errors:
        print(f"\n❌ Errors ({len(errors)}):")
        for error in errors:
            print(f"   • {error}")
    
    # Show order details if available
    orders_with_bikes = result.get('orders_with_bikes', [])
    if orders_with_bikes:
        print(f"\n🚴 Conway Bike Orders Found:")
        for i, order in enumerate(orders_with_bikes, 1):
            # Safely get order information with fallbacks
            order_id = order.get('id', 'Unknown') if isinstance(order, dict) else 'Unknown'
            
            # Handle contact field - can be string ID or dict
            contact = order.get('contact', {}) if isinstance(order, dict) else {}
            if isinstance(contact, dict):
                contact_name = contact.get('name', 'Unknown Customer')
            else:
                contact_name = 'Unknown Customer'
            
            customer_name = order.get('contactName', contact_name) if isinstance(order, dict) else 'Unknown Customer'
            order_total = order.get('total', 'N/A') if isinstance(order, dict) else 'N/A'
            
            print(f"   {i}. Order {order_id}")
            print(f"      Customer: {customer_name}")
            print(f"      Total: {order_total}")
            
            matching_refs = order.get('matching_references', []) if isinstance(order, dict) else []
            if matching_refs:
                print(f"      References: {', '.join(matching_refs)}")

def run_frequent_check(args):
    """Run the frequent check workflow."""
    print("\n⚡ Starting frequent Conway bike order check...")
    
    try:
        # Initialize workflow orchestrator
        workflow = WorkflowOrchestrator()
        
        # Run the frequent check
        result = workflow.run_frequent_check()
        
        # Print results
        print_frequent_result_summary(result)
        
        # Return appropriate exit code
        return 0 if result['success'] else 1
        
    except Exception as e:
        print(f"\n❌ Critical error during frequent check: {e}")
        return 1

def run_daily_check(args):
    """Run the daily check workflow."""
    print("\n🔍 Starting daily Conway bike order check...")
    
    try:
        # Initialize workflow orchestrator
        workflow = WorkflowOrchestrator()
        
        # Run the daily check
        result = workflow.run_daily_check()
        
        # Print results
        print_result_summary(result)
        
        # Return appropriate exit code
        return 0 if result['success'] else 1
        
    except Exception as e:
        print(f"\n❌ Critical error during daily check: {e}")
        return 1

def test_components(args):
    """Test all system components."""
    print("\n🧪 Testing all system components...")
    
    try:
        # Initialize workflow orchestrator
        workflow = WorkflowOrchestrator()
        
        # Run component tests
        test_results = workflow.test_all_components()
        
        # Print test results
        print("\n📊 Component Test Results:")
        print("-" * 40)
        
        for component, result in test_results.items():
            if component == 'overall_success':
                continue
                
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{component}: {status}")
            
            if result.get('error'):
                print(f"   Error: {result['error']}")
            
            if result.get('stats'):
                stats = result['stats']
                if component == 'csv_processor':
                    print(f"   References loaded: {stats['total_references']}")
                    print(f"   File path: {stats['file_path']}")
        
        overall_status = "✅ ALL TESTS PASSED" if test_results['overall_success'] else "❌ SOME TESTS FAILED"
        print(f"\nOverall Result: {overall_status}")
        
        # Return appropriate exit code
        return 0 if test_results['overall_success'] else 1
        
    except Exception as e:
        print(f"\n❌ Critical error during component testing: {e}")
        return 1

def show_status(args):
    """Show system status and configuration."""
    print("\n📋 System Status and Configuration...")
    
    try:
        # Initialize workflow orchestrator
        workflow = WorkflowOrchestrator()
        
        # Get system status
        status = workflow.get_system_status()
        
        # Print status information
        print("\n🖥️  System Information:")
        print("-" * 40)
        print(f"Current Time: {status['timestamp']}")
        print(f"Timezone: {status['timezone']}")
        print(f"Schedule: {status['schedule']['next_run_description']}")
        
        print("\n⚙️  Configuration:")
        print("-" * 40)
        config = status['configuration']
        print(f"CSV File: {config['csv_file']}")
        print(f"API Base URL: {config['api_base_url']}")
        print(f"Target Email: {config['target_email']}")
        print(f"Test Mode: {'Yes' if config['test_mode'] else 'No'}")
        print(f"Test Email Only: {'Yes' if config['test_email_only'] else 'No'}")
        
        if status['csv_stats']:
            print("\n📄 CSV File Statistics:")
            print("-" * 40)
            csv_stats = status['csv_stats']
            print(f"File Exists: {'Yes' if csv_stats['file_exists'] else 'No'}")
            print(f"Total References: {csv_stats['total_references']}")
            print(f"Total Rows: {csv_stats['total_rows']}")
        
        if status['errors']:
            print(f"\n❌ Errors ({len(status['errors'])}):")
            for error in status['errors']:
                print(f"   • {error}")
        
        print("\n🔧 Configuration Summary:")
        print("-" * 40)
        print(f"📧 Target Email: {settings.TARGET_EMAIL}")
        print(f"🌍 Timezone: {settings.TIMEZONE}")
        print(f"📊 CSV File: {settings.CSV_FILE_PATH}")
        print(f"📝 Log Level: {settings.LOG_LEVEL}")
        print(f"⏰ Daily Schedule: {settings.SCHEDULE_HOUR:02d}:{settings.SCHEDULE_MINUTE:02d} Madrid time")
        print(f"🕐 Operation Hours: {settings.OPERATION_START_HOUR:02d}:00 - {settings.OPERATION_END_HOUR:02d}:00")
        print(f"⏱️ Check Delay: {settings.CHECK_DELAY_MINUTES} minutes")
        print(f"🧪 Test Mode: {'Enabled' if settings.TEST_MODE else 'Disabled'}")
        print(f"📨 Test Email Only: {'Enabled' if settings.TEST_EMAIL_ONLY else 'Disabled'}")
        
        # Show processed orders tracker stats
        try:
            from src.utils.processed_orders import ProcessedOrdersTracker
            tracker = ProcessedOrdersTracker()
            stats = tracker.get_stats()
            
            print("\n🔄 Duplicate Prevention Status:")
            print("-" * 40)
            print(f"📋 Total Processed Orders: {stats['total_processed_orders']}")
            print(f"💾 Storage File: {stats['storage_file']}")
            print(f"📁 Storage Exists: {'Yes' if stats['storage_file_exists'] else 'No'}")
            
            if stats['oldest_record']:
                print(f"📅 Oldest Record: {stats['oldest_record']}")
            if stats['newest_record']:
                print(f"📅 Newest Record: {stats['newest_record']}")
                
        except Exception as e:
            print(f"\n⚠️ Duplicate Prevention: Error loading stats - {e}")
        
        # Show current time and operation status
        madrid_tz = pytz.timezone(settings.TIMEZONE)
        current_time = datetime.now(madrid_tz)
        current_hour = current_time.hour
        is_operational = settings.OPERATION_START_HOUR <= current_hour < settings.OPERATION_END_HOUR
        
        print("\n⏰ Current Status:")
        print("-" * 40)
        print(f"🕐 Current Time: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"🔄 Currently Operational: {'Yes' if is_operational else 'No'}")
        if not is_operational:
            next_start = current_time.replace(hour=settings.OPERATION_START_HOUR, minute=0, second=0, microsecond=0)
            if current_hour >= settings.OPERATION_END_HOUR:
                next_start += timedelta(days=1)  # Next day
            print(f"⏳ Next Operational: {next_start.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        print("\n✅ System status check completed successfully")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Critical error getting system status: {e}")
        return 1

def run_scheduler(args):
    """Run the continuous scheduler for daily automation."""
    print("\n⏰ Starting continuous scheduler...")
    print(f"📅 Scheduled to run daily at {settings.SCHEDULE_HOUR:02d}:{settings.SCHEDULE_MINUTE:02d} Madrid time")
    print("🛑 Press Ctrl+C to stop the scheduler")
    
    # Setup signal handlers for graceful shutdown
    setup_signal_handlers()
    
    try:
        import schedule
        
        # Initialize workflow orchestrator
        workflow = WorkflowOrchestrator()
        
        def scheduled_job():
            """Job function to run the daily check."""
            print(f"\n⏰ Scheduled check triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            result = workflow.run_daily_check()
            print_result_summary(result)
            
            # Log the result
            if result['success']:
                print("✅ Scheduled check completed successfully")
            else:
                print("❌ Scheduled check completed with errors")
        
        # Schedule the daily job
        schedule.every().day.at(f"{settings.SCHEDULE_HOUR:02d}:{settings.SCHEDULE_MINUTE:02d}").do(scheduled_job)
        
        print(f"✅ Scheduler configured. Next run: {schedule.next_run()}")
        
        # Run the scheduler loop
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        print("\n🛑 Scheduler stopped by user")
        return 0
    except ImportError:
        print("\n❌ Error: 'schedule' library not installed. Run: pip install schedule")
        return 1
    except Exception as e:
        print(f"\n❌ Critical error in scheduler: {e}")
        return 1

def main():
    """Main entry point."""
    print_banner()
    
    # Setup argument parser
    parser = argparse.ArgumentParser(
        description="Conway Bikes Order Monitoring Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py check         # Run daily check manually
  python main.py frequent      # Run frequent check (5-minute window)
  python main.py test          # Test all components
  python main.py schedule      # Run continuous scheduler
  python main.py status        # Get system status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Run daily check manually')
    check_parser.set_defaults(func=run_daily_check)
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test all system components')
    test_parser.set_defaults(func=test_components)
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status and configuration')
    status_parser.set_defaults(func=show_status)
    
    # Schedule command
    schedule_parser = subparsers.add_parser('schedule', help='Run continuous scheduler for daily automation')
    schedule_parser.set_defaults(func=run_scheduler)

    # Frequent Check command
    frequent_check_parser = subparsers.add_parser('frequent', help='Run a frequent check (e.g., hourly, daily)')
    frequent_check_parser.set_defaults(func=run_frequent_check)
    
    # Parse arguments
    args = parser.parse_args()
    
    # If no command provided, show help
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute the selected command
    try:
        return args.func(args)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 