"""
Analytics router - Real user analytics endpoints.
Replaces mock data in AnalyticsDashboard.jsx with real backend data.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.database.session import get_db
from app.models import User, Resume, JobApplication, InterviewSession
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/user")
async def get_user_analytics(
    time_range: str = Query("30d", description="Time range: 7d, 30d, 90d, 1y"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get real user analytics data to replace mock data in AnalyticsDashboard.
    """
    # Calculate date range
    now = datetime.now()
    range_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    days = range_map.get(time_range, 30)
    start_date = now - timedelta(days=days)
    start_str = start_date.isoformat()

    # --- Key Metrics ---
    all_applications = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id
    ).all()

    total_applications = len(all_applications)
    interview_count = sum(1 for a in all_applications if a.status in ("interview", "offer"))
    offer_count = sum(1 for a in all_applications if a.status == "offer")

    interview_rate = round((interview_count / total_applications * 100) if total_applications > 0 else 0, 1)
    offer_rate = round((offer_count / total_applications * 100) if total_applications > 0 else 0, 1)

    # Average resume score
    resumes = db.query(Resume).filter(
        Resume.user_id == current_user.id,
        Resume.ats_score.isnot(None)
    ).all()
    avg_resume_score = round(sum(r.ats_score for r in resumes) / len(resumes), 1) if resumes else 0

    # --- Application Trend (monthly breakdown) ---
    months = []
    for i in range(min(6, days // 30 + 1)):
        month_start = now - timedelta(days=30 * (5 - i))
        month_end = now - timedelta(days=30 * (4 - i))
        month_name = month_start.strftime("%b")

        month_apps = [
            a for a in all_applications
            if a.created_at and month_start.isoformat() <= a.created_at <= month_end.isoformat()
        ]
        month_interviews = sum(1 for a in month_apps if a.status in ("interview", "offer"))
        month_offers = sum(1 for a in month_apps if a.status == "offer")

        months.append({
            "name": month_name,
            "applications": len(month_apps),
            "interviews": month_interviews,
            "offers": month_offers
        })

    # --- Resume Performance (monthly ATS scores) ---
    resume_performance = []
    for i in range(min(6, days // 30 + 1)):
        month_start = now - timedelta(days=30 * (5 - i))
        month_end = now - timedelta(days=30 * (4 - i))
        month_name = month_start.strftime("%b")

        month_resumes = [
            r for r in resumes
            if r.created_at and month_start.isoformat() <= r.created_at <= month_end.isoformat()
        ]
        avg_score = round(sum(r.ats_score for r in month_resumes) / len(month_resumes), 1) if month_resumes else 0

        month_apps = [
            a for a in all_applications
            if a.created_at and month_start.isoformat() <= a.created_at <= month_end.isoformat()
        ]

        resume_performance.append({
            "name": month_name,
            "score": avg_score,
            "applications": len(month_apps)
        })

    # --- Application Status Breakdown ---
    status_counts = {}
    for app in all_applications:
        s = app.status or "applied"
        status_counts[s] = status_counts.get(s, 0) + 1

    color_map = {
        "applied": "#3b82f6",
        "interview": "#f59e0b",
        "offer": "#10b981",
        "rejected": "#ef4444",
        "saved": "#8b5cf6"
    }
    application_status = [
        {"name": k.capitalize(), "value": v, "color": color_map.get(k, "#64748b")}
        for k, v in status_counts.items()
    ]

    # --- Skill Gap Analysis from resume skills ---
    skill_counts = {}
    for r in resumes:
        for skill in r.skills:
            name = skill.name
            skill_counts[name] = skill_counts.get(name, 0) + 1

    # Top skills with presence percentage
    total_resumes = len(resumes) if resumes else 1
    skill_gap_analysis = [
        {"skill": name, "gap": round((count / total_resumes) * 100), "color": "#3b82f6"}
        for name, count in sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    ]
    if not skill_gap_analysis:
        skill_gap_analysis = [
            {"skill": "Add Skills", "gap": 0, "color": "#64748b"}
        ]

    # --- Recent Activity ---
    recent_apps = sorted(all_applications, key=lambda a: a.created_at or "", reverse=True)[:5]
    recent_activity = []
    for app in recent_apps:
        try:
            dt = datetime.fromisoformat(app.created_at)
            diff = now - dt
            if diff.days > 0:
                time_str = f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
            elif diff.seconds // 3600 > 0:
                h = diff.seconds // 3600
                time_str = f"{h} hour{'s' if h > 1 else ''} ago"
            else:
                time_str = "Just now"
        except Exception:
            time_str = "Recently"

        recent_activity.append({
            "id": app.id,
            "type": "application",
            "title": f"Applied to {app.job_title} at {app.company}",
            "time": time_str,
            "status": "success" if app.status == "offer" else ("warning" if app.status == "interview" else "info")
        })

    # Interview sessions
    interview_sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id
    ).order_by(InterviewSession.created_at.desc()).limit(3).all()

    for session in interview_sessions:
        try:
            dt = datetime.fromisoformat(session.created_at)
            diff = now - dt
            time_str = f"{diff.days} days ago" if diff.days > 0 else "Today"
        except Exception:
            time_str = "Recently"

        recent_activity.append({
            "id": f"interview_{session.id}",
            "type": "interview",
            "title": f"Mock Interview - {session.job_role or 'General'}",
            "time": time_str,
            "status": "success" if session.status == "completed" else "info"
        })

    # --- AI Insights ---
    insights = []
    if avg_resume_score < 70:
        insights.append({
            "type": "warning",
            "message": f"Your average resume score is {avg_resume_score}%. Optimize your resume to improve match rates.",
            "action": "Optimize Resume"
        })
    elif avg_resume_score >= 85:
        insights.append({
            "type": "success",
            "message": f"Excellent resume score of {avg_resume_score}%! You're well positioned for top roles.",
            "action": "View Resume"
        })

    if total_applications == 0:
        insights.append({
            "type": "info",
            "message": "Start applying to jobs to track your application progress here.",
            "action": "Find Jobs"
        })
    elif interview_rate < 10 and total_applications >= 5:
        insights.append({
            "type": "tip",
            "message": f"Your interview rate is {interview_rate}%. Try tailoring your resume for each job application.",
            "action": "Optimize Resume"
        })

    return {
        "keyMetrics": {
            "totalApplications": total_applications,
            "avgResumeScore": avg_resume_score,
            "interviewRate": interview_rate,
            "offerRate": offer_rate,
            "applicationTrend": months,
            "resumePerformance": resume_performance,
            "applicationStatus": application_status if application_status else [
                {"name": "No Data", "value": 1, "color": "#64748b"}
            ],
            "skillGapAnalysis": skill_gap_analysis,
            "recentActivity": recent_activity[:8],
            "aiInsights": insights
        },
        "timeRange": time_range,
        "generatedAt": now.isoformat()
    }
