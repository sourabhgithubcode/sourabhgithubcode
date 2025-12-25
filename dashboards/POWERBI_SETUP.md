# Power BI Dashboard Setup Guide

## Chicago Clinic Demand Intelligence - Dashboard Configuration

This guide will help you create a comprehensive Power BI dashboard connected to the Chicago Clinic Demand Intelligence database.

---

## Prerequisites

1. **Power BI Desktop** installed (Download from Microsoft)
2. **Database Access**: Connection credentials to PostgreSQL or SQLite database
3. **ODBC Driver**: PostgreSQL ODBC driver (if using PostgreSQL)

---

## Database Connection Setup

### Option 1: PostgreSQL Connection

1. Open Power BI Desktop
2. Click **Get Data** → **Database** → **PostgreSQL database**
3. Enter connection details:
   - **Server**: `localhost:5432` (or your server address)
   - **Database**: `clinic_intelligence`
4. Select **DirectQuery** or **Import** mode
   - **DirectQuery**: Real-time data, slower performance
   - **Import**: Snapshot data, faster performance (recommended)
5. Enter credentials when prompted
6. Select all tables to import:
   - `clinics`
   - `reviews`
   - `search_trends`
   - `visibility_scores`
   - `demand_metrics`
   - `competitor_analysis`
   - `data_collection_logs`

### Option 2: SQLite Connection

1. Open Power BI Desktop
2. Click **Get Data** → **More** → **Database** → **ODBC**
3. Select SQLite ODBC driver
4. Browse to your database file: `data/clinic_intelligence.db`
5. Import all tables

---

## Dashboard Structure

Create the following pages in your Power BI report:

### 1. Executive Overview

**Key Metrics Cards:**
- Total Active Clinics
- ZIP Codes Covered
- Total Reviews Tracked
- Average Visibility Score
- Highest Demand Service
- Top Opportunity ZIP Code

**Visuals:**
- Trend line: Daily search demand over time
- Bar chart: Clinics by service type
- Donut chart: Market share by ZIP code

**Data Source:**
```sql
-- Use the Executive Summary query from sql/kpi_queries.sql
```

---

### 2. Market Opportunity Map

**Visuals:**
- **Map Visual**: Geographic heatmap showing opportunity scores by ZIP code
  - Latitude/Longitude from clinics table
  - Color by `opportunity_score` from demand_metrics

- **Table**: High-Opportunity Markets
  - ZIP Code
  - Service Category
  - Opportunity Score
  - Demand-to-Competition Ratio
  - Current Clinic Count

**Filters:**
- Service Category slicer
- Opportunity Score range slider
- ZIP Code search

**Data Source:**
```sql
-- Use High-Opportunity Markets query from sql/kpi_queries.sql
```

---

### 3. Competitive Analysis

**Visuals:**
- **Clustered Bar Chart**: Competitor Density by ZIP Code
  - X-axis: ZIP Code
  - Y-axis: Total Clinics
  - Color by average rating

- **Scatter Plot**: Market Position Matrix
  - X-axis: Average Review Count
  - Y-axis: Average Rating
  - Size: Number of clinics
  - Color: ZIP Code

- **Table**: Competitor Details
  - ZIP Code
  - Total Clinics
  - Average Rating
  - Top 3 Market Share
  - High-Rated Count

**Data Source:**
```sql
-- Use Competitor Density query from sql/kpi_queries.sql
```

---

### 4. Search Demand Trends

**Visuals:**
- **Line Chart**: Search Interest Over Time
  - X-axis: Date
  - Y-axis: Interest Score
  - Legend: Service Category
  - Show 7-day and 30-day moving averages

- **KPI Cards**: Week-over-week trends
  - Current week interest
  - Previous week interest
  - % Change
  - Trend indicator (↑ ↓ →)

- **Table**: Trending Services
  - Service Category
  - Current Interest
  - Previous Interest
  - % Change
  - Trend Status

**Filters:**
- Date range slider
- Service category slicer

**Data Source:**
```sql
-- Use Search Demand Trends and Trending Services queries
```

---

### 5. Clinic Performance

**Visuals:**
- **Table**: Top Performing Clinics
  - Name
  - Address
  - Visibility Score
  - City Rank
  - Local Rank
  - Total Reviews
  - Average Rating

- **Gauge Charts**: Performance Metrics
  - Rating Score (0-100)
  - Review Volume Score (0-100)
  - Recency Score (0-100)
  - Geographic Score (0-100)

- **Funnel Chart**: Visibility Score Distribution
  - Show how many clinics fall into each score range

**Filters:**
- ZIP Code slicer
- Clinic type slicer
- Minimum visibility score slider

**Data Source:**
```sql
-- Use Top Performing Clinics query
```

---

### 6. Review Analytics

**Visuals:**
- **Stacked Bar Chart**: Review Sentiment Distribution
  - X-axis: Clinic Name
  - Y-axis: Count
  - Stacks: Positive/Neutral/Negative

- **Line + Column Chart**: Reviews Over Time
  - Columns: Review count
  - Line: Average rating

