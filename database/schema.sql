-- Listings table
CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    source_listing_id TEXT,
    source_url_hash TEXT NOT NULL,
    title TEXT NOT NULL,
    company_name TEXT NOT NULL,
    location TEXT NOT NULL DEFAULT 'Unknown',
    work_mode TEXT NOT NULL DEFAULT 'Unknown', -- Remote, Hybrid, On-site, Unknown
    employment_type TEXT NOT NULL DEFAULT 'Unknown',
    posted_date TEXT DEFAULT 'Unknown',
    apply_url TEXT NOT NULL UNIQUE,
    description_text TEXT DEFAULT '',
    requirements_text TEXT DEFAULT '',
    salary_text TEXT DEFAULT 'Unknown',
    scraped_at_utc TEXT NOT NULL,
    raw_html_path TEXT,
    raw_json_path TEXT,
    data_quality_flags TEXT, -- JSON array of flags
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Visa assessment table
CREATE TABLE IF NOT EXISTS visa_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    visa_category TEXT NOT NULL, -- High, Mid, Low, No history so far
    confidence_score_0_100 INTEGER NOT NULL CHECK(confidence_score_0_100 >= 0 AND confidence_score_0_100 <= 100),
    confidence_band TEXT NOT NULL, -- High, Mid, Low, No history so far
    reasons_short TEXT NOT NULL,
    reasons_long TEXT NOT NULL,
    evidence_links_json TEXT, -- JSON array of evidence links with descriptions
    signals_json TEXT, -- JSON object with positive, negative, neutral signals
    model_version TEXT NOT NULL,
    assessed_at_utc TEXT NOT NULL,
    human_override_category TEXT,
    human_override_note TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_listings_source ON listings(source);
CREATE INDEX IF NOT EXISTS idx_listings_scraped_at ON listings(scraped_at_utc);
CREATE INDEX IF NOT EXISTS idx_listings_posted_date ON listings(posted_date);
CREATE INDEX IF NOT EXISTS idx_listings_company ON listings(company_name);
CREATE INDEX IF NOT EXISTS idx_listings_location ON listings(location);
CREATE INDEX IF NOT EXISTS idx_listings_work_mode ON listings(work_mode);
CREATE INDEX IF NOT EXISTS idx_listings_url_hash ON listings(source_url_hash);

CREATE INDEX IF NOT EXISTS idx_visa_assessments_listing ON visa_assessments(listing_id);
CREATE INDEX IF NOT EXISTS idx_visa_assessments_category ON visa_assessments(visa_category);
CREATE INDEX IF NOT EXISTS idx_visa_assessments_confidence_band ON visa_assessments(confidence_band);
CREATE INDEX IF NOT EXISTS idx_visa_assessments_confidence_score ON visa_assessments(confidence_score_0_100);

-- History table for tracking listing updates
CREATE TABLE IF NOT EXISTS listing_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    field_changed TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE
);

-- Source status table for monitoring
CREATE TABLE IF NOT EXISTS source_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'active', -- active, degraded, blocked, disabled
    last_successful_scrape TEXT,
    last_error TEXT,
    last_error_time TEXT,
    consecutive_failures INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Scrape jobs table for scheduling
CREATE TABLE IF NOT EXISTS scrape_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, running, completed, failed
    started_at TEXT,
    completed_at TEXT,
    listings_found INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Assessment queue table
CREATE TABLE IF NOT EXISTS assessment_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, running, completed, failed
    priority INTEGER DEFAULT 5,
    started_at TEXT,
    completed_at TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_assessment_queue_status ON assessment_queue(status);
CREATE INDEX IF NOT EXISTS idx_assessment_queue_priority ON assessment_queue(priority DESC);
