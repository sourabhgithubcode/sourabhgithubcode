from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
import json
import logging
from datetime import datetime

from app.core.database import db
from app.models import VisaCategory, OverrideRequest
from app.scrapers import IdealistScraper
from app.enrichment import VisaAssessor
from app.core.utils import generate_url_hash, validate_listing_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


class ScrapeRequest(BaseModel):
    sources: List[str] = ["idealist"]
    max_pages: int = 5
    search_terms: str = "volunteer"
    location: str = "United States"


class AssessRequest(BaseModel):
    listing_ids: Optional[List[int]] = None
    assess_all_unassessed: bool = False


@router.post("/scrape")
async def trigger_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Trigger scraping job for selected sources.
    """
    try:
        conn = await db.get_connection()

        # Create scrape job record
        for source in request.sources:
            await conn.execute(
                """
                INSERT INTO scrape_jobs (source_name, status, created_at)
                VALUES (?, 'pending', ?)
                """,
                (source, datetime.utcnow().isoformat())
            )
            await conn.commit()

        await conn.close()

        # Run scraping in background
        background_tasks.add_task(
            run_scrape_job,
            request.sources,
            request.max_pages,
            request.search_terms,
            request.location
        )

        return {
            "message": f"Scrape job started for sources: {', '.join(request.sources)}",
            "sources": request.sources
        }

    except Exception as e:
        logger.error(f"Error triggering scrape: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_scrape_job(
    sources: List[str],
    max_pages: int,
    search_terms: str,
    location: str
):
    """
    Background task to run scraping.
    """
    for source in sources:
        logger.info(f"Starting scrape job for {source}")

        try:
            conn = await db.get_connection()

            # Update job status
            await conn.execute(
                """
                UPDATE scrape_jobs
                SET status = 'running', started_at = ?
                WHERE source_name = ? AND status = 'pending'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (datetime.utcnow().isoformat(), source)
            )
            await conn.commit()

            # Initialize scraper
            if source == "idealist":
                scraper = IdealistScraper()
            else:
                logger.warning(f"Unknown source: {source}")
                continue

            # Run scraping
            listings = await scraper.scrape(
                search_terms=search_terms,
                location=location,
                max_pages=max_pages
            )

            # Store listings with deduplication
            new_count = 0
            duplicate_count = 0

            for listing_data in listings:
                # Validate data
                is_valid, flags = validate_listing_data(listing_data)
                listing_data['data_quality_flags'] = json.dumps(flags)

                # Check for duplicates
                url_hash = listing_data['source_url_hash']
                cursor = await conn.execute(
                    "SELECT id FROM listings WHERE source_url_hash = ?",
                    (url_hash,)
                )
                existing = await cursor.fetchone()

                if existing:
                    duplicate_count += 1
                    # Optionally update existing listing
                    continue

                # Insert new listing
                listing_data['scraped_at_utc'] = datetime.utcnow().isoformat()
                listing_data['created_at'] = datetime.utcnow().isoformat()
                listing_data['updated_at'] = datetime.utcnow().isoformat()

                await conn.execute(
                    """
                    INSERT INTO listings (
                        source, source_listing_id, source_url_hash, title, company_name,
                        location, work_mode, employment_type, posted_date, apply_url,
                        description_text, requirements_text, salary_text,
                        scraped_at_utc, raw_html_path, raw_json_path, data_quality_flags,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        listing_data['source'],
                        listing_data.get('source_listing_id'),
                        listing_data['source_url_hash'],
                        listing_data['title'],
                        listing_data['company_name'],
                        listing_data.get('location', 'Unknown'),
                        listing_data.get('work_mode', 'Unknown'),
                        listing_data.get('employment_type', 'Unknown'),
                        listing_data.get('posted_date', 'Unknown'),
                        listing_data['apply_url'],
                        listing_data.get('description_text', ''),
                        listing_data.get('requirements_text', ''),
                        listing_data.get('salary_text', 'Unknown'),
                        listing_data['scraped_at_utc'],
                        listing_data.get('raw_html_path'),
                        listing_data.get('raw_json_path'),
                        listing_data['data_quality_flags'],
                        listing_data['created_at'],
                        listing_data['updated_at']
                    )
                )
                await conn.commit()

                # Get the inserted listing ID
                cursor = await conn.execute("SELECT last_insert_rowid()")
                listing_id = (await cursor.fetchone())[0]

                # Add to assessment queue
                await conn.execute(
                    """
                    INSERT INTO assessment_queue (listing_id, status, created_at)
                    VALUES (?, 'pending', ?)
                    """,
                    (listing_id, datetime.utcnow().isoformat())
                )
                await conn.commit()

                new_count += 1

            # Update job status
            await conn.execute(
                """
                UPDATE scrape_jobs
                SET status = 'completed', completed_at = ?, listings_found = ?
                WHERE source_name = ? AND status = 'running'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (datetime.utcnow().isoformat(), new_count, source)
            )
            await conn.commit()

            await conn.close()

            logger.info(
                f"Scrape job completed for {source}: "
                f"{new_count} new, {duplicate_count} duplicates"
            )

        except Exception as e:
            logger.error(f"Error in scrape job for {source}: {e}")

            # Mark job as failed
            try:
                conn = await db.get_connection()
                await conn.execute(
                    """
                    UPDATE scrape_jobs
                    SET status = 'failed', error_message = ?, completed_at = ?
                    WHERE source_name = ? AND status IN ('pending', 'running')
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (str(e), datetime.utcnow().isoformat(), source)
                )
                await conn.commit()
                await conn.close()
            except:
                pass


@router.post("/assess")
async def trigger_assessment(request: AssessRequest, background_tasks: BackgroundTasks):
    """
    Trigger visa assessment for listings.
    """
    try:
        if request.assess_all_unassessed:
            # Queue all listings without assessment
            conn = await db.get_connection()

            cursor = await conn.execute(
                """
                SELECT l.id FROM listings l
                LEFT JOIN visa_assessments va ON l.id = va.listing_id
                WHERE va.id IS NULL
                """
            )
            rows = await cursor.fetchall()
            listing_ids = [row[0] for row in rows]

            await conn.close()

        else:
            listing_ids = request.listing_ids or []

        if not listing_ids:
            return {"message": "No listings to assess"}

        # Run assessment in background
        background_tasks.add_task(run_assessment_job, listing_ids)

        return {
            "message": f"Assessment started for {len(listing_ids)} listings",
            "listing_count": len(listing_ids)
        }

    except Exception as e:
        logger.error(f"Error triggering assessment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_assessment_job(listing_ids: List[int]):
    """
    Background task to run visa assessments.
    """
    assessor = VisaAssessor()

    for listing_id in listing_ids:
        try:
            logger.info(f"Assessing listing {listing_id}")

            conn = await db.get_connection()

            # Get listing
            cursor = await conn.execute(
                "SELECT * FROM listings WHERE id = ?",
                (listing_id,)
            )
            listing_row = await cursor.fetchone()

            if not listing_row:
                logger.warning(f"Listing {listing_id} not found")
                await conn.close()
                continue

            listing = dict(listing_row)

            # Run assessment
            assessment = await assessor.assess_listing(
                listing_id=listing_id,
                company_name=listing['company_name'],
                job_title=listing['title'],
                job_description=listing['description_text'],
                location=listing['location'],
                apply_url=listing['apply_url'],
                requirements=listing.get('requirements_text')
            )

            # Store assessment
            await conn.execute(
                """
                INSERT INTO visa_assessments (
                    listing_id, visa_category, confidence_score_0_100, confidence_band,
                    reasons_short, reasons_long, evidence_links_json, signals_json,
                    model_version, assessed_at_utc, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    assessment.listing_id,
                    assessment.visa_category.value,
                    assessment.confidence_score_0_100,
                    assessment.confidence_band.value,
                    assessment.reasons_short,
                    assessment.reasons_long,
                    json.dumps(assessment.evidence_links_json),
                    json.dumps(assessment.signals_json),
                    assessment.model_version,
                    assessment.assessed_at_utc,
                    datetime.utcnow().isoformat()
                )
            )
            await conn.commit()

            # Update queue
            await conn.execute(
                """
                UPDATE assessment_queue
                SET status = 'completed', completed_at = ?
                WHERE listing_id = ? AND status = 'pending'
                """,
                (datetime.utcnow().isoformat(), listing_id)
            )
            await conn.commit()

            await conn.close()

            logger.info(f"Assessment completed for listing {listing_id}")

        except Exception as e:
            logger.error(f"Error assessing listing {listing_id}: {e}")


@router.post("/override/{listing_id}")
async def override_assessment(listing_id: int, override: OverrideRequest):
    """
    Allow admin to override visa assessment.
    """
    try:
        conn = await db.get_connection()

        # Check if assessment exists
        cursor = await conn.execute(
            "SELECT id FROM visa_assessments WHERE listing_id = ? ORDER BY created_at DESC LIMIT 1",
            (listing_id,)
        )
        assessment = await cursor.fetchone()

        if not assessment:
            await conn.close()
            raise HTTPException(status_code=404, detail="No assessment found for this listing")

        # Update with override
        await conn.execute(
            """
            UPDATE visa_assessments
            SET human_override_category = ?, human_override_note = ?
            WHERE id = ?
            """,
            (override.category.value, override.note, assessment[0])
        )
        await conn.commit()

        await conn.close()

        return {
            "message": "Assessment overridden successfully",
            "listing_id": listing_id,
            "override_category": override.category.value
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error overriding assessment: {e}")
        raise HTTPException(status_code=500, detail=str(e))
