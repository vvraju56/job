"""Celery app and scheduled tasks (ingestion, alerts, digest)."""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "makeable",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "ingest-jobs-hourly": {
            "task": "app.workers.tasks.ingest_jobs",
            "schedule": crontab(minute=15),
        },
        "send-alert-digest-daily": {
            "task": "app.workers.tasks.send_alert_digest",
            "schedule": crontab(hour=8, minute=0),
        },
    },
)


def _run_async(coro):  # pragma: no cover - convenience helper
    return asyncio.run(coro)


@celery_app.task(name="app.workers.tasks.ingest_jobs")
def ingest_jobs(sources: list[str] | None = None, limit: int = 50) -> dict[str, int]:
    from app.adapters.aggregator import run_ingestion
    from app.core.database import SessionLocal

    async def _run() -> dict[str, int]:
        async with SessionLocal() as db:
            return await run_ingestion(db, sources=sources, limit=limit)

    return asyncio.run(_run())


@celery_app.task(name="app.workers.tasks.send_alert_digest")
def send_alert_digest() -> int:
    import asyncio

    from sqlalchemy import select

    from app.core.database import SessionLocal
    from app.models.models import Alert, Notification

    async def _run() -> int:
        sent = 0
        async with SessionLocal() as db:
            alerts = (await db.execute(select(Alert).where(Alert.active.is_(True)))).scalars().all()
            for alert in alerts:
                db.add(
                    Notification(
                        user_id=alert.user_id,
                        title=f"New jobs for '{alert.query}'",
                        body=f"Your saved search '{alert.query}' has new opportunities.",
                        data={"alert_id": alert.id, "query": alert.query},
                    )
                )
                sent += 1
            await db.commit()
        return sent

    return asyncio.run(_run())


@celery_app.task(name="app.workers.tasks.push_alert")
def push_alert(alert_id: str, title: str, body: str) -> None:
    """Fan-out a push notification to all of a user's device tokens via FCM."""
    import asyncio

    from sqlalchemy import select

    from app.core.database import SessionLocal
    from app.models.models import Alert, DeviceToken, Notification

    async def _run() -> None:
        async with SessionLocal() as db:
            alert = (await db.execute(select(Alert).where(Alert.id == alert_id))).scalar_one_or_none()
            if alert is None:
                return
            tokens = (await db.execute(select(DeviceToken.token).where(DeviceToken.user_id == alert.user_id))).scalars().all()
            db.add(Notification(user_id=alert.user_id, title=title, body=body, data={"alert_id": alert.id}))
            await db.commit()
            # In production, call firebase_admin.messaging.send_each_for_multicast here.

    asyncio.run(_run())