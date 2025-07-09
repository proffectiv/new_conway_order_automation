# 🚴 Conway Bikes Order Monitoring Automation

A Python automation system that monitors Holded API for sales orders containing Conway bike references and sends email notifications.

## 📋 Features

- **Daily Automated Monitoring**: Checks Holded API every day at 9 AM Madrid time
- **Frequent Automated Monitoring**: Runs every 5 minutes via GitHub Actions (NEW!)
- **Conway Bike Detection**: Filters orders containing references from your CSV file
- **Email Notifications**: Sends professional HTML/plain text emails with order details
- **Time-Based Operation**: Only runs during configured hours (7:00-23:00)
- **Smart Duplicate Prevention**: Avoids sending duplicate notifications
- **Robust Error Handling**: Comprehensive logging and error management
- **Timezone Aware**: Handles Madrid timezone correctly
- **Test Mode Support**: Safe testing without sending actual emails
- **Modular Design**: Clean, maintainable code following best practices

## 🏗️ Project Structure

```
proffectiv/
├── src/
│   ├── config/
│   │   └── settings.py          # Configuration management
│   ├── utils/
│   │   └── csv_processor.py     # CSV file processing
│   ├── holded/
│   │   └── api_client.py        # Holded API client
│   ├── email/
│   │   └── email_sender.py      # Email notifications
│   └── main_workflow.py         # Main orchestrator
├── logs/                        # Log files directory
├── main.py                      # CLI entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── .env                         # Your actual environment variables (create this)
└── Bike_References_Conway_2025.csv  # Conway bike references
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
EMAIL_SUBJECT_PREFIX=[Conway Bikes Alert]

# Timezone Configuration
TIMEZONE=Europe/Madrid

# Application Configuration
CSV_FILE_PATH=Bike_References_Conway_2025.csv
LOG_LEVEL=INFO
LOG_FILE=logs/holded_automation.log

# Schedule Configuration
SCHEDULE_HOUR=9
SCHEDULE_MINUTE=0

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

For the most responsive order monitoring, use GitHub Actions to run checks every 5 minutes:

### Setup GitHub Actions

1. **Configure Secrets**: Go to your repository Settings → Secrets and variables → Actions
2. **Add Required Secrets**: See [GitHub Actions Setup Guide](.github/GITHUB_ACTIONS_SETUP.md) for complete list
3. **Enable Workflow**: The workflow in `.github/workflows/frequent-check.yml` will run automatically

### Key Benefits

- **🚀 Immediate Notifications**: Orders detected within 5 minutes of creation
- **⏰ Smart Scheduling**: Only runs during business hours (7:00-23:00)
- **🔄 No Duplicates**: Uses time windows to prevent duplicate notifications
- **🛡️ Robust**: Continues running even if individual checks fail
- **📊 Monitoring**: Detailed logs and failure artifacts in GitHub Actions

### Quick Test

```bash
# Test the frequent check locally
python main.py frequent

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

# Run daily check manually
python main.py check

# Run frequent check (5-minute window)
python main.py frequent

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
| `EMAIL_USERNAME`       | SMTP username                   | `your_email@gmail.com`       |
| `EMAIL_PASSWORD`       | SMTP password/app password      | `your_app_password`          |
| `TARGET_EMAIL`         | Recipient email address         | `alerts@yourcompany.com`     |
| `TIMEZONE`             | Madrid timezone                 | `Europe/Madrid`              |
| `SCHEDULE_HOUR`        | Daily run hour (24h format)     | `9`                          |
| `SCHEDULE_MINUTE`      | Daily run minute                | `0`                          |
| `CHECK_DELAY_MINUTES`  | Frequent check window (minutes) | `5`                          |
| `OPERATION_START_HOUR` | Automation start hour           | `7`                          |
| `OPERATION_END_HOUR`   | Automation end hour             | `23`                         |
| `TEST_MODE`            | Enable test mode                | `false`                      |
| `TEST_EMAIL_ONLY`      | Test emails without sending     | `false`                      |

### CSV File Format

Your `Bike_References_Conway_2025.csv` file should have:

- A `Referencia` column containing bike reference codes
- Headers in the first row
- UTF-8 encoding
- Comma or semicolon delimited

Example:

```csv
Referencia,Modelo,Cuadro,Rueda,Talla,Color,Año
CBK001,Conway Model A,Aluminum,27.5,M,Black,2025
CBK002,Conway Model B,Carbon,29,L,Blue,2025
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
Description=Conway Bikes Order Monitor
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/proffectiv
Environment=PATH=/path/to/proffectiv/.venv/bin
ExecStart=/path/to/proffectiv/.venv/bin/python main.py schedule
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
0 9 * * * cd /path/to/proffectiv && /path/to/proffectiv/.venv/bin/python main.py check
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
2. **API Keys**: Use restricted API keys with minimal permissions
3. **Email Passwords**: Use app passwords, not main account passwords
4. **File Permissions**: Restrict access to configuration files
5. **Network Security**: Run in secure network environment

## 🐛 Troubleshooting

### Common Issues

**Issue**: "Required environment variable not found"

- **Solution**: Ensure all required variables are set in `.env`

**Issue**: "CSV file not found"

- **Solution**: Verify CSV file path and existence

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
  - Verify CSV file format
  - Check `Referencia` column exists
  - Ensure file encoding is UTF-8

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

## 📈 Performance Notes

- **CSV Processing**: Optimized for files up to 10,000 references
- **API Calls**: Respects rate limits with proper error handling
- **Memory Usage**: Minimal memory footprint (~50MB typical)
- **Execution Time**: Complete check typically takes 10-30 seconds

## 🔄 Workflow Details

The automation follows this process:

1. **Load Bike References** from CSV file
2. **Query Holded API** for sales orders since yesterday 9 AM
3. **Filter Orders** containing any bike references
4. **Generate Email** with standardized format
5. **Send Notification** to configured recipient
6. **Log Results** for monitoring and debugging

## 👥 Support

For issues and questions:

1. Check logs in `logs/holded_automation.log`
2. Run `python main.py test` to diagnose issues
3. Verify environment configuration
4. Check CSV file format and content

## 📄 License

This project is proprietary software for Conway Bikes order monitoring.

---

**🚴 Happy Monitoring!** The system will keep you informed of all Conway bike orders automatically.
