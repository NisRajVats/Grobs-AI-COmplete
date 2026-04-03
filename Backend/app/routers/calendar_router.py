from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database.session import get_db
from app.models import User, CalendarEvent
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/api/calendar", tags=["Calendar"])

class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    date: str
    time: str
    platform: str = "Google Meet"
    type: str = "interview"
    status: str = "scheduled"

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    platform: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None

class EventResponse(EventBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.get("/events", response_model=List[EventResponse])
async def get_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(CalendarEvent).filter(CalendarEvent.user_id == current_user.id).all()

@router.post("/events", response_model=EventResponse)
async def create_event(
    event: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_event = CalendarEvent(
        **event.model_dump(),
        user_id=current_user.id
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.put("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_update: EventUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_event = db.query(CalendarEvent).filter(
        CalendarEvent.id == event_id,
        CalendarEvent.user_id == current_user.id
    ).first()
    
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    update_data = event_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_event, key, value)
    
    db.commit()
    db.refresh(db_event)
    return db_event

@router.delete("/events/{event_id}")
async def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_event = db.query(CalendarEvent).filter(
        CalendarEvent.id == event_id,
        CalendarEvent.user_id == current_user.id
    ).first()
    
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    db.delete(db_event)
    db.commit()
    return {"message": "Event deleted successfully"}
