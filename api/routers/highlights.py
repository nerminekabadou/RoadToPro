# Endpoints for highlights
from fastapi import APIRouter

router = APIRouter()

@router.get("/highlights")
async def get_highlights():
    return []
