"""Notifications and job alerts."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbDep
from app.models.models import Alert, DeviceToken, Notification
from app.schemas.schemas import (
    AlertCreate,
    AlertOut,
    AlertsOut,
    DeviceTokenCreate,
    NotificationOut,
    NotificationsOut,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=NotificationsOut)
async def list_notifications(
    db: DbDep,
    user: CurrentUser,
    unread_only: bool = False,
    limit: int = Query(50, ge=1, le=200),
) -> dict:
    stmt = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        stmt = stmt.where(Notification.read.is_(False))
    result = await db.execute(stmt.order_by(Notification.created_at.desc()).limit(limit))
    return {"notifications": list(result.scalars().all())}


@router.post("/{notification_id}/read", response_model=NotificationOut)
async def mark_read(db: DbDep, user: CurrentUser, notification_id: str) -> Notification:
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id, Notification.user_id == user.id)
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    notification.read = True
    await db.commit()
    await db.refresh(notification)
    return notification


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(db: DbDep, user: CurrentUser) -> None:
    result = await db.execute(select(Notification).where(Notification.user_id == user.id, Notification.read.is_(False)))
    for notification in result.scalars().all():
        notification.read = True
    await db.commit()


@router.post("/alerts", response_model=AlertOut, status_code=status.HTTP_201_CREATED)
async def create_alert(db: DbDep, user: CurrentUser, payload: AlertCreate) -> Alert:
    alert = Alert(user_id=user.id, **payload.model_dump())
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.get("/alerts", response_model=AlertsOut)
async def list_alerts(db: DbDep, user: CurrentUser) -> dict:
    result = await db.execute(select(Alert).where(Alert.user_id == user.id).order_by(Alert.created_at.desc()))
    return {"alerts": list(result.scalars().all())}


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(db: DbDep, user: CurrentUser, alert_id: str) -> None:
    result = await db.execute(select(Alert).where(Alert.id == alert_id, Alert.user_id == user.id))
    alert = result.scalar_one_or_none()
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    await db.delete(alert)
    await db.commit()


@router.post("/device-token", status_code=status.HTTP_201_CREATED)
async def register_device(db: DbDep, user: CurrentUser, payload: DeviceTokenCreate) -> dict:
    db.add(DeviceToken(user_id=user.id, token=payload.token, platform=payload.platform))
    await db.commit()
    return {"registered": True}