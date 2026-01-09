# Quick Start Guide

Get the OPT/CPT Friendly Listings platform running in 5 minutes!

## Prerequisites

- Python 3.10+ installed
- Node.js 18+ installed
- API key (Anthropic Claude or OpenAI GPT)

## Step 1: Clone and Setup Environment

```bash
# Already in the repo directory
cd /home/user/sourabhgithubcode

# Copy environment file
cp .env.example .env

# Edit .env and add your API key
# For Claude:
# ANTHROPIC_API_KEY=your_key_here
# For OpenAI:
# OPENAI_API_KEY=your_key_here
```

## Step 2: Start Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start server (database auto-created on first run)
python main.py
```

Backend will run at: http://localhost:8000

## Step 3: Start Frontend (New Terminal)

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will run at: http://localhost:3000

## Step 4: Load Sample Data

### Option A: Using cURL

```bash
# Trigger scraping (5 pages from Idealist)
curl -X POST http://localhost:8000/admin/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "sources": ["idealist"],
    "max_pages": 3,
    "search_terms": "volunteer",
    "location": "United States"
  }'

# Wait a few minutes, then trigger assessment
curl -X POST http://localhost:8000/admin/assess \
  -H "Content-Type: application/json" \
  -d '{"assess_all_unassessed": true}'
```

### Option B: Using Python

```python
import requests

# Scrape
response = requests.post('http://localhost:8000/admin/scrape', json={
    'sources': ['idealist'],
    'max_pages': 3,
    'search_terms': 'volunteer',
    'location': 'United States'
})
print(response.json())

# Assess (run after scraping completes)
response = requests.post('http://localhost:8000/admin/assess', json={
    'assess_all_unassessed': True
})
print(response.json())
```

## Step 5: Browse Listings

Open your browser to http://localhost:3000

You should see:
- Search and filter interface
- List of scraped listings
- Visa friendliness assessments with confidence scores
- Detailed views with reasoning and evidence

## API Endpoints

### Check Health
```bash
curl http://localhost:8000/health
```

### Get Listings
```bash
# All listings
curl http://localhost:8000/listings

# Filter by visa category
curl "http://localhost:8000/listings?visa_category=High"

# Filter by work mode
curl "http://localhost:8000/listings?work_mode=Remote"

# Search by keyword
curl "http://localhost:8000/listings?keyword=software"
```

### Get Listing Detail
```bash
curl http://localhost:8000/listings/1
```

## Troubleshooting

### Port Already in Use

Backend (8000):
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn main:app --port 8001
```

Frontend (3000):
```bash
# Kill existing process
lsof -ti:3000 | xargs kill -9

# Or edit vite.config.js to use different port
```

### Database Issues

```bash
# Delete and recreate
rm database/listings.db
python main.py  # Will recreate on startup
```

### Import Errors

```bash
# Make sure you're in virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### API Key Not Working

1. Check `.env` file exists in root directory
2. Verify key is correct format (no quotes, no spaces)
3. Restart backend after changing `.env`
4. Check logs for specific error messages

### No Listings Showing

1. Check scraping completed: `curl http://localhost:8000/health`
2. Check database has listings:
   ```python
   import sqlite3
   conn = sqlite3.connect('database/listings.db')
   print(conn.execute('SELECT COUNT(*) FROM listings').fetchone())
   ```
3. Check browser console for frontend errors

## Next Steps

### Add More Sources

1. Create new scraper in `backend/app/scrapers/`
2. Follow pattern from `idealist.py`
3. Register in `__init__.py`
4. Update admin API to support new source

### Customize UI

- Edit `frontend/src/components/` for component changes
- Edit `frontend/src/pages/` for page layout
- Modify `frontend/tailwind.config.js` for styling

### Deploy to Production

See `PROJECT_README.md` for deployment checklist and Docker instructions.

## Getting Help

- Check `PROJECT_README.md` for detailed documentation
- Review code comments in source files
- Open an issue on GitHub
- Email: srodagi@depaul.edu

## Common Tasks

### Run Tests
```bash
cd backend
pytest tests/ -v
```

### Format Code
```bash
black app/ tests/
```

### Build Frontend for Production
```bash
cd frontend
npm run build
# Output in dist/ directory
```

### Export Database
```bash
sqlite3 database/listings.db .dump > backup.sql
```

### Import Database
```bash
sqlite3 database/listings.db < backup.sql
```

## Success!

If you see listings with visa assessments, you're all set!

Browse the UI, try different filters, and explore the detailed reasoning for each assessment.
