"""Resume AI tools and alert tests (heuristic fallback engine)."""
from httpx import AsyncClient

RESUME = (
    "Software Engineer with 5 years of experience. Built scalable products using "
    "TypeScript, React, Python and PostgreSQL. Optimized query performance by 40%. "
    "Developed CI/CD pipelines with Docker and Kubernetes. Shipped features with "
    "Redis and AWS. Managed a team of 4 engineers. Improved API latency by 25%."
)


async def test_analyze_resume(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    resp = await client.post(
        "/api/v1/resume/analyze",
        json={"resume_text": RESUME, "target_role": "developer"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert 20 <= data["ats_score"] <= 99
    assert isinstance(data["missing_keywords"], list)
    assert isinstance(data["suggestions"], list)
    assert data["summary"]


async def test_analyze_resume_too_short(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    resp = await client.post(
        "/api/v1/resume/analyze",
        json={"resume_text": "too short"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_cover_letter(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    resp = await client.post(
        "/api/v1/resume/cover-letter",
        json={
            "resume_text": RESUME,
            "job_title": "Senior Flutter Developer",
            "company_name": "Nova Labs",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    letter = resp.json()["cover_letter"]
    assert "Nova Labs" in letter
    assert "Senior Flutter Developer" in letter


async def test_skill_gap(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    resp = await client.post(
        "/api/v1/resume/skill-gap",
        json={"resume_text": RESUME, "target_role": "Flutter Developer"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["current_skills"], list)
    assert isinstance(data["missing_skills"], list)
    assert isinstance(data["recommended_learning"], list)


async def test_interview_prep(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    resp = await client.post(
        "/api/v1/resume/interview-prep",
        json={
            "job_title": "Flutter Developer",
            "job_description": "Build cross-platform apps with system design focus.",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    questions = resp.json()["questions"]
    assert len(questions) >= 3


async def test_resume_history(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    await client.post(
        "/api/v1/resume/analyze",
        json={"resume_text": RESUME},
        headers=auth_headers,
    )
    history = await client.get("/api/v1/resume/history", headers=auth_headers)
    assert history.status_code == 200
    assert len(history.json()) >= 1


async def test_alert_crud(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await client.post(
        "/api/v1/notifications/alerts",
        json={"query": "Flutter Developer", "frequency": "daily"},
        headers=auth_headers,
    )
    assert created.status_code == 201
    alert_id = created.json()["id"]

    alerts = await client.get("/api/v1/notifications/alerts", headers=auth_headers)
    assert any(a["id"] == alert_id for a in alerts.json()["alerts"])

    deleted = await client.delete(f"/api/v1/notifications/alerts/{alert_id}", headers=auth_headers)
    assert deleted.status_code == 204

    alerts = await client.get("/api/v1/notifications/alerts", headers=auth_headers)
    assert not any(a["id"] == alert_id for a in alerts.json()["alerts"])


async def test_register_device_token(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    resp = await client.post(
        "/api/v1/notifications/device-token",
        json={"token": "fcm-token-123", "platform": "android"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["registered"] is True