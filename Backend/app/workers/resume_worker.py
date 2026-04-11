"""
Background worker for resume processing tasks.
Celery task for full pipeline + individual stages.
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.database.session import SessionLocal
from app.workers.celery_app import celery
from app.services.resume_service.resume_pipeline import ResumePipelineService
from app.services.resume_service.resume_manager import ResumeManager
from app.services.resume_service.optimizer import ResumeOptimizer

if celery:
    @celery.task(bind=True, name='resume_worker.process_full_pipeline', max_retries=3)
    def process_resume_full_pipeline(self, resume_id: int, user_id: int):
        """Celery task: Full resume pipeline (parse → embed → ATS → match)."""
        db = SessionLocal()
        try:
            logger.info(f"Celery task: Starting full pipeline for resume {resume_id}")
            
            from app.models.resume import Resume
            resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user_id).first()
            if not resume or not resume.file_path:
                raise ValueError(f"Resume {resume_id} not found or no file_path")
            
            pipeline = ResumePipelineService(db)
            # Use await because process_resume_upload is async, 
            # but since this is a Celery task (which is usually sync-run by the worker unless using an async worker),
            # we might need to run it in a loop if it was async.
            # Actually, the original code called it like result = pipeline.process_resume_upload(...) which suggested it might have been sync or they were missing await.
            # Let's check if we should use an event loop.
            import asyncio
            result = asyncio.run(pipeline.process_resume_upload(resume_id, resume.file_path, user_id))
            
            if result.get("success"):
                logger.info(f"Pipeline complete for resume {resume_id}")
            else:
                logger.error(f"Pipeline failed for resume {resume_id}: {result.get('errors')}")
                raise ValueError(f"Pipeline failed: {result.get('errors')}")
        except Exception as e:
            logger.error(f"Pipeline Celery task failed for resume {resume_id}: {str(e)}")
            raise self.retry(exc=e)
        finally:
            db.close()
else:
    def process_resume_full_pipeline(resume_id: int, user_id: int):
        """Sync fallback: Full resume pipeline (parse → embed → ATS → match)."""
        logger.warning(f"Celery unavailable. Running sync fallback for resume {resume_id}")
        db = SessionLocal()
        try:
            logger.info(f"Sync pipeline: Starting full pipeline for resume {resume_id}")
            
            from app.models.resume import Resume
            resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user_id).first()
            if not resume or not resume.file_path:
                raise ValueError(f"Resume {resume_id} not found or no file_path")
            
            pipeline = ResumePipelineService(db)
            import asyncio
            result = asyncio.run(pipeline.process_resume_upload(resume_id, resume.file_path, user_id))
            
            if result.get("success"):
                logger.info(f"Sync pipeline complete for resume {resume_id}")
            else:
                logger.error(f"Sync pipeline failed for resume {resume_id}: {result.get('errors')}")
                raise ValueError(f"Pipeline failed: {result.get('errors')}")
        except Exception as e:
            logger.error(f"Sync pipeline failed for resume {resume_id}: {str(e)}")
            raise
        finally:
            db.close()


def process_resume_parsing(resume_id: int, user_id: int):
    """Background task to parse a resume PDF."""
    db = SessionLocal()
    try:
        logger.info(f"Starting resume parsing for resume {resume_id}")
        manager = ResumeManager(db)
        import asyncio
        result = asyncio.run(manager.parse_resume_file(resume_id, user_id))
        if result:
            logger.info(f"Successfully parsed resume {resume_id}")
        else:
            logger.warning(f"Failed to parse resume {resume_id}")
    except Exception as e:
        logger.error(f"Error parsing resume {resume_id}: {str(e)}")
    finally:
        db.close()


def process_ats_analysis(resume_id: int, user_id: int, job_description: str = ""):
    """Background task to calculate ATS score."""
    db = SessionLocal()
    try:
        logger.info(f"Starting ATS analysis for resume {resume_id}")
        manager = ResumeManager(db)
        import asyncio
        result = asyncio.run(manager.get_ats_score(resume_id, user_id, job_description))
        if result:
            logger.info(f"ATS score calculated for resume {resume_id}: {result.get('overall_score')}")
        else:
            logger.warning(f"Failed to calculate ATS score for resume {resume_id}")
    except Exception as e:
        logger.error(f"Error in ATS analysis for resume {resume_id}: {str(e)}")
    finally:
        db.close()


def process_resume_optimization(resume_id: int, user_id: int, optimization_type: str = "comprehensive", job_description: str = ""):
    """Background task to optimize a resume."""
    db = SessionLocal()
    try:
        logger.info(f"Starting AI-powered resume optimization for resume {resume_id}")
        optimizer = ResumeOptimizer(db)
        import asyncio
        result = asyncio.run(optimizer.optimize_resume(
            resume_id=resume_id,
            user_id=user_id,
            optimization_type=optimization_type,
            job_description=job_description
        ))
        
        if result.get("success"):
            from app.models import Resume
            resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user_id).first()
            if resume:
                resume.status = "optimized"
                db.commit()
                logger.info(f"Resume {resume_id} successfully optimized by AI")
        else:
            logger.error(f"AI Optimization failed for resume {resume_id}: {result.get('error')}")
    except Exception as e:
        logger.error(f"Error in AI optimization worker for resume {resume_id}: {str(e)}")
    finally:
        db.close()

# Add .delay() mock to functions when celery is not available
if not celery:
    def add_delay_mock(func):
        def delay(*args, **kwargs):
            """Sync fallback for .delay() - runs in background thread if loop is running."""
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                # Run sync function in threadpool to avoid blocking event loop
                # This also allows the internal asyncio.run() to work
                return loop.run_in_executor(None, func, *args, **kwargs)
            except RuntimeError:
                # No loop running, just call sync
                return func(*args, **kwargs)
        func.delay = delay
        return func

    process_resume_full_pipeline = add_delay_mock(process_resume_full_pipeline)
    process_resume_parsing = add_delay_mock(process_resume_parsing)
    process_ats_analysis = add_delay_mock(process_ats_analysis)
    process_resume_optimization = add_delay_mock(process_resume_optimization)
