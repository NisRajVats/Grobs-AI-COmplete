"""
Resume router for managing resumes.
Includes multi-resume support and all resume actions.
"""
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Any

from app.database.session import get_db
from app.models import User, Resume, ResumeVersion, Notification
from app.utils.dependencies import get_current_user
from app.services.resume_service.resume_manager import ResumeManager
from app.services.resume_service.optimizer import ResumeOptimizer
from app.services.job_service.job_matcher import JobMatcher
from app.schemas.resume import (
    ResumeCreate,
    ResumeUpdate,
    ResumeResponse,
    ResumeDetailResponse,
    ATSScoreRequest,
    OptimizeResumeRequest,
    OptimizeResumeResponse,
    ResumeVersionResponse
)
from app.schemas.job import (
    JobMatchResponse,
    JobRecommendationResponse
)

from app.integrations.cloud_storage import cloud_storage_service

# Backward compatibility alias
JobRecommender = JobMatcher

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])


# ==================== Endpoints ====================

@router.get("", response_model=List[ResumeResponse])
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
    return resume


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    target_role: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a resume PDF file."""
    try:
        # Read file content
        file_content = await file.read()
        
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
        
        # Parse the resume in background
        try:
            manager.parse_resume_file(resume.id, current_user.id)
        except Exception as e:
            print(f"Error parsing resume: {e}")
        
        # Create notification
        try:
            notif = Notification(
                user_id=current_user.id,
                title="Resume Uploaded",
                message=f"'{title or file.filename}' has been uploaded and is being processed.",
                type="info",
                action_url="/app/resumes"
            )
            db.add(notif)
            db.commit()
        except Exception:
            pass
        
        return {"message": "Resume uploaded successfully", "resume_id": resume.id}
    
    except ValueError as e:
        # Handle storage/upload errors (like S3 failures)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Handle any other errors
        raise HTTPException(status_code=500, detail=f"Error uploading resume: {str(e)}")


@router.get("/{resume_id}", response_model=ResumeDetailResponse)
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
    result = manager.parse_resume_file(resume_id, current_user.id)
    
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
    result = manager.get_ats_score(resume_id, current_user.id, job_description)
    
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
    matches = recommender.match_resume_to_jobs(resume_id, current_user.id, limit)
    
    return {
        "resume_id": resume_id,
        "recommendations": matches,
        "total": len(matches)
    }


@router.get("/{resume_id}/job-recommendations", response_model=JobRecommendationResponse)
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
        raise HTTPException(status_code=404, detail="Resume not found")
        
    optimizer = ResumeOptimizer(db)
    try:
        result = optimizer.optimize_resume(
            resume_id=resume_id,
            user_id=current_user.id,
            optimization_type=request.optimization_type,
            job_description=request.job_description,
            job_id=request.job_id,
            save_as_new=request.save_as_new
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Optimization failed"))
            
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error during optimization: {str(e)}")


@router.post("/{resume_id}/process-pipeline")
async def process_resume_pipeline(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Run full resume processing pipeline (parse -> ats-score)."""
    manager = ResumeManager(db)
    resume = manager.get_resume(resume_id, current_user.id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
        
    # 1. Parse (if file exists)
    if resume.file_path:
        parsed_data = manager.parse_resume_file(resume_id, current_user.id)
    else:
        # If manually created, we already have some data
        parsed_data = json.loads(resume.parsed_data) if resume.parsed_data else {}
        
    # 2. ATS Score
    ats_result = manager.get_ats_score(resume_id, current_user.id, "")
    
    return {
        "success": True,
        "resume_id": resume_id,
        "parsed_data": parsed_data,
        "ats_result": ats_result
    }


@router.get("/{resume_id}/versions", response_model=List[ResumeVersionResponse])
async def get_resume_versions(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all versions of a resume."""
    manager = ResumeManager(db)
    versions = manager.get_resume_versions(resume_id, current_user.id)
    return versions


@router.get("/{resume_id}/preview")
async def preview_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Preview a resume."""
    manager = ResumeManager(db)
    resume = manager.get_resume(resume_id, current_user.id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if not resume.file_path:
        raise HTTPException(status_code=400, detail="Resume has no file associated")
    
    # Get the file using cloud_storage_service
    # If local, return FileResponse
    # If S3/GCS, we could either redirect to signed URL or stream it
    try:
        if hasattr(cloud_storage_service.provider, "_get_file_path"):
            full_path = cloud_storage_service.provider._get_file_path(resume.file_path)
            return FileResponse(full_path, media_type="application/pdf")
        else:
            # For cloud providers, generate signed URL and redirect
            signed_url = cloud_storage_service.get_file_url(resume.file_path)
            from fastapi.responses import RedirectResponse
            return RedirectResponse(signed_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accessing file: {str(e)}")
