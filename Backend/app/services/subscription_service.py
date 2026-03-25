from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import stripe
from app.core.config import settings
from app.models.user import User, SubscriptionPlan, UserSubscription
from fastapi import HTTPException, status

stripe.api_key = settings.STRIPE_SECRET_KEY

class SubscriptionService:
    @staticmethod
    def get_active_plans(db: Session):
        return db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True).all()

    @staticmethod
    def get_user_subscription(db: Session, user_id: int):
        subscription = db.query(UserSubscription).filter(
            UserSubscription.user_id == user_id,
            UserSubscription.status == "active"
        ).first()
        
        if not subscription:
            return None, None
        
        plan = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == subscription.plan_id
        ).first()
        
        return subscription, plan

    @staticmethod
    def create_subscription(db: Session, user: User, plan_id: int):
        plan = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == plan_id,
            SubscriptionPlan.is_active == True
        ).first()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Check if user already has active subscription
        existing = db.query(UserSubscription).filter(
            UserSubscription.user_id == user.id,
            UserSubscription.status == "active"
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="User already has active subscription")
        
        try:
            # Check if user has stripe_customer_id, create if not
            if not user.stripe_customer_id:
                customer = stripe.Customer.create(email=user.email)
                user.stripe_customer_id = customer.id
                db.add(user)
                db.commit()

            stripe_subscription = stripe.Subscription.create(
                customer=user.stripe_customer_id,
                items=[{"price": plan.stripe_price_id}],
                expand=["latest_invoice.payment_intent"]
            )
            
            # Create database subscription
            end_date = datetime.now() + timedelta(days=plan.duration_days)
            subscription = UserSubscription(
                user_id=user.id,
                plan_id=plan.id,
                start_date=datetime.now().isoformat(),
                end_date=end_date.isoformat(),
                status="active",
                stripe_subscription_id=stripe_subscription.id
            )
            
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
            
            return {
                "subscription": subscription,
                "client_secret": stripe_subscription.latest_invoice.payment_intent.client_secret
            }
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")
