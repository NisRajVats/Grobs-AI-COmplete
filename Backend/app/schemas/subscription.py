from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SubscriptionPlanBase(BaseModel):
    name: str
    description: str
    price: int
    duration_days: int
    features: str

class SubscriptionPlanCreate(SubscriptionPlanBase):
    pass

class SubscriptionPlan(SubscriptionPlanBase):
    id: int
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class UserSubscriptionBase(BaseModel):
    user_id: int
    plan_id: int
    start_date: str
    end_date: str
    status: str

class UserSubscriptionCreate(UserSubscriptionBase):
    pass

class UserSubscription(UserSubscriptionBase):
    id: int
    stripe_subscription_id: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True

class SubscriptionInfo(BaseModel):
    subscription: Optional[UserSubscription] = None
    plan: Optional[SubscriptionPlan] = None
    features: List[str] = []
    is_active: bool = False