- **Word Cloud**: Common review themes (requires custom visual)

- **Table**: Review Summary
  - Clinic Name
  - Total Reviews
  - Average Rating
  - Positive %
  - Negative %

**Data Source:**
```sql
-- Use Review Sentiment Analysis query
```

---

### 7. Data Collection Monitor

**Visuals:**
- **Table**: Collection Log
  - Collection Type
  - Date
  - Status
  - Records Collected
  - Records Updated
  - Duration
  - Errors

- **Gauge**: Collection Success Rate

- **Line Chart**: Daily collection volume

**Data Source:**
```sql
-- Use Daily Collection Status query
```

---

## Creating Relationships

Power BI should auto-detect most relationships, but verify these:

1. **clinics** ↔ **reviews**
   - `clinics.id` → `reviews.clinic_id` (One-to-Many)

2. **clinics** ↔ **visibility_scores**
   - `clinics.id` → `visibility_scores.clinic_id` (One-to-Many)

3. **demand_metrics** ↔ **competitor_analysis**
   - `demand_metrics.zip_code` → `competitor_analysis.zip_code` (Many-to-Many)
   - Also relate on `calculation_date`

---

## Custom Measures (DAX)

Add these calculated measures:

### Total Reviews
```dax
TotalReviews =
SUM(clinics[google_review_count]) + SUM(clinics[yelp_review_count])
```

### Average Combined Rating
```dax
AvgCombinedRating =
DIVIDE(
    SUM(clinics[google_rating]) + SUM(clinics[yelp_rating]),
    COUNTROWS(FILTER(clinics, clinics[google_rating] <> BLANK())) +
    COUNTROWS(FILTER(clinics, clinics[yelp_rating] <> BLANK()))
)
```

### Opportunity Index
```dax
OpportunityIndex =
AVERAGE(demand_metrics[opportunity_score])
```

### Market Share %
```dax
MarketShare% =
DIVIDE(
    COUNTROWS(clinics),
    CALCULATE(COUNTROWS(clinics), ALL(clinics[zip_code]))
) * 100
```

---

## Formatting Recommendations

### Color Scheme
- **Primary**: `#0066CC` (Blue)
- **Success**: `#28A745` (Green)
- **Warning**: `#FFC107` (Yellow)
- **Danger**: `#DC3545` (Red)
- **Neutral**: `#6C757D` (Gray)

### Conditional Formatting

**Visibility Scores:**
- 80-100: Dark Green
- 60-79: Light Green
- 40-59: Yellow
- 20-39: Orange
- 0-19: Red

**Trends:**
- Increasing: Green with ↑
- Stable: Yellow with →
- Decreasing: Red with ↓

---

## Refresh Schedule

### For Import Mode:
1. Go to **File** → **Options** → **Data load**
2. Set refresh schedule:
   - **Frequency**: Daily
   - **Time**: After your pipeline runs (e.g., 03:00 AM)

### For Published Reports:
1. Publish to Power BI Service
2. Configure dataset refresh in Power BI Service
3. Set credentials for database connection
4. Schedule automatic refresh

---

## Sample Dashboard Layout

```
┌─────────────────────────────────────────────────────────┐
│  CHICAGO CLINIC DEMAND INTELLIGENCE                     │
│  [Executive Overview]                                    │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│ Total    │ ZIP      │ Total    │ Avg      │ Top         │
│ Clinics  │ Codes    │ Reviews  │ Score    │ Service     │
│  1,234   │   56     │  45,678  │  67.5    │ Urgent Care │
└──────────┴──────────┴──────────┴──────────┴─────────────┘
┌──────────────────────────┬──────────────────────────────┐
│ Search Demand Trends     │ Market Opportunity Map       │
│ [Line Chart]             │ [Geographic Heatmap]         │
│                          │                              │
└──────────────────────────┴──────────────────────────────┘
```

---

## Sharing the Dashboard

### Option 1: Desktop File
1. Save `.pbix` file
2. Share file with stakeholders
3. Recipients need Power BI Desktop

### Option 2: Power BI Service (Recommended)
1. Publish to workspace
2. Share dashboard link
3. Set appropriate permissions
4. Configure row-level security if needed

---

## Troubleshooting

### Connection Issues
- Verify database is running
- Check firewall settings
- Confirm credentials
- Test connection with psql/sqlite3

### Performance Issues
- Use Import mode instead of DirectQuery
- Create aggregated tables
- Limit date range in visuals
- Use query folding where possible

### Data Not Refreshing
- Check data collection logs
- Verify scheduler is running
- Confirm database permissions
- Review error logs

---

## Next Steps

1. Import KPI queries from `sql/kpi_queries.sql`
2. Create calculated measures
3. Design visualizations following this guide
4. Set up automatic refresh
5. Share with stakeholders

---

## Support

For questions or issues:
- Check documentation in `/docs` folder
- Review database schema in `/src/database/models.py`
- Examine SQL queries in `/sql/kpi_queries.sql`
