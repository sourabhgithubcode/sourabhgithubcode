from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import json
import logging

from app.models import Listing, ListingResponse, ListingFilters
from app.core.database import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("", response_model=dict)
async def get_listings(
    keyword: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    work_mode: Optional[str] = Query(None),
    visa_category: Optional[str] = Query(None),
    confidence_band: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    posted_date_start: Optional[str] = Query(None),
    posted_date_end: Optional[str] = Query(None),
    min_confidence_score: Optional[int] = Query(None, ge=0, le=100),
    max_confidence_score: Optional[int] = Query(None, ge=0, le=100),
    sort_by: str = Query("scraped_at_utc", pattern="^(posted_date|confidence_score|scraped_at_utc)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    Get listings with filters and pagination.
    """
    try:
        conn = await db.get_connection()

        # Build query
        query = """
            SELECT
                l.*,
                va.visa_category,
                va.confidence_score_0_100,
                va.confidence_band,
                va.reasons_short,
                va.assessed_at_utc
            FROM listings l
            LEFT JOIN visa_assessments va ON l.id = va.listing_id
            WHERE 1=1
        """
        params = []

        # Apply filters
        if keyword:
            query += " AND (l.title LIKE ? OR l.description_text LIKE ? OR l.company_name LIKE ?)"
            pattern = f"%{keyword}%"
            params.extend([pattern, pattern, pattern])

        if location:
            query += " AND l.location LIKE ?"
            params.append(f"%{location}%")

        if work_mode:
            query += " AND l.work_mode = ?"
            params.append(work_mode)

        if visa_category:
            query += " AND va.visa_category = ?"
            params.append(visa_category)

        if confidence_band:
            query += " AND va.confidence_band = ?"
            params.append(confidence_band)

        if source:
            query += " AND l.source = ?"
            params.append(source)

        if posted_date_start:
            query += " AND l.posted_date >= ?"
            params.append(posted_date_start)

        if posted_date_end:
            query += " AND l.posted_date <= ?"
            params.append(posted_date_end)

        if min_confidence_score is not None:
            query += " AND va.confidence_score_0_100 >= ?"
            params.append(min_confidence_score)

        if max_confidence_score is not None:
            query += " AND va.confidence_score_0_100 <= ?"
            params.append(max_confidence_score)

        # Add sorting
        sort_field_map = {
            "posted_date": "l.posted_date",
            "confidence_score": "va.confidence_score_0_100",
            "scraped_at_utc": "l.scraped_at_utc"
        }
        sort_field = sort_field_map.get(sort_by, "l.scraped_at_utc")
        query += f" ORDER BY {sort_field} {sort_order.upper()}"

        # Add pagination
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        # Execute query
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()

        # Count total
        count_query = query.split("ORDER BY")[0].replace(
            "SELECT l.*, va.visa_category, va.confidence_score_0_100, va.confidence_band, va.reasons_short, va.assessed_at_utc",
            "SELECT COUNT(*)"
        )
        count_cursor = await conn.execute(count_query, params[:-2])  # Exclude limit/offset
        total = (await count_cursor.fetchone())[0]

        # Format results
        listings = []
        for row in rows:
            listing_dict = dict(row)
            # Parse data_quality_flags from JSON
            if listing_dict.get('data_quality_flags'):
                try:
                    listing_dict['data_quality_flags'] = json.loads(listing_dict['data_quality_flags'])
                except:
                    listing_dict['data_quality_flags'] = []

            listings.append(listing_dict)

        await conn.close()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": listings
        }

    except Exception as e:
        logger.error(f"Error getting listings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{listing_id}", response_model=dict)
async def get_listing(listing_id: int):
    """
    Get detailed listing with visa assessment and evidence.
    """
    try:
        conn = await db.get_connection()

        # Get listing
        cursor = await conn.execute(
            "SELECT * FROM listings WHERE id = ?",
            (listing_id,)
        )
        listing_row = await cursor.fetchone()

        if not listing_row:
            await conn.close()
            raise HTTPException(status_code=404, detail="Listing not found")

        listing = dict(listing_row)

        # Parse data_quality_flags
        if listing.get('data_quality_flags'):
            try:
                listing['data_quality_flags'] = json.loads(listing['data_quality_flags'])
            except:
                listing['data_quality_flags'] = []

        # Get visa assessment
        cursor = await conn.execute(
            "SELECT * FROM visa_assessments WHERE listing_id = ? ORDER BY created_at DESC LIMIT 1",
            (listing_id,)
        )
        assessment_row = await cursor.fetchone()

        if assessment_row:
            assessment = dict(assessment_row)

            # Parse JSON fields
            if assessment.get('evidence_links_json'):
                try:
                    assessment['evidence_links_json'] = json.loads(assessment['evidence_links_json'])
                except:
                    assessment['evidence_links_json'] = []

            if assessment.get('signals_json'):
                try:
                    assessment['signals_json'] = json.loads(assessment['signals_json'])
                except:
                    assessment['signals_json'] = {"positive": [], "negative": [], "neutral": []}

            listing['visa_assessment'] = assessment
        else:
            listing['visa_assessment'] = None

        await conn.close()

        return listing

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting listing {listing_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
