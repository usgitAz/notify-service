"""
API v1 router — aggregates all v1 endpoint modules.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import users

api_router = APIRouter()
api_router.include_router(users.router)
