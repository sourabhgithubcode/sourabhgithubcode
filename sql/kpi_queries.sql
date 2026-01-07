-- =====================================================
-- Chicago Clinic Demand Intelligence - KPI Queries
-- =====================================================
-- These queries power the Power BI dashboard and reports

-- =====================================================
-- 1. TOP PERFORMING CLINICS BY VISIBILITY
-- =====================================================
-- Shows clinics with highest visibility scores
SELECT
    c.name,
    c.address,
    c.city,
    c.zip_code,
    c.google_rating,
    c.yelp_rating,
    (COALESCE(c.google_review_count, 0) + COALESCE(c.yelp_review_count, 0)) as total_reviews,
    vs.overall_visibility_score,
    vs.rating_score,
    vs.review_volume_score,
    vs.recency_score,
    vs.geographic_score,
    vs.local_rank,
    vs.city_rank
FROM clinics c
JOIN visibility_scores vs ON c.id = vs.clinic_id
WHERE vs.calculation_date = CURRENT_DATE
    AND c.is_active = TRUE
ORDER BY vs.overall_visibility_score DESC
LIMIT 50;


-- =====================================================
-- 2. HIGH-OPPORTUNITY MARKETS
-- =====================================================
-- Identifies ZIP codes with high demand and low competition
SELECT
    dm.zip_code,
    dm.service_category,
    dm.search_demand_index,
    dm.clinic_count,
    dm.demand_to_competition_ratio,
    dm.opportunity_score,
    dm.search_volume_trend,
    dm.avg_rating,
    ca.total_clinics as total_competitors
FROM demand_metrics dm
LEFT JOIN competitor_analysis ca
    ON dm.zip_code = ca.zip_code
    AND dm.calculation_date = ca.calculation_date
WHERE dm.calculation_date = CURRENT_DATE
ORDER BY dm.opportunity_score DESC
LIMIT 100;


-- =====================================================
-- 3. SEARCH DEMAND TRENDS BY SERVICE
-- =====================================================
-- Shows search interest trends over time by service category
SELECT
    service_category,
    DATE(date) as trend_date,
    AVG(interest_score) as avg_interest,
    AVG(interest_7day_avg) as seven_day_avg,
    AVG(interest_30day_avg) as thirty_day_avg
FROM search_trends
WHERE date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY service_category, DATE(date)
ORDER BY service_category, trend_date;


-- =====================================================
-- 4. COMPETITOR DENSITY BY ZIP CODE
-- =====================================================
-- Shows competitive landscape across Chicago ZIP codes
SELECT
    zip_code,
    total_clinics,
    avg_rating,
    avg_review_count,
    high_rated_count,
    low_review_count,
    top_3_market_share,
    ROUND((high_rated_count::NUMERIC / NULLIF(total_clinics, 0)) * 100, 2) as pct_high_rated
FROM competitor_analysis
WHERE calculation_date = CURRENT_DATE
ORDER BY total_clinics DESC;


-- =====================================================
-- 5. REVIEW SENTIMENT ANALYSIS
-- =====================================================
-- Analyzes review ratings and sentiment by clinic
SELECT
    c.name,
    c.zip_code,
    COUNT(r.id) as total_reviews,
    ROUND(AVG(r.rating), 2) as avg_review_rating,
    COUNT(CASE WHEN r.rating >= 4 THEN 1 END) as positive_reviews,
    COUNT(CASE WHEN r.rating = 3 THEN 1 END) as neutral_reviews,
    COUNT(CASE WHEN r.rating <= 2 THEN 1 END) as negative_reviews,
    ROUND((COUNT(CASE WHEN r.rating >= 4 THEN 1 END)::NUMERIC / COUNT(r.id)) * 100, 2) as positive_pct
FROM clinics c
LEFT JOIN reviews r ON c.id = r.clinic_id
WHERE c.is_active = TRUE
GROUP BY c.id, c.name, c.zip_code
HAVING COUNT(r.id) > 0
ORDER BY avg_review_rating DESC, total_reviews DESC;


-- =====================================================
-- 6. MARKET SHARE BY SERVICE TYPE
-- =====================================================
-- Shows distribution of clinics and reviews by service type
SELECT
    clinic_type,
    COUNT(*) as clinic_count,
    ROUND(AVG(COALESCE(google_rating, yelp_rating)), 2) as avg_rating,
    SUM(COALESCE(google_review_count, 0) + COALESCE(yelp_review_count, 0)) as total_reviews,
    ROUND(AVG(COALESCE(google_review_count, 0) + COALESCE(yelp_review_count, 0)), 2) as avg_reviews_per_clinic
FROM clinics
WHERE is_active = TRUE
    AND clinic_type IS NOT NULL
GROUP BY clinic_type
ORDER BY clinic_count DESC;


-- =====================================================
-- 7. GEOGRAPHIC VISIBILITY HEATMAP
-- =====================================================
-- Data for creating geographic heatmap of visibility
SELECT
    c.zip_code,
    COUNT(DISTINCT c.id) as clinic_count,
    ROUND(AVG(vs.overall_visibility_score), 2) as avg_visibility_score,
    ROUND(AVG(c.latitude), 6) as avg_latitude,
    ROUND(AVG(c.longitude), 6) as avg_longitude
FROM clinics c
JOIN visibility_scores vs ON c.id = vs.clinic_id
WHERE vs.calculation_date = CURRENT_DATE
    AND c.is_active = TRUE
    AND c.latitude IS NOT NULL
    AND c.longitude IS NOT NULL
