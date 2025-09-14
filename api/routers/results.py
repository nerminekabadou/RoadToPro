# Endpoints for results
from fastapi import APIRouter

router = APIRouter()


@router.get("/results")
async def get_results():
    return []
