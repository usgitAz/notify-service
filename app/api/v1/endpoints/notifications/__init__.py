"""
Notifications endpoints package.

Combines common (cross-channel) and channel-specific routes.
"""

from fastapi import APIRouter

from app.api.v1.endpoints.notifications import common, email

router = APIRouter(prefix="/notifications")

# Common: GET /notifications, GET /notifications/{id}
router.include_router(common.router)

# Email-specific: POST /notifications/email
router.include_router(email.router)
