# GitHub Actions Setup for Conway Bikes Automation

This guide explains how to set up GitHub Actions to run Conway bike order monitoring every 5 minutes automatically.

## 🔑 Required GitHub Secrets

You need to configure the following secrets in your GitHub repository settings:

### To set up secrets:

1. Go to your repository on GitHub
2. Click on **Settings** tab
3. Click on **Secrets and variables** → **Actions**
4. Click **New repository secret** for each secret below

### Required Secrets:

#### Holded API Configuration

- **`HOLDED_API_KEY`**: Your Holded API key
- **`HOLDED_BASE_URL`**: Holded API base URL (default: `https://api.holded.com/api`)

#### Email Configuration

- **`SMTP_SERVER`**: SMTP server (e.g., `smtp.gmail.com`)
- **`SMTP_PORT`**: SMTP port (e.g., `587`)
- **`EMAIL_USERNAME`**: Your email username
- **`EMAIL_PASSWORD`**: Your email password (use App Password for Gmail)
- **`EMAIL_FROM`**: From email address (usually same as username)

#### Notification Configuration

- **`TARGET_EMAIL`**: Email address to receive notifications
- **`EMAIL_SUBJECT_PREFIX`**: Email subject prefix (e.g., `[Conway Bikes Alert]`)

#### Timezone Configuration

- **`TIMEZONE`**: Timezone for operations (default: `Europe/Madrid`)

#### Operation Hours Configuration

- **`OPERATION_START_HOUR`**: Start hour for automation (default: `7`)
- **`OPERATION_END_HOUR`**: End hour for automation (default: `23`)

## 🚀 Workflow Overview

The GitHub Actions workflow (`frequent-check.yml`) will:

1. **Run every 5 minutes** using cron schedule `*/5 * * * *`
2. **Check operation hours** - only runs between configured hours (7:00-23:00 by default)
3. **Fetch orders** from Holded API (last 24 hours)
4. **Filter for unprocessed orders** using duplicate prevention tracking
5. **Filter for bike references** using the CSV file
6. **Send email notifications** if Conway bike orders are found
7. **Skip gracefully** if no orders, no new orders, or outside operation hours

## ⚙️ Workflow Features

### Time-Based Execution

- Runs every 5 minutes during configured operation hours
- Automatically skips execution outside operation hours (7:00-23:00)
- Uses Madrid timezone for consistent operation

### Smart Filtering

- Only fetches orders from the last N minutes (configurable)
- Avoids duplicate notifications by using time windows
- Early exit if no orders or no bike references found

### Robust Error Handling

- Continues running even if individual checks fail
- Uploads logs as artifacts on failures for debugging
- Maintains operation logs for monitoring

### Manual Triggering

- Can be triggered manually via GitHub Actions UI
- Useful for testing and debugging

## 📊 Monitoring and Logs

### GitHub Actions Logs

- Each run creates detailed logs visible in GitHub Actions tab
- Logs show operation hours check, orders retrieved, and email status
- Failed runs upload log files as artifacts

### Log Artifacts

- **On Failure**: Logs are saved for 7 days for debugging
- **Weekly**: Logs can be archived for longer-term monitoring

## 🔧 Configuration Examples

### Basic Setup (Minimal Required Secrets)

```
HOLDED_API_KEY=your_api_key_here
EMAIL_USERNAME=your_email@example.com
EMAIL_PASSWORD=your_app_password
TARGET_EMAIL=orders@yourcompany.com
```

### Advanced Setup (Full Configuration)

```
HOLDED_API_KEY=your_api_key_here
HOLDED_BASE_URL=https://api.holded.com/api
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=notifications@yourcompany.com
EMAIL_PASSWORD=your_app_password
EMAIL_FROM=notifications@yourcompany.com
TARGET_EMAIL=orders@yourcompany.com
EMAIL_SUBJECT_PREFIX=[Conway Bikes - Urgent]
TIMEZONE=Europe/Madrid
CHECK_DELAY_MINUTES=5
OPERATION_START_HOUR=7
OPERATION_END_HOUR=23
```

## 🛠️ Troubleshooting

### Common Issues

1. **Authentication Errors**

   - Verify `HOLDED_API_KEY` is correct
   - Check `EMAIL_USERNAME` and `EMAIL_PASSWORD`
   - For Gmail, ensure you're using an App Password

2. **No Notifications**

   - Check if current time is within operation hours
   - Verify CSV file contains bike references
   - Review logs for filtering results

3. **Workflow Not Running**
   - Check if GitHub Actions are enabled for your repository
   - Verify cron syntax in workflow file
   - Ensure the workflow file is in the correct path

### Debug Commands

Run these locally to test your configuration:

```bash
# Test the system
python main.py test

# Run a manual check
python main.py check

# Check system status
python main.py status
```

## 📈 Expected Behavior

### During Operation Hours (7:00-23:00)

- Runs every 5 minutes
- Checks last 24 hours of orders with duplicate prevention
- Sends emails only for Conway bike orders that haven't been processed
- Logs all activity

### Outside Operation Hours (23:00-7:00)

- Runs every 5 minutes but immediately skips
- Logs "Outside operation hours" message
- No API calls or email sending

### When No Orders Found

- Skips email sending gracefully
- Logs "No orders found", "No new orders", or "No bike orders"
- Considered successful execution

## 🔄 System Benefits

This simplified system provides several advantages:

1. **Comprehensive Coverage**: Always checks the full 24-hour window, ensuring no orders are missed
2. **Duplicate Prevention**: Uses processed orders tracking to prevent duplicate notifications
3. **Simplified Maintenance**: Single check method reduces complexity
4. **Robust Error Recovery**: If a check fails, the next run still covers the full time window

The workflow is designed to be responsive and efficient while being robust enough for production use.

---

**💡 Pro Tip**: Start with a longer delay (e.g., 10-15 minutes) and adjust based on your order volume and requirements.
