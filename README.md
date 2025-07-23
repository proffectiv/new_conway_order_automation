# 🚴 Conway Bikes Order Monitoring Automation

A Python automation system that monitors Holded API for sales orders containing Conway bike references and sends email notifications.

## 📋 Features

- **Daily Automated Monitoring**: Checks Holded API every day at 9 AM Madrid time
- **Automated Monitoring**: Runs every 5 minutes via GitHub Actions with duplicate prevention
- **Conway Bike Detection**: Filters orders containing references from secure Dropbox storage
- **Email Notifications**: Sends professional HTML/plain text emails with order details
- **Time-Based Operation**: Only runs during configured hours (7:00-23:00)
- **Smart Duplicate Prevention**: Avoids sending duplicate notifications
- **Robust Error Handling**: Comprehensive logging and error management
- **Timezone Aware**: Handles Madrid timezone correctly
- **Test Mode Support**: Safe testing without sending actual emails
- **Secure File Handling**: CSV data retrieved securely from Dropbox with automatic cleanup
- **Privacy Protection**: Sensitive data filtered from logs and output
- **Modular Design**: Clean, maintainable code following best practices

## 🏗️ Project Structure

```
new_conway_order_automation/
├── src/
│   ├── config/
│   │   ├── settings.py          # Configuration management
│   │   └── logging_filters.py   # Sensitive data filtering
│   ├── utils/
│   │   ├── csv_processor.py     # CSV file processing
│   │   └── dropbox_handler.py   # Secure Dropbox file retrieval
│   ├── holded/
│   │   └── api_client.py        # Holded API client
│   ├── notifications/
│   │   └── email_sender.py      # Email notifications
│   └── main_workflow.py         # Main orchestrator
├── logs/                        # Log files directory
├── main.py                      # CLI entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
└── .env                         # Your actual environment variables (create this)
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Environment Variables

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your actual credentials:

```bash
# Holded API Configuration
HOLDED_API_KEY=your_holded_api_key_here
HOLDED_BASE_URL=https://api.holded.com/api

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@example.com
EMAIL_PASSWORD=your_app_password_here
EMAIL_FROM=your_email@example.com

# Notification Configuration
TARGET_EMAIL=recipient@example.com
EMAIL_SUBJECT_PREFIX=[Bike Order Alert]

# Timezone Configuration
TIMEZONE=Europe/Madrid

# Dropbox Configuration (for secure file retrieval)
DROPBOX_APP_KEY=your_dropbox_app_key_here
DROPBOX_APP_SECRET=your_dropbox_app_secret_here
DROPBOX_REFRESH_TOKEN=your_dropbox_refresh_token_here
DROPBOX_FILE_PATH=/path/to/your/data/file.csv
LOG_LEVEL=INFO
LOG_FILE=logs/holded_automation.log

# Schedule Configuration
SCHEDULE_HOUR=12
SCHEDULE_MINUTE=30

# Development/Testing Configuration
TEST_MODE=false
TEST_EMAIL_ONLY=false
```

### 3. Test the System

```bash
# Test all components
python main.py test

# Check system status
python main.py status

# Run a manual check
python main.py check
```

### 4. Run Daily Automation

```bash
# Run continuous scheduler (keeps running)
python main.py schedule
```

## 🤖 GitHub Actions Automation (Recommended)

For the most responsive order monitoring, use GitHub Actions to run checks every 15 minutes:

### Setup GitHub Actions

1. **Configure Secrets**: Go to your repository Settings → Secrets and variables → Actions
2. **Add Required Secrets**: See [GitHub Actions Setup Guide](.github/GITHUB_ACTIONS_SETUP.md) for complete list
3. **Enable Workflow**: The workflow in `.github/workflows/frequent-check.yml` will run automatically

### Key Benefits

- **🚀 Immediate Notifications**: Orders detected within 15 minutes of creation
- **⏰ Smart Scheduling**: Only runs during business hours (7:00-23:00)
- **🔄 No Duplicates**: Checks last 24 hours but prevents duplicate notifications using processed orders tracking
- **🛡️ Robust**: Continues running even if individual checks fail
- **📊 Monitoring**: Detailed logs and failure artifacts in GitHub Actions

### Quick Test

```bash
# Test the system locally
python main.py check

# Test all components
python main.py test
```

For detailed setup instructions, see the [GitHub Actions Setup Guide](.github/GITHUB_ACTIONS_SETUP.md).

## 📚 Usage

### Command Line Interface

The system provides a comprehensive CLI for all operations:

```bash
# Show help
python main.py --help

# Run check manually (last 24 hours with duplicate prevention)
python main.py check

# Test all system components
python main.py test

# Show system status and configuration
python main.py status

# Run continuous scheduler for automation
python main.py schedule
```

### Manual Testing

Before setting up automation, test each component:

```bash
# 1. Test CSV processing
python main.py status  # Shows CSV statistics

# 2. Test Holded API connection
python main.py test    # Tests API connectivity

# 3. Test email sending
python main.py test    # Tests email functionality

# 4. Run complete workflow manually
python main.py check   # Runs full check process
```

## ⚙️ Configuration

### Environment Variables

| Variable               | Description                     | Example                      |
| ---------------------- | ------------------------------- | ---------------------------- |
| `HOLDED_API_KEY`       | Your Holded API key             | `your_api_key_here`          |
| `HOLDED_BASE_URL`      | Holded API base URL             | `https://api.holded.com/api` |
| `DROPBOX_APP_KEY`      | Dropbox application key         | `your_dropbox_app_key`       |
| `DROPBOX_APP_SECRET`   | Dropbox application secret      | `your_dropbox_app_secret`    |
| `DROPBOX_REFRESH_TOKEN`| Dropbox refresh token           | `your_dropbox_refresh_token` |
| `DROPBOX_FILE_PATH`    | Path to CSV file in Dropbox     | `/folder/data.csv`           |
| `EMAIL_USERNAME`       | SMTP username                   | `your_email@gmail.com`       |
| `EMAIL_PASSWORD`       | SMTP password/app password      | `your_app_password`          |
| `TARGET_EMAIL`         | Recipient email address         | `alerts@yourcompany.com`     |
| `TIMEZONE`             | Madrid timezone                 | `Europe/Madrid`              |
| `SCHEDULE_HOUR`        | Daily run hour (24h format)     | `12`                          |
| `SCHEDULE_MINUTE`      | Daily run minute                | `30`                          |
| `OPERATION_START_HOUR` | Start hour for automation       | `7`                          |
| `OPERATION_END_HOUR`   | End hour for automation         | `23`                         |
| `TEST_MODE`            | Enable test mode                | `false`                      |
| `TEST_EMAIL_ONLY`      | Test emails without sending     | `false`                      |

### Dropbox Setup

The system securely retrieves the CSV data file from Dropbox:

1. **Create Dropbox App**: Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. **Get Credentials**: Note your App Key and App Secret
3. **Generate Refresh Token**: Use OAuth2 flow to get a refresh token
4. **Upload CSV File**: Place your data file in Dropbox
5. **Configure Path**: Set `DROPBOX_FILE_PATH` to your file location

### CSV File Format

Your CSV data file should have:

- An `Artikelnummer` column containing bike SKU/reference codes
- Headers in the first row
- UTF-8 encoding
- Comma or semicolon delimited
- SKUs with leading zeros (e.g., "[REFERENCE_EXAMPLE]") are supported

Example:

```csv
Artikelnummer,Artikeltext,Marke,Modelljahr,Modell
[REFERENCE_1],[PRODUCT_NAME_1],[BRAND],[YEAR],[MODEL]
[REFERENCE_2],[PRODUCT_NAME_2],[BRAND],[YEAR],[MODEL]
```

### Email Configuration

For Gmail users:

1. Enable 2-factor authentication
2. Generate an App Password
3. Use the App Password as `EMAIL_PASSWORD`

For other email providers:

- Use appropriate SMTP settings
- Ensure TLS/SSL is supported

## 🔄 Automation Setup

### Running as a Service (Production)

For production deployment, you can run the scheduler as a system service:

#### Using systemd (Linux)

Create `/etc/systemd/system/conway-bikes-monitor.service`:

```ini
[Unit]
Description=Bike Order Monitor
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/new_conway_order_automation
Environment=PATH=/path/to/new_conway_order_automation/.venv/bin
ExecStart=/path/to/new_conway_order_automation/.venv/bin/python main.py schedule
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable conway-bikes-monitor.service
sudo systemctl start conway-bikes-monitor.service
sudo systemctl status conway-bikes-monitor.service
```

#### Using cron (Alternative)

Add to crontab for daily execution:

