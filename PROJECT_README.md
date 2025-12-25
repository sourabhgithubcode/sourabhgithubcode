# Chicago Local Clinics Marketing Demand Intelligence

> A comprehensive data-driven system to understand how people discover and choose local clinics in Chicago. Combines search intent, local visibility, and review signals to turn raw public data into actionable marketing insights.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📊 Project Overview

### The Problem

Local clinics spend on marketing without clear visibility into:
- Which services people are actually searching for
- When demand spikes for specific services
- How they rank against local competitors
- What review signals affect their visibility

### The Solution

This system provides **data-driven marketing intelligence** by:
- ✅ Measuring real demand for clinic services by area
- ✅ Comparing clinic visibility vs competitors
- ✅ Linking reviews and ratings to local ranking
- ✅ Identifying high-opportunity services and locations

---

## 🎯 Key Features

### Data Collection
- **Google Places API**: Clinic profiles, ratings, reviews, location data
- **Yelp Fusion API**: Reviews, sentiment proxies, competitor benchmarks
- **Google Trends**: Search demand by service and time

### Analysis & Metrics
- **Visibility Score**: Composite metric based on ratings, reviews, recency, and geography
- **Demand Index**: Real search volume for clinic services
- **Competitor Analysis**: Market density and concentration by ZIP code
- **Opportunity Score**: Demand-to-competition ratio identifying high-potential markets

### Outputs
- 📅 **Daily Refreshed Database**: Automated data collection and updates
- 📊 **Power BI Dashboard**: Interactive visualizations and insights
- 📈 **Actionable Recommendations**: Clear next steps for clinics

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  DATA SOURCES                        │
├──────────────┬──────────────┬──────────────┬────────┤
│ Google Places│ Yelp Fusion  │Google Trends │        │
└──────┬───────┴──────┬───────┴──────┬───────┘        │
       │              │              │                 │
       └──────────────┼──────────────┘                 │
                      ↓                                 │
              ┌───────────────┐                        │
              │  COLLECTORS   │                        │
              │  - Rate limit │                        │
              │  - Retry logic│                        │
              │  - Validation │                        │
              └───────┬───────┘                        │
                      ↓                                 │
              ┌───────────────┐                        │
              │   DATABASE    │                        │
              │  PostgreSQL/  │                        │
              │    SQLite     │                        │
              └───────┬───────┘                        │
                      ↓                                 │
              ┌───────────────┐                        │
              │    ANALYSIS   │                        │
              │  - Scoring    │                        │
              │  - Ranking    │                        │
              │  - Trends     │                        │
              └───────┬───────┘                        │
                      ↓                                 │
         ┌────────────┴────────────┐                  │
         ↓                         ↓                   │
  ┌─────────────┐         ┌────────────────┐         │
  │  Power BI   │         │  SQL Queries   │         │
  │  Dashboard  │         │  & Reports     │         │
  └─────────────┘         └────────────────┘         │
```

---

## 📁 Project Structure

```
sourabhgithubcode/
├── config/
│   └── settings.py              # Configuration management
├── src/
│   ├── collectors/
│   │   ├── google_places_collector.py
│   │   ├── yelp_collector.py
│   │   └── trends_collector.py
│   ├── database/
│   │   ├── models.py           # SQLAlchemy ORM models
│   │   └── init_db.py          # Database initialization
│   ├── analysis/
│   │   └── scoring_engine.py   # Metrics calculation
│   └── utils/
│       └── scheduler.py        # Automated pipeline
├── sql/
│   └── kpi_queries.sql         # Pre-built dashboard queries
├── dashboards/
│   └── POWERBI_SETUP.md        # Dashboard setup guide
├── docs/
│   └── SETUP_GUIDE.md          # Installation guide
├── data/
│   ├── raw/                    # Raw collected data
│   └── processed/              # Processed datasets
├── logs/                       # Application logs
├── tests/                      # Unit tests
├── .env.example                # Environment template
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+ or SQLite 3
- Google Places API key
- Yelp Fusion API key

### Installation

```bash
# Clone the repository
git clone https://github.com/sourabhgithubcode/clinic-demand-intelligence.git
cd clinic-demand-intelligence

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and database settings

# Initialize database
python src/database/init_db.py create
```

### First Run

```bash
# Collect initial data (may take 2-4 hours)
python src/utils/scheduler.py --mode once

# Or run components individually
python src/collectors/google_places_collector.py
python src/collectors/yelp_collector.py
python src/collectors/trends_collector.py
python src/analysis/scoring_engine.py
```

### Schedule Daily Refresh

```bash
python src/utils/scheduler.py --mode scheduled
```

---

## 📊 Key Performance Indicators (KPIs)

### Search Demand Metrics
- **Search Demand Index**: Normalized search volume by service (0-100)
- **Trend Direction**: Increasing / Stable / Decreasing
- **Peak Periods**: Identified high-demand timeframes

