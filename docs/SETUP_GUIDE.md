# Chicago Clinic Demand Intelligence - Setup Guide

## Complete Installation and Configuration Guide

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Database Setup](#database-setup)
5. [API Keys](#api-keys)
6. [Running the System](#running-the-system)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Database**: PostgreSQL 12+ or SQLite 3
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 10GB free space
- **OS**: Windows, macOS, or Linux

### Required Accounts
1. **Google Cloud Platform**
   - Google Places API access
   - Billing enabled (free tier available)

2. **Yelp Fusion API**
   - Free API key from Yelp Developers

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/sourabhgithubcode.git
cd sourabhgithubcode
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configuration

### Step 1: Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```ini
# API Keys
GOOGLE_PLACES_API_KEY=your_google_places_api_key_here
YELP_API_KEY=your_yelp_api_key_here

# Database Configuration
DB_TYPE=postgresql  # or sqlite
DB_HOST=localhost
DB_PORT=5432
DB_NAME=clinic_intelligence
DB_USER=your_username
DB_PASSWORD=your_password

# For SQLite (simpler option for testing)
SQLITE_DB_PATH=data/clinic_intelligence.db

# Scheduling
DAILY_REFRESH_TIME=02:00
```

### Step 2: Validate Configuration

```bash
python config/settings.py
```

You should see:
```
✓ Configuration is valid
Database URL: postgresql://localhost:5432/clinic_intelligence
Target City: Chicago, IL
Clinic Types: urgent_care, primary_care, ...
```

---

## Database Setup

### Option 1: PostgreSQL (Recommended for Production)

#### Install PostgreSQL

**On Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**On macOS (using Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**On Windows:**
Download installer from [postgresql.org](https://www.postgresql.org/download/windows/)

#### Create Database

```bash
# Login to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE clinic_intelligence;
CREATE USER clinic_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE clinic_intelligence TO clinic_user;
\q
```

#### Initialize Tables

```bash
python src/database/init_db.py create
```

### Option 2: SQLite (Recommended for Development)

SQLite requires no installation. Simply set in `.env`:

```ini
DB_TYPE=sqlite
SQLITE_DB_PATH=data/clinic_intelligence.db
```

Initialize database:

```bash
python src/database/init_db.py create
```

---

## API Keys

### Google Places API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Places API**
4. Go to **Credentials** → **Create Credentials** → **API Key**
5. Copy the API key
6. (Optional) Restrict key to Places API only
7. Add to `.env` file

**Cost**: Free tier includes $200/month credit (~40,000 place searches)

### Yelp Fusion API

1. Go to [Yelp Fusion](https://www.yelp.com/developers)
2. Create an account
3. Create a new app
4. Copy the API key
5. Add to `.env` file

**Cost**: Free (5,000 requests/day)

---

## Running the System

### Initial Data Collection

#### Step 1: Collect Google Places Data

```bash
python src/collectors/google_places_collector.py
```

Expected output:
```
INFO: Starting Google Places collection for 56 ZIP codes
INFO: Found 18 places in 60601
...
✓ Collection complete: 1,234 new, 0 updated, 5 failed
```

**Estimated time**: 2-4 hours (due to rate limits)

#### Step 2: Collect Yelp Data

```bash
python src/collectors/yelp_collector.py
```

**Estimated time**: 1-2 hours

#### Step 3: Collect Google Trends Data

```bash
python src/collectors/trends_collector.py
```

**Estimated time**: 30-60 minutes

#### Step 4: Run Analysis

```bash
python src/analysis/scoring_engine.py
```

**Estimated time**: 5-10 minutes

### Automated Daily Refresh

#### Run Once

```bash
python src/utils/scheduler.py --mode once
```

#### Schedule Daily Refresh

```bash
python src/utils/scheduler.py --mode scheduled
```

This will:
1. Collect new data daily at configured time
2. Update existing records
3. Recalculate all scores and metrics
4. Log results

### Run Individual Components

```bash
# Just Google Places
python src/utils/scheduler.py --component google

# Just Yelp
python src/utils/scheduler.py --component yelp

# Just Trends
python src/utils/scheduler.py --component trends

# Just Analysis
python src/utils/scheduler.py --component analysis
```

---

## Verify Installation

### Check Database Tables

```bash
# For PostgreSQL
psql -U clinic_user -d clinic_intelligence -c "\dt"

# For SQLite
sqlite3 data/clinic_intelligence.db ".tables"
```

You should see:
- clinics
- reviews
- search_trends
- visibility_scores
- demand_metrics
- competitor_analysis
- data_collection_logs

### Check Data

```bash
# For PostgreSQL
psql -U clinic_user -d clinic_intelligence -c "SELECT COUNT(*) FROM clinics;"

# For SQLite
sqlite3 data/clinic_intelligence.db "SELECT COUNT(*) FROM clinics;"
```

### View Sample Results

```bash
# For PostgreSQL
psql -U clinic_user -d clinic_intelligence

# Run sample queries
SELECT name, zip_code, google_rating, yelp_rating FROM clinics LIMIT 10;

SELECT service_category, AVG(search_demand_index)
FROM demand_metrics
GROUP BY service_category;
```

---

## Troubleshooting

### API Key Errors

**Error**: `GOOGLE_PLACES_API_KEY is not set`

**Solution**:
1. Check `.env` file exists
2. Verify API key is correctly set
3. Ensure no spaces around `=`
4. Restart Python session

### Database Connection Errors

**Error**: `could not connect to server`

**Solution**:
1. Verify PostgreSQL is running: `systemctl status postgresql`
2. Check connection details in `.env`
3. Test connection: `psql -U clinic_user -d clinic_intelligence`
4. Check firewall settings

### Rate Limiting

**Error**: `API rate limit exceeded`

**Solution**:
1. Increase `API_RATE_LIMIT_DELAY` in `.env`
2. Run collection in smaller batches
3. Wait and retry later
4. Check your API quota

### Memory Issues

**Error**: `MemoryError` during data collection

**Solution**:
1. Process fewer ZIP codes at a time
2. Increase system RAM
3. Use PostgreSQL instead of SQLite
4. Clear old data

### Import Errors

**Error**: `ModuleNotFoundError`

**Solution**:
```bash
# Verify virtual environment is activated
which python

# Reinstall dependencies
pip install -r requirements.txt

# Check Python version
python --version  # Should be 3.8+
```

---

## Performance Optimization

### For Large Datasets

1. **Use PostgreSQL**: Better performance for large data
2. **Add Indexes**: Already included in models
3. **Batch Processing**: Process ZIP codes in batches
4. **Caching**: Results are cached in database

### For Faster Collection

1. **Increase concurrent requests** (respecting rate limits)
2. **Filter by specific clinic types**
3. **Focus on high-priority ZIP codes**
4. **Use incremental updates**

---

## Logs and Monitoring

### Log Files

Logs are stored in `logs/clinic_intelligence.log`

```bash
# View recent logs
tail -f logs/clinic_intelligence.log

# Search for errors
grep ERROR logs/clinic_intelligence.log
```

### Collection Status

Check `data_collection_logs` table:

```sql
SELECT * FROM data_collection_logs
ORDER BY start_time DESC
LIMIT 10;
```

---

## Next Steps

1. ✅ Complete installation
2. ✅ Collect initial data
3. ✅ Run analysis
4. 📊 Set up Power BI dashboard (see `dashboards/POWERBI_SETUP.md`)
5. 🔄 Configure scheduled refresh
6. 📈 Start generating insights!

---

## Support

For issues or questions:
- Check the [main documentation](../README.md)
- Review [Power BI setup guide](../dashboards/POWERBI_SETUP.md)
- Check database schema: `src/database/models.py`
- Review SQL queries: `sql/kpi_queries.sql`

---

## Maintenance

### Regular Tasks

**Daily**:
- Monitor collection logs
- Check for API errors

**Weekly**:
- Review data quality
- Validate metrics
- Check storage usage

**Monthly**:
- Archive old data (>1 year)
- Review API usage and costs
- Update service keywords if needed

### Backup

```bash
# Backup PostgreSQL
pg_dump clinic_intelligence > backup_$(date +%Y%m%d).sql

# Backup SQLite
cp data/clinic_intelligence.db data/backup_$(date +%Y%m%d).db
```

---

## Security Best Practices

1. **Never commit `.env` file** (already in `.gitignore`)
2. **Rotate API keys regularly**
3. **Use strong database passwords**
4. **Restrict database access**
5. **Keep dependencies updated**
6. **Monitor API usage**

---

**You're all set! 🎉**

The system is now ready to provide actionable marketing intelligence for Chicago clinics.
