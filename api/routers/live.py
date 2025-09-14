# Endpoints for live data
from fastapi import APIRouter

router = APIRouter()

@router.get("/live")
async def get_live_data():
    return {}