GROUP BY c.zip_code
ORDER BY avg_visibility_score DESC;


-- =====================================================
-- 8. UNDERPERFORMING CLINICS (IMPROVEMENT OPPORTUNITIES)
-- =====================================================
-- Clinics with low visibility scores that could improve
SELECT
    c.name,
    c.address,
    c.zip_code,
    c.phone,
    c.website,
    vs.overall_visibility_score,
    (COALESCE(c.google_review_count, 0) + COALESCE(c.yelp_review_count, 0)) as total_reviews,
    COALESCE(c.google_rating, c.yelp_rating) as rating,
    CASE
        WHEN (COALESCE(c.google_review_count, 0) + COALESCE(c.yelp_review_count, 0)) < 10
        THEN 'Need more reviews'
        WHEN COALESCE(c.google_rating, c.yelp_rating, 0) < 4.0
        THEN 'Improve service quality'
        ELSE 'Increase recent engagement'
    END as improvement_focus
FROM clinics c
JOIN visibility_scores vs ON c.id = vs.clinic_id
WHERE vs.calculation_date = CURRENT_DATE
    AND c.is_active = TRUE
    AND vs.overall_visibility_score < 50
ORDER BY vs.overall_visibility_score ASC
LIMIT 50;


-- =====================================================
-- 9. SEARCH DEMAND VS SUPPLY GAP
-- =====================================================
-- Shows biggest gaps between demand and supply
SELECT
    dm.service_category,
    dm.zip_code,
    dm.search_demand_index,
    dm.clinic_count as supply,
    dm.demand_to_competition_ratio as gap_ratio,
    CASE
        WHEN dm.clinic_count = 0 THEN 'No supply - HIGH OPPORTUNITY'
        WHEN dm.demand_to_competition_ratio > 20 THEN 'High demand gap'
        WHEN dm.demand_to_competition_ratio > 10 THEN 'Moderate demand gap'
        ELSE 'Adequate supply'
    END as market_status
FROM demand_metrics dm
WHERE dm.calculation_date = CURRENT_DATE
    AND dm.search_demand_index > 0
ORDER BY dm.demand_to_competition_ratio DESC
LIMIT 100;


-- =====================================================
-- 10. DAILY COLLECTION STATUS
-- =====================================================
-- Monitors data collection health
SELECT
    collection_type,
    DATE(start_time) as collection_date,
    status,
    records_collected,
    records_updated,
    records_failed,
    EXTRACT(EPOCH FROM (end_time - start_time))/60 as duration_minutes,
    error_message
FROM data_collection_logs
WHERE start_time >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY start_time DESC;


-- =====================================================
-- 11. TRENDING SERVICES (WEEK OVER WEEK)
-- =====================================================
-- Shows which services are trending up or down
WITH weekly_trends AS (
    SELECT
        service_category,
        DATE_TRUNC('week', date) as week,
        AVG(interest_score) as avg_interest
    FROM search_trends
    WHERE date >= CURRENT_DATE - INTERVAL '8 weeks'
    GROUP BY service_category, DATE_TRUNC('week', date)
),
week_comparison AS (
    SELECT
        t1.service_category,
        t1.avg_interest as current_week,
        t2.avg_interest as previous_week,
        ROUND(((t1.avg_interest - t2.avg_interest) / NULLIF(t2.avg_interest, 0)) * 100, 2) as pct_change
    FROM weekly_trends t1
    LEFT JOIN weekly_trends t2
        ON t1.service_category = t2.service_category
        AND t1.week = t2.week + INTERVAL '1 week'
    WHERE t1.week = DATE_TRUNC('week', CURRENT_DATE)
)
SELECT
    service_category,
    current_week as current_interest,
    previous_week as previous_interest,
    pct_change,
    CASE
        WHEN pct_change > 15 THEN 'Surging ↑↑'
        WHEN pct_change > 5 THEN 'Growing ↑'
        WHEN pct_change < -15 THEN 'Declining ↓↓'
        WHEN pct_change < -5 THEN 'Falling ↓'
        ELSE 'Stable →'
    END as trend_status
FROM week_comparison
ORDER BY pct_change DESC;


-- =====================================================
-- 12. EXECUTIVE SUMMARY METRICS
-- =====================================================
-- High-level KPIs for executive dashboard
SELECT
    (SELECT COUNT(*) FROM clinics WHERE is_active = TRUE) as total_active_clinics,
    (SELECT COUNT(DISTINCT zip_code) FROM clinics WHERE is_active = TRUE) as zip_codes_covered,
    (SELECT SUM(COALESCE(google_review_count, 0) + COALESCE(yelp_review_count, 0))
     FROM clinics WHERE is_active = TRUE) as total_reviews_tracked,
    (SELECT ROUND(AVG(overall_visibility_score), 2)
     FROM visibility_scores WHERE calculation_date = CURRENT_DATE) as avg_visibility_score,
    (SELECT service_category
     FROM demand_metrics
     WHERE calculation_date = CURRENT_DATE
     ORDER BY search_demand_index DESC
     LIMIT 1) as highest_demand_service,
    (SELECT zip_code
     FROM demand_metrics
     WHERE calculation_date = CURRENT_DATE
     ORDER BY opportunity_score DESC
     LIMIT 1) as top_opportunity_zip;
