# OPT/CPT Friendly Listings Platform

A comprehensive platform for international students to find OPT and CPT friendly job and volunteer opportunities, with AI-powered visa friendliness assessment.

## Overview

This system helps international students on F-1 visas find opportunities that explicitly accept OPT (Optional Practical Training) or CPT (Curricular Practical Training). It uses AI to assess each listing's visa friendliness with confidence scores and evidence-based reasoning.

## Features

### Core Functionality
- **Automated Scraping**: Collects job/volunteer listings from multiple sources (starting with Idealist.org)
- **Data Normalization**: Standardizes all data with "Unknown" defaults for missing fields
- **Deduplication**: Hash-based duplicate detection and prevention
- **AI Assessment**: Uses LLM (Claude or GPT) to assess visa friendliness with evidence
- **Confidence Scoring**: 0-100 scale with band classification (High/Mid/Low/No history)
- **Evidence-Based Reasoning**: Transparent explanations with cited sources

### User Interface
- **Search & Filter**: Keyword, location, work mode, visa category, confidence filters
- **Detailed Views**: Full listing details with expandable reasoning
- **Mobile Responsive**: Clean, accessible interface built with React and Tailwind CSS

### Admin Features
- **Trigger Scraping**: Manual or scheduled scraping jobs
- **Assessment Queue**: Batch processing of visa assessments
- **Human Override**: Admin can override AI assessments with notes
- **Audit Trail**: Full history of changes and assessments

## Architecture

### Backend (Python/FastAPI)
```
backend/
├── app/
│   ├── models/           # Pydantic models and enums
│   ├── api/              # FastAPI endpoints
│   ├── scrapers/         # Web scraping adapters
│   ├── enrichment/       # AI assessment system
│   └── core/             # Config, database, utilities
├── tests/                # Unit and integration tests
├── main.py               # FastAPI application
└── requirements.txt      # Python dependencies
```

### Frontend (React/Vite)
```
frontend/
├── src/
│   ├── components/       # Reusable React components
│   ├── pages/            # Main page components
│   ├── api/              # API client
│   └── hooks/            # Custom React hooks
├── index.html
├── package.json
└── vite.config.js
```

### Database (SQLite → PostgreSQL)
- **listings**: Main job/volunteer listings table
- **visa_assessments**: AI assessment results with evidence
- **assessment_queue**: Background job queue
- **scrape_jobs**: Scraping job tracking
- **source_status**: Source health monitoring

## Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- API keys (Anthropic or OpenAI)

### Backend Setup

1. **Create virtual environment**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp ../.env.example .env
   # Edit .env and add your API keys
   ```

4. **Initialize database**:
   ```bash
   # Database will be auto-created on first run
   python main.py
   ```

5. **Run backend**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Run development server**:
   ```bash
   npm run dev
   ```

3. **Build for production**:
   ```bash
   npm run build
   ```

## Usage

### API Endpoints

#### Public Endpoints
- `GET /` - API information
- `GET /health` - Health check
- `GET /listings` - Get listings with filters
- `GET /listings/{id}` - Get detailed listing

**Example**:
```bash
# Get high-confidence OPT/CPT friendly remote jobs
curl "http://localhost:8000/listings?visa_category=High&work_mode=Remote"
```

#### Admin Endpoints
- `POST /admin/scrape` - Trigger scraping job
- `POST /admin/assess` - Trigger assessment
- `POST /admin/override/{id}` - Override assessment

**Example**:
```bash
# Trigger scraping
curl -X POST http://localhost:8000/admin/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "sources": ["idealist"],
    "max_pages": 5,
    "search_terms": "volunteer",
    "location": "United States"
  }'
