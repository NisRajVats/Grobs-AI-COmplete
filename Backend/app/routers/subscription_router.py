from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.models.user import User
from app.services.subscription_service import SubscriptionService
from app.utils.dependencies import get_current_user
from app.schemas.subscription import SubscriptionPlan, SubscriptionInfo

router = APIRouter(prefix="/api/subscriptions", tags=["Subscriptions"])

@router.get("/plans", response_model=List[SubscriptionPlan])
async def get_plans(db: Session = Depends(get_db)):
    """Get all active subscription plans."""
    return SubscriptionService.get_active_plans(db)

@router.get("/my", response_model=SubscriptionInfo)
async def get_my_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current user's active subscription."""
    subscription, plan = SubscriptionService.get_user_subscription(db, current_user.id)
    
    if not subscription:
        return SubscriptionInfo(
            subscription=None,
            plan=None,
            features=[],
            is_active=False
        )
    
    features = plan.features.split(",") if plan and plan.features else []
    
    return SubscriptionInfo(
        subscription=subscription,
        plan=plan,
        features=features,
        is_active=True
    )

@router.post("/subscribe", response_model=dict)
async def subscribe_to_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Subscribe the current user to a plan via Stripe."""
    result = SubscriptionService.create_subscription(db, current_user, plan_id)
    return {
        "message": "Subscription created successfully",
        **result
    }