```bash
# Run daily at 9:00 AM
0 9 * * * cd /path/to/new_conway_order_automation && /path/to/new_conway_order_automation/.venv/bin/python main.py check
```

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py", "schedule"]
```

Build and run:

```bash
docker build -t conway-bikes-monitor .
docker run -d --name conway-monitor \
  --env-file .env \
  --restart unless-stopped \
  conway-bikes-monitor
```

## 📊 Monitoring and Logging

### Log Files

Logs are stored in `logs/holded_automation.log` with rotation.

Log levels:

- `INFO`: Normal operations
- `WARNING`: Non-critical issues
- `ERROR`: Errors requiring attention
- `DEBUG`: Detailed debugging (set `LOG_LEVEL=DEBUG`)

### Monitoring Commands

```bash
# View recent logs
tail -f logs/holded_automation.log

# Check system status
python main.py status

# Test all components
python main.py test
```

## 🛡️ Security Best Practices

1. **Environment Variables**: Never commit `.env` to version control
2. **Dropbox Security**: Use app-specific credentials with limited scope
3. **API Keys**: Use restricted API keys with minimal permissions
4. **Email Passwords**: Use app passwords, not main account passwords
5. **File Permissions**: Restrict access to configuration files
6. **Data Privacy**: Sensitive information is automatically filtered from logs
7. **Temporary Files**: Downloaded files are automatically cleaned up
8. **Network Security**: Run in secure network environment

## 🐛 Troubleshooting

### Common Issues

**Issue**: "Required environment variable not found"

- **Solution**: Ensure all required variables are set in `.env`

**Issue**: "Failed to download file from Dropbox"

- **Solutions**:
  - Verify Dropbox credentials in `.env`
  - Check file path exists in Dropbox
  - Ensure network connectivity

**Issue**: "Holded API connection failed"

- **Solutions**:
  - Check API key validity
  - Verify API endpoint URL
  - Check network connectivity

**Issue**: "Email sending failed"

- **Solutions**:
  - Verify SMTP settings
  - Check email credentials
  - Enable app passwords for Gmail

**Issue**: "No bike references loaded"

- **Solutions**:
  - Verify Dropbox file access and permissions
  - Check CSV file format in Dropbox
  - Ensure `Artikelnummer` column exists
  - Verify file encoding is UTF-8
  - Test Dropbox connection with `python main.py test`

### Debug Mode

Enable detailed logging:

```bash
# Set in .env
LOG_LEVEL=DEBUG

# Or temporarily
export LOG_LEVEL=DEBUG
python main.py check
```

### Test Mode

For safe testing without real emails:

```bash
# Set in .env
TEST_MODE=true
TEST_EMAIL_ONLY=true

python main.py test
python main.py check
```

## 🔒 Privacy and Security Features

The system includes comprehensive privacy protection:

- **Sensitive Data Filtering**: File paths, reference counts, and file names are automatically redacted from logs
- **Secure File Handling**: CSV files are downloaded to temporary locations and automatically cleaned up
- **Credential Protection**: All API keys, tokens, and credentials are filtered from log output
- **Email Redaction**: Email addresses are masked in logs as `[EMAIL_REDACTED]`
- **Dropbox Integration**: Files are retrieved securely without persistent local storage

## 📈 Performance Notes

- **CSV Processing**: Optimized for files up to 10,000 references
- **Dropbox Downloads**: Efficient file retrieval with automatic cleanup
- **API Calls**: Respects rate limits with proper error handling
- **Memory Usage**: Minimal memory footprint (~50MB typical)
- **Execution Time**: Complete check typically takes 15-45 seconds (including Dropbox download)

## 🔄 Workflow Details

The automation follows this process:

1. **Secure Data Retrieval** from Dropbox with automatic cleanup
2. **Load Bike References** from downloaded CSV file
3. **Query Holded API** for sales orders since yesterday 9 AM
4. **Filter Orders** containing any bike references
5. **Generate Email** with standardized format
6. **Send Notification** to configured recipient
7. **Log Results** with sensitive data filtering for security

## 👥 Support

For issues and questions:

1. Check logs in `logs/holded_automation.log`
2. Run `python main.py test` to diagnose issues
3. Verify environment configuration
4. Check CSV file format and content

## 📄 License

This project is proprietary software for bike order monitoring automation.

---

**🚴 Happy Monitoring!** The system will keep you informed of all bike orders automatically.