```

### Filter Parameters

| Parameter | Type | Options |
|-----------|------|---------|
| keyword | string | Search in title, description, company |
| location | string | City, State, Country |
| work_mode | enum | Remote, Hybrid, On-site |
| visa_category | enum | High, Mid, Low, No history so far |
| confidence_band | enum | High, Mid, Low, No history so far |
| min_confidence_score | int | 0-100 |
| max_confidence_score | int | 0-100 |
| sort_by | enum | posted_date, confidence_score, scraped_at_utc |
| sort_order | enum | asc, desc |
| limit | int | 1-500 (default: 50) |
| offset | int | Pagination offset |

## Visa Category Definitions

### High (90-100% confidence)
Strong evidence of OPT/CPT acceptance:
- Explicit statement in job posting
- Company careers page mentions OPT/CPT
- Multiple credible reports of international student hires

### Mid (70-89% confidence)
Some evidence of visa friendliness:
- H-1B sponsorship history
- E-Verify participation
- International hiring patterns
- Flexible language, no restrictions

### Low (40-69% confidence)
Little or conflicting evidence:
- "No sponsorship" statements
- Citizenship requirements
- Security clearance needed

### No history so far (0-39% confidence)
No usable signals found after all checks

## Data Quality

### Validation Rules
- All required fields must be present (title, company, apply_url)
- Missing optional fields default to "Unknown"
- Description minimum 50 characters (flagged if shorter)
- Location normalized to "City, State, Country" format
- Work mode normalized to fixed set

### Quality Flags
Listings are tagged with quality issues:
- `missing_description` - No description text
- `short_description` - Less than 50 characters
- `too_many_unknowns` - 4+ fields are "Unknown"
- `missing_title` / `missing_company` - Critical fields missing

## AI Assessment System

### Evidence Collection
1. **Web Search**: Company website, careers page
2. **Pattern Matching**: Explicit visa keywords in posting
3. **Signal Extraction**: Positive, negative, neutral indicators
4. **Source Tracking**: All evidence URLs and excerpts saved

### Assessment Rules
- Confidence capped at 60% without strong evidence
- Explicit restrictions → Low category
- Multiple positive signals → High category
- Evidence older than 24 months downweighted

### LLM Prompt
The system uses a structured prompt that:
- Separates facts from inference
- Requires evidence citations
- Enforces category definitions
- Returns structured JSON response

## Development

### Adding New Scrapers

1. Create new scraper class inheriting from `BaseScraper`:
   ```python
   from app.scrapers.base import BaseScraper

   class NewSiteScraper(BaseScraper):
       def __init__(self):
           super().__init__("newsite")

       async def get_listing_urls(self, **kwargs):
           # Implementation
           pass

       async def parse_listing(self, url, html):
           # Implementation
           pass
   ```

2. Register in `app/scrapers/__init__.py`

3. Update admin endpoint to support new source

### Running Tests

```bash
cd backend
pytest tests/ -v
```

### Code Quality

```bash
# Format code
black app/ tests/

# Lint
ruff check app/ tests/
```

## Deployment

### Environment Variables
See `.env.example` for all configuration options.

### Production Checklist
- [ ] Set `DATABASE_URL` to PostgreSQL
- [ ] Configure API keys
- [ ] Set up rate limiting
- [ ] Enable logging to file/service
- [ ] Configure CORS for production domain
- [ ] Set up scheduled scraping (cron/Celery)
- [ ] Enable HTTPS
- [ ] Set up monitoring/alerts

### Docker (Optional)
```bash
# Build
docker build -t opt-cpt-listings .

# Run
docker run -p 8000:8000 --env-file .env opt-cpt-listings
```

## Roadmap

### Planned Features
- [ ] More data sources (LinkedIn, Indeed, etc.)
- [ ] Email alerts for new high-confidence listings
- [ ] User accounts and saved searches
- [ ] Mobile app
- [ ] Company directory with visa stats
- [ ] Verification from actual students
- [ ] Integration with university career services

### Improvements
- [ ] Headless browser for JavaScript-heavy sites
- [ ] Better natural language date parsing
- [ ] Company name normalization/deduplication
- [ ] ML-based duplicate detection
- [ ] Scheduled background jobs with Celery
- [ ] Redis caching layer
- [ ] Full-text search with Elasticsearch

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - see LICENSE file for details

## Support

For questions or issues:
- GitHub Issues: [Create an issue](https://github.com/sourabhgithubcode/sourabhgithubcode/issues)
- Email: srodagi@depaul.edu

## Acknowledgments

Built by Sourabh Rodagi for helping international students find visa-friendly opportunities.

Special thanks to the international student community for inspiration and feedback.
