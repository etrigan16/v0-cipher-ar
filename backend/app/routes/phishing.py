from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db

router = APIRouter(prefix="/phishing", tags=["phishing"])


class CampaignCreate(BaseModel):
    name: str
    template_id: str
    target_emails: list[str]
    scheduled_at: Optional[str] = None


@router.get("/campaigns")
async def list_campaigns(db: AsyncSession = Depends(get_db)):
    return {"campaigns": []}


@router.post("/campaigns")
async def create_campaign(req: CampaignCreate, db: AsyncSession = Depends(get_db)):
    return {"id": "placeholder", "status": "created"}


@router.get("/campaigns/{campaign_id}/results")
async def get_campaign_results(campaign_id: str, db: AsyncSession = Depends(get_db)):
    return {
        "campaign_id": campaign_id,
        "total_sent": 0,
        "total_clicked": 0,
        "total_reported": 0,
    }