### Visibility Metrics
- **Overall Visibility Score**: Composite 0-100 score
  - Rating Score (30%)
  - Review Volume Score (30%)
  - Recency Score (25%)
  - Geographic Score (15%)
- **Local Rank**: Position within ZIP code
- **City Rank**: Position across Chicago

### Competition Metrics
- **Competitor Density**: Clinics per ZIP code
- **Market Concentration**: Top 3 clinic market share
- **Average Rating**: Benchmark by area
- **Review Distribution**: High vs low-reviewed clinics

### Opportunity Metrics
- **Demand-to-Competition Ratio**: Higher = better opportunity
- **Opportunity Score**: Composite metric for market entry
- **Underserved Markets**: High demand, low supply areas

---

## 📈 Sample Insights

### High-Opportunity Markets
```
ZIP Code | Service       | Demand Index | Clinics | Opportunity Score
---------|---------------|--------------|---------|------------------
60618    | Urgent Care   | 87           | 3       | 94.5
60614    | Dental        | 82           | 5       | 89.3
60647    | Primary Care  | 79           | 4       | 87.1
```

### Top Performing Clinics
```
Clinic Name              | Visibility | City Rank | Reviews | Rating
-------------------------|------------|-----------|---------|-------
Chicago Immediate Care   | 94.2       | 1         | 1,247   | 4.8
Lincoln Park Health      | 91.8       | 2         | 892     | 4.7
```

### Search Trends
```
Service       | Current | Previous | Change  | Trend
--------------|---------|----------|---------|-------
Urgent Care   | 76      | 68       | +11.8%  | ↑↑
Dental        | 64      | 62       | +3.2%   | →
Primary Care  | 58      | 61       | -4.9%   | ↓
```

---

## 🗃️ Database Schema

### Core Tables
- **clinics**: Master clinic information (Google + Yelp)
- **reviews**: All reviews from both sources
- **search_trends**: Google Trends data over time
- **visibility_scores**: Calculated daily visibility metrics
- **demand_metrics**: Demand analysis by service/location
- **competitor_analysis**: Market density analysis
- **data_collection_logs**: Collection monitoring

See `src/database/models.py` for complete schema.

---

## 🎨 Power BI Dashboard

The system includes a complete Power BI dashboard with:

1. **Executive Overview**: High-level KPIs and trends
2. **Market Opportunity Map**: Geographic heatmap of opportunities
3. **Competitive Analysis**: Competitor density and positioning
4. **Search Demand Trends**: Time-series analysis
5. **Clinic Performance**: Individual clinic scorecards
6. **Review Analytics**: Sentiment and rating analysis
7. **Data Collection Monitor**: System health dashboard

Setup guide: [`dashboards/POWERBI_SETUP.md`](dashboards/POWERBI_SETUP.md)

---

## 🔧 Configuration

### API Rate Limits
```ini
API_RATE_LIMIT_DELAY=1.0    # Seconds between requests
MAX_RETRIES=3               # Retry failed requests
```

### Service Categories
```ini
SERVICE_KEYWORDS=urgent care,walk-in clinic,family doctor,dental emergency
```

### Geographic Scope
```ini
TARGET_CITY=Chicago
TARGET_STATE=IL
SEARCH_RADIUS_METERS=5000
```

---

## 📖 Documentation

- [Setup Guide](docs/SETUP_GUIDE.md) - Complete installation instructions
- [Power BI Setup](dashboards/POWERBI_SETUP.md) - Dashboard configuration
- [Database Schema](src/database/models.py) - Table definitions
- [KPI Queries](sql/kpi_queries.sql) - Pre-built SQL queries

---

## 🧪 Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=src tests/
```

---

## 🛠️ Maintenance

### Daily Tasks
- Monitor collection logs
- Check for API errors
- Verify data quality

### Weekly Tasks
- Review metrics accuracy
- Check storage usage
- Validate trends

### Monthly Tasks
- Archive old data (>1 year)
- Review API costs
- Update service keywords

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Sourabh Rodagi**

- MS Business Analytics Candidate at DePaul University
- Email: srodagi@depaul.edu
- LinkedIn: [Sourabh Rodagi](https://linkedin.com/in/sourabh-rodagi)
- Portfolio: [sourabhrodagi.com](https://sourabhrodagi.com)

---

## 🙏 Acknowledgments

- Google Places API for clinic data
- Yelp Fusion API for reviews and ratings
- Google Trends for search demand data
- Open-source Python community

---

## 📞 Support

For questions or issues:
- 📧 Email: srodagi@depaul.edu
- 📚 Check [Setup Guide](docs/SETUP_GUIDE.md)
- 🐛 Report bugs via GitHub Issues

---

## 🗺️ Roadmap

- [ ] Add sentiment analysis for reviews
- [ ] Include social media signals
- [ ] Expand to other cities
- [ ] Add predictive demand forecasting
- [ ] Build web-based dashboard
- [ ] Add real-time alerts for market changes

---

**Built with ❤️ using Python, PostgreSQL, and Power BI**
