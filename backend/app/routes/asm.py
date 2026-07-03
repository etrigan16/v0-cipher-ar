from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter(prefix="/asm", tags=["asm"])


class AssetResponse(BaseModel):
    id: str
    domain: str
    status: str
    findings_count: int


@router.get("/assets")
async def list_assets(db: AsyncSession = Depends(get_db)):
    return {"assets": []}


@router.post("/scan/{asset_id}")
async def trigger_scan(asset_id: str, db: AsyncSession = Depends(get_db)):
    return {"scan_id": "placeholder", "status": "queued"}


@router.get("/results/{scan_id}")
async def get_results(scan_id: str, db: AsyncSession = Depends(get_db)):
    return {"findings": []}
