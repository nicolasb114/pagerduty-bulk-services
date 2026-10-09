# PagerDuty Bulk Service Creator

A Python script to bulk create PagerDuty services from a CSV file with automatic retry logic, rate limiting, and comprehensive failure reporting.

---

## 📋 Overview

This tool allows you to create 100-150+ PagerDuty services in bulk by reading service details from a CSV file and making individual API requests for each service. It includes:

- ✅ Automatic retry logic for failed requests
- ✅ Rate limiting to respect API limits
- ✅ Real-time progress tracking
- ✅ Comprehensive failure reporting (console + CSV file)
- ✅ Configurable alert grouping and notification settings
- ✅ **No external dependencies** - uses only built-in Python libraries

---

## 🔧 Requirements

### Software Requirements
- **Python 3.6 or higher** (that's it!)

### Installation

1. **Check if Python is installed:**
   ```bash
   python3 --version
   ```
   or
   ```bash
   python --version
   ```

**No additional libraries needed!** The script uses only built-in Python libraries (`urllib`, `csv`, `json`).

---

## 📁 File Structure

Your project directory should contain the following files:

```
project-folder/
├── bulk_create_services.py    # Main Python script
├── config.json                 # Configuration file (API key, settings)
├── services.csv                # Input CSV with services to create
└── README.md                   # This file
```

After running, if there are failures:
```
project-folder/
├── ...
└── failed_services.csv         # Generated only if services fail
```

---

## ⚙️ Setup Instructions

### Step 1: Configure `config.json`

Edit the `config.json` file with your settings:

```json
{
  "api_key": "YOUR_PAGERDUTY_API_KEY_HERE",
  "alert_grouping_type": "intelligent",
  "auto_pause_notifications_enabled": true,
  "rate_limit_requests_per_second": 5,
  "max_retry_attempts": 3
}
```

**Configuration Parameters:**

| Parameter | Type | Options | Description |
|-----------|------|---------|-------------|
| `api_key` | string | Your API key | PagerDuty API key (required) |
| `alert_grouping_type` | string | `"intelligent"` or `"time"` | Alert grouping method |
| `auto_pause_notifications_enabled` | boolean | `true` or `false` | Enable/disable auto-pause notifications |
| `rate_limit_requests_per_second` | number | 1-10 | Number of API requests per second (default: 5) |
| `max_retry_attempts` | number | 1-5 | Maximum retry attempts for failed requests (default: 3) |

**How to get your PagerDuty API Key:**
1. Log in to PagerDuty
2. Go to **Integrations** → **API Access Keys**
3. Create a new API key with appropriate permissions
4. Copy and paste it into `config.json`

---

### Step 2: Prepare `services.csv`

The CSV file contains the services you want to create.

**Format:**
- **First row:** Column headers (required)
- **Subsequent rows:** Service data

**Required Columns:**

| Column Name | Description | Example |
|-------------|-------------|---------|
| `name` | Service name | `"My Web App"` |
| `description` | Service description | `"Production web application"` |
| `escalation_policy_id` | PagerDuty escalation policy ID | `"PN81AKA"` |

**Example `services.csv`:**

```csv
name,description,escalation_policy_id
My Web App,My cool web application that does things.,PN81AKA
Database Service,Production database monitoring,PN81AKA
API Gateway,Main API gateway service,PN81AKA
Payment Processing,Payment processing service,PN81AKA
Email Service,Email notification service,PN81AKA
```

**Important Notes:**
- ✅ **First row MUST be headers** (`name`, `description`, `escalation_policy_id`)
- ✅ Data starts from the second row
- ✅ Column order doesn't matter as long as headers are correct
- ✅ You can have 100-150+ rows (services)

---

## 🚀 How to Run

1. **Navigate to the project directory:**
   ```bash
   cd /path/to/project-folder
   ```

2. **Run the script:**
   ```bash
   python3 bulk_create_services.py
   ```
   or
   ```bash
   python bulk_create_services.py
   ```

3. **Monitor the progress** in the console output

---

## 📊 Output & Results

### Console Output

During execution, you'll see real-time progress:

```
============================================================
PagerDuty Bulk Service Creator
============================================================

🚀 Starting bulk service creation...
📊 Total services to create: 150
⚙️  Alert grouping type: intelligent
⚙️  Auto-pause notifications: True
⚙️  Rate limit: 5 requests/second
⚙️  Max retry attempts: 3

============================================================

[1/150] ✅ Created: "My Web App"
[2/150] ✅ Created: "Database Service"
[3/150] ⚠️  Retrying: "API Gateway" (Attempt 2/3)
[3/150] ✅ Created: "API Gateway"
[4/150] ❌ Failed: "Payment Service" - 400 Bad Request - Invalid escalation policy ID
...
```

### Summary Report

After completion:

```
============================================================
BULK SERVICE CREATION COMPLETE
============================================================
Total Services: 150
✅ Successfully Created: 147
❌ Failed: 3
============================================================

FAILED SERVICES:
------------------------------------------------------------
1. "Payment Service"
   Error: 400 Bad Request - Invalid escalation policy ID

2. "Email Service"
   Error: 429 Rate Limit Exceeded

3. "Monitoring Service"
   Error: 500 Internal Server Error

------------------------------------------------------------

📄 Failed services saved to: failed_services.csv

✨ Done!
```

### Failed Services CSV

If any services fail after all retry attempts, a `failed_services.csv` file is automatically generated:

```csv
name,description,escalation_policy_id,error
Payment Service,Payment processing service,INVALID_ID,400 Bad Request - Invalid escalation policy ID
Email Service,Email notification service,PN81AKA,429 Rate Limit Exceeded
Monitoring Service,Server monitoring service,PN81AKA,500 Internal Server Error
```

**You can:**
- Review the errors
- Fix the issues in the CSV
- Re-run the script with only the failed services

---

## ⏱️ Performance & Limits

### Execution Time Estimates

Based on the configured rate limit:

| Services | Rate (req/sec) | Estimated Time |
|----------|----------------|----------------|
| 100 | 5 | ~20 seconds |
| 150 | 5 | ~30 seconds |
| 100 | 10 | ~10 seconds |
| 150 | 10 | ~15 seconds |

### Rate Limiting

- **Default:** 5 requests per second
- **Recommended:** 5-10 requests per second
- **PagerDuty API Limit:** Typically 960 requests per minute
- The script automatically spaces out requests to respect the configured rate limit

### Retry Logic

- **Default:** 3 attempts per service
- **Retry Delay:** 2 seconds between attempts
- **Smart Retry:** Skips retry for client errors (4xx except 429 rate limit)
- **Retries on:** Network errors, timeouts, 5xx server errors, 429 rate limits

---

## 🔍 Alert Grouping Types

The script supports two alert grouping configurations:

### 1. Intelligent Grouping (`"intelligent"`)

PagerDuty automatically groups related alerts using machine learning.

**Resulting JSON:**
```json
"alert_grouping_parameters": {
  "type": "intelligent"
}
```

### 2. Time-Based Grouping (`"time"`)

Groups alerts that occur within a specified time window (2 minutes).

**Resulting JSON:**
```json
"alert_grouping_parameters": {
  "type": "time",
  "config": {
    "timeout": 2
  }
}
```

**Note:** The timeout is fixed at 2 minutes for time-based grouping.

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. **"Config file not found"**
- **Solution:** Ensure `config.json` is in the same directory as the script

#### 2. **"CSV file not found"**
- **Solution:** Ensure `services.csv` is in the same directory as the script

#### 3. **"401 Unauthorized"**
- **Solution:** Check that your API key in `config.json` is correct and has proper permissions

#### 4. **"400 Bad Request - Invalid escalation policy ID"**
- **Solution:** Verify the escalation policy IDs in your CSV exist in PagerDuty

#### 5. **"429 Rate Limit Exceeded"**
- **Solution:** Reduce `rate_limit_requests_per_second` in `config.json` (try 3 or lower)

#### 6. **All services failing**
- **Check:** API key is valid
- **Check:** Escalation policy IDs are correct
- **Check:** Internet connection is stable
- **Try:** Reduce rate limit to 1-2 requests per second

#### 7. **SSL Certificate errors**
- **Solution:** This is rare but can happen on some systems. Ensure your Python installation has up-to-date SSL certificates

---

## 📖 Complete Example Walkthrough

### Scenario
Create 5 services with intelligent alert grouping and auto-pause enabled.

### Step 1: Edit `config.json`
```json
{
  "api_key": "u+AbCdEfGhIjKlMnOpQrStUv",
  "alert_grouping_type": "intelligent",
  "auto_pause_notifications_enabled": true,
  "rate_limit_requests_per_second": 5,
  "max_retry_attempts": 3
}
```

### Step 2: Create `services.csv`
```csv
name,description,escalation_policy_id
Web Application,Production web app,P123ABC
Database,PostgreSQL database,P123ABC
Cache Service,Redis cache,P123ABC
API Gateway,Kong API gateway,P123ABC
Message Queue,RabbitMQ service,P123ABC
```

### Step 3: Run the script
```bash
python3 bulk_create_services.py
```

### Step 4: Review output
```
============================================================
PagerDuty Bulk Service Creator
============================================================

🚀 Starting bulk service creation...
📊 Total services to create: 5
⚙️  Alert grouping type: intelligent
⚙️  Auto-pause notifications: True
⚙️  Rate limit: 5 requests/second
⚙️  Max retry attempts: 3

============================================================

[1/5] ✅ Created: "Web Application"
[2/5] ✅ Created: "Database"
[3/5] ✅ Created: "Cache Service"
[4/5] ✅ Created: "API Gateway"
[5/5] ✅ Created: "Message Queue"

============================================================
BULK SERVICE CREATION COMPLETE
============================================================
Total Services: 5
✅ Successfully Created: 5
❌ Failed: 0
============================================================

✨ Done!
```

---

## 📝 Static Service Configuration

All created services will have the following static settings:

| Field | Value |
|-------|-------|
| `type` | `"service"` |
| `status` | `"active"` |
| `auto_resolve_timeout` | `null` |
| `acknowledgement_timeout` | `null` |
| `incident_urgency_rule.type` | `"constant"` |
| `incident_urgency_rule.urgency` | `"high"` |
| `alert_creation` | `"create_alerts_and_incidents"` |
| `auto_pause_notifications_parameters.timeout` | `300` (5 minutes) |
| `escalation_policy.type` | `"escalation_policy_reference"` |

---

## 📞 Support

For issues or questions:
1. Review the **Troubleshooting** section
2. Check PagerDuty API documentation: https://developer.pagerduty.com/
3. Verify your API key permissions
4. Review the `failed_services.csv` for specific error messages

---

## 📄 License

This tool is provided as-is for bulk service creation in PagerDuty.

---

**Happy bulk creating! 🚀**


---
**Setup:** edit `config.json` and replace the placeholder values with your own. Keep your real API key out of commits. Run with `dry_run` enabled first.
