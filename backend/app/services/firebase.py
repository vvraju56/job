"""Firebase Admin bootstrap.

Initializes the Firebase Admin SDK once from the service-account JSON provided
either as a file path (`FIREBASE_CREDENTIALS`) or as an inline JSON string
(`FIREBASE_CREDENTIALS_JSON`, e.g. on Render/Vercel where file uploads are not
available). Used to verify Google ID tokens for social login and to send FCM
push notifications. If Firebase is not configured, functions degrade gracefully
(social login falls back to email/password).
"""
from __future__ import annotations

import json
import os

from app.core.config import settings

_app = None


def get_firebase_app():
    """Return the initialized Firebase Admin app, or None if not configured."""
    global _app
    if _app is not None:
        return _app

    import firebase_admin
    from firebase_admin import credentials

    cred = None
    if settings.FIREBASE_CREDENTIALS_JSON:
        cred_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
        cred = credentials.Certificate(cred_dict)
    elif settings.FIREBASE_CREDENTIALS and os.path.exists(settings.FIREBASE_CREDENTIALS):
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)

    if cred is None:
        return None

    _app = firebase_admin.initialize_app(
        cred, {"projectId": settings.FIREBASE_PROJECT_ID or None}
    )
    return _app


def verify_google_id_token(id_token: str) -> dict | None:
    """Verify a Firebase-issued Google ID token and return its claims."""
    app = get_firebase_app()
    if app is None:
        return None
    from firebase_admin import auth

    try:
        decoded = auth.verify_id_token(id_token, app=app)
        return decoded
    except Exception:  # noqa: BLE001  (invalid/expired tokens)
        return None