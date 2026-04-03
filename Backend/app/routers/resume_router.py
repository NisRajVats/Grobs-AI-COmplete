"""
Resume router for managing resumes.
Includes multi-resume support and all resume actions.
"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Any

from app.database.session import get_db
from app.models import User, Resume, ResumeVersion, Notification
from app.utils.dependencies import get_current_user
from app.utils.cache import cache_response
from app.services.resume_service.resume_manager import ResumeManager
from app.services.resume_service.optimizer import ResumeOptimizer
from app.services.job_service.job_matcher import JobMatcher
from app.services.resume_service.resume_pipeline import ResumePipelineService
from app.schemas.resume import (
    ResumeCreate,
    ResumeUpdate,
    ResumeResponse,
    ResumeDetailResponse,
    ATSScoreRequest,
    OptimizeResumeRequest,
    OptimizeResumeResponse,
    ResumeVersionResponse,
    BulkDeleteRequest,
    BulkDeleteResponse
)
from app.utils.cache import cache_instance
from app.schemas.job import (
    JobMatchResponse,
    JobRecommendationResponse
)

from app.integrations.cloud_storage import cloud_storage_service

from app.workers.resume_worker import process_resume_parsing, process_ats_analysis

# Backward compatibility alias
JobRecommender = JobMatcher

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])


# ==================== Endpoints ====================

@router.get("", response_model=List[ResumeResponse])
@cache_response(ttl=60)
async def get_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all resumes for current user."""
    manager = ResumeManager(db)
    resumes = manager.get_user_resumes(current_user.id)
    return resumes


@router.post("", response_model=ResumeResponse)
async def create_resume(
    resume_data: ResumeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new resume."""
    manager = ResumeManager(db)
    resume = manager.create_resume(
        user=current_user,
        resume_data=resume_data.dict()
    )
    
    # Clear cache for get_resumes
    cache_instance.clear()
    
    return resume


@router.post("/upload", response_model=ResumeDetailResponse)
async def upload_resume(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    target_role: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a resume PDF file and parse immediately."""
    logger = logging.getLogger(__name__)
    try:
        # Read file content
        file_content = await file.read()
        logger.info(f"Upload started: filename={file.filename}, size={len(file_content)}, title={title}, target_role={target_role}")
        
        manager = ResumeManager(db)
        
        # Create resume with file
        resume = manager.create_resume(
            user=current_user,
            resume_data={
                "full_name": "Uploaded Resume",
                "email": current_user.email,
                "title": title or file.filename,
                "target_role": target_role
            },
            file_content=file_content,
            filename=file.filename
        )
        
        # IMMEDIATELY parse (sync) - populate parsed_data + nested tables
        await manager.parse_resume_file(resume.id, current_user.id)
        
        # Explicitly reload the resume from DB to get the latest state after parsing
        from sqlalchemy.orm import selectinload
        resume = db.query(Resume).options(
            selectinload(Resume.education),
            selectinload(Resume.experience),
            selectinload(Resume.projects),
            selectinload(Resume.skills),
            selectinload(Resume.versions),
            selectinload(Resume.analyses)
        ).filter(Resume.id == resume.id, Resume.user_id == current_user.id).first()
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found after parsing")
        
        # Create notification
        try:
            notif = Notification(
                user_id=current_user.id,
                title="Resume Parsed",
                message=f"'{title or file.filename}' successfully parsed and loaded!",
                type="success",
                action_url=f"/app/resumes/{resume.id}"
            )
            db.add(notif)
            db.commit()
        except Exception:
            pass
        
        # Return FULL response with parsed_data for frontend
        return ResumeDetailResponse.from_orm(resume)
    
    except ValueError as e:
        logger = logging.getLogger(__name__)
        logger.error(f"ValueError in upload_resume: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception(f"Unexpected error in upload_resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading resume: {str(e)}")


@router.get("/{resume_id}", response_model=ResumeDetailResponse)
@cache_response(ttl=60)
async def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific resume with all details."""
    manager = ResumeManager(db)
    resume = manager.get_resume(resume_id, current_user.id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Use our custom from_orm to handle complex fields
    return ResumeDetailResponse.from_orm(resume)

@router.put("/{resume_id}", response_model=ResumeDetailResponse)
async def update_resume(
    resume_id: int,
    resume_data: ResumeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a resume."""
    manager = ResumeManager(db)
    
    # Filter out None values
    update_data = {k: v for k, v in resume_data.dict().items() if v is not None}
    
    resume = manager.update_resume(resume_id, current_user.id, update_data)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    return ResumeDetailResponse.from_orm(resume)


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a resume."""
    manager = ResumeManager(db)
    success = manager.delete_resume(resume_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    return {"message": "Resume deleted successfully"}


@router.post("/{resume_id}/parse")
async def parse_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Parse a resume PDF and extract data."""
    manager = ResumeManager(db)
    result = await manager.parse_resume_file(resume_id, current_user.id)
    
    if not result:
        raise HTTPException(status_code=400, detail="Could not parse resume")
    
    return {"message": "Resume parsed successfully", "data": result}


@router.post("/{resume_id}/ats-score")
async def get_ats_score(
    resume_id: int,
    request: Optional[ATSScoreRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ATS score for a resume."""
    manager = ResumeManager(db)
    resume = manager.get_resume(resume_id, current_user.id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
        
    job_description = request.job_description if request else ""
    result = await manager.get_ats_score(resume_id, current_user.id, job_description)
    
    if not result:
        raise HTTPException(status_code=400, detail="Could not calculate ATS score")
    
    return result


@router.post("/{resume_id}/ats-check")
async def ats_check(
    resume_id: int,
    request: Optional[ATSScoreRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Alias for get_ats_score for frontend compatibility."""
    return await get_ats_score(resume_id, request, current_user, db)


@router.post("/{resume_id}/job-match", response_model=JobRecommendationResponse)
async def match_jobs(
    resume_id: int,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Match resume to jobs (POST version)."""
    manager = ResumeManager(db)
    resume = manager.get_resume(resume_id, current_user.id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
        
    recommender = JobRecommender(db)
    matches = await recommender.match_resume_to_jobs(resume_id, current_user.id, limit)
    
    return {
        "resume_id": resume_id,
        "recommendations": matches,
        "total": len(matches)
    }


@router.get("/{resume_id}/job-recommendations", response_model=JobRecommendationResponse)
@cache_response(ttl=300)
async def get_job_recommendations(
    resume_id: int,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get job recommendations for resume (GET version for frontend)."""
    return await match_jobs(resume_id, limit, current_user, db)


@router.post("/{resume_id}/optimize", response_model=OptimizeResumeResponse)
async def optimize_resume(
    resume_id: int,
    request: OptimizeResumeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Optimize a resume using AI."""
    manager = ResumeManager(db)
    resume = manager.get_resume(resume_id, current_user.id)
    if not resume:
        raise HTTPException(
            status_code=404, 
            detail=f"Resume with id {resume_id} not found or you don't have access to it"
        )
    
    # Validate that the resume has necessary data for optimization
    if not resume.parsed_data and not resume.summary and not resume.experience:
        raise HTTPException(
            status_code=400,
            detail="Resume has insufficient data for optimization. Please add content to your resume first."
        )
        
    optimizer = ResumeOptimizer(db)
    try:
        result = await optimizer.optimize_resume(
            resume_id=resume_id,
            user_id=current_user.id,
            optimization_type=request.optimization_type,
            job_description=request.job_description,
            job_id=request.job_id,
            save_as_new=request.save_as_new
        )
        
        if not result["success"]:
            error_msg = result.get("error", "Optimization failed")
            raise HTTPException(status_code=400, detail=error_msg)
            
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception(f"Unexpected error during resume optimization for resume {resume_id}")
        raise HTTPException(
            status_code=500, 
            detail="An unexpected error occurred during optimization. Please try again or contact support if the issue persists."
        )


@router.post("/{resume_id}/process-pipeline")
async def process_resume_pipeline(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Run full resume processing pipeline (parse -> embed -> ats-score)."""
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
        
    pipeline = ResumePipelineService(db)
    
    # Check if we have a file path
    if resume.file_path:
        result = await pipeline.process_resume_upload(resume_id, resume.file_path, current_user.id)
    else:
        # For manually created resumes, we skip parsing but need embeddings and ATS
        # Generate embeddings
        embed_result = pipeline.generate_resume_embeddings(resume_id, current_user.id)
        # Run ATS
        ats_result = await pipeline.run_ats_analysis(resume_id, current_user.id)
        
        result = {
            "success": embed_result.get("success") and ats_result.get("success"),
            "resume_id": resume_id,
            "stages_completed": ["embeddings", "ats_analysis"] if embed_result.get("success") and ats_result.get("success") else [],
            "errors": []
        }
        if not embed_result.get("success"): result["errors"].append(f"Embed: {embed_result.get('error')}")
        if not ats_result.get("success"): result["errors"].append(f"ATS: {ats_result.get('error')}")

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=f"Pipeline failed: {', '.join(result.get('errors', []))}")
    
    return result


@router.get("/{resume_id}/versions", response_model=List[ResumeVersionResponse])
@cache_response(ttl=300)
async def get_resume_versions(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all versions of a resume."""
    manager = ResumeManager(db)
    versions = manager.get_resume_versions(resume_id, current_user.id)
    return versions


@router.post("/bulk-delete", response_model=BulkDeleteResponse)
async def bulk_delete_resumes(
    request: BulkDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bulk delete multiple resumes for the current user."""
    if not request.ids:
        raise HTTPException(status_code=400, detail="No resume IDs provided")
    
    manager = ResumeManager(db)
    result = manager.bulk_delete(request.ids, current_user.id)
    
    message = f"Successfully deleted {result['deleted']} resume(s). {result['failed']} failed."
    
    return BulkDeleteResponse(
        deleted=result["deleted"],
        failed=result["failed"],
        message=message
    )


@router.get("/{resume_id}/download")
async def download_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download resume as PDF."""
    manager = ResumeManager(db)
    resume = manager.get_resume(resume_id, current_user.id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if not resume.file_path:
        raise HTTPException(status_code=400, detail="Resume has no associated file for download")
    
    try:
        if hasattr(cloud_storage_service.provider, "_get_file_path"):
            full_path = cloud_storage_service.provider._get_file_path(resume.file_path)
            filename = resume.filename or f"resume_{resume.id}.pdf"
            return FileResponse(full_path, media_type="application/pdf", filename=filename)
        else:
            signed_url = cloud_storage_service.get_file_url(resume.file_path)
            from fastapi.responses import RedirectResponse
            return RedirectResponse(signed_url)
    except Exception as e:
        logging.error(f"Download error for resume {resume_id}: {e}")
        raise HTTPException(status_code=500, detail="Download failed")

@router.get("/{resume_id}/preview")
async def preview_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Preview a resume."""
    return await download_resume(resume_id, current_user, db)
