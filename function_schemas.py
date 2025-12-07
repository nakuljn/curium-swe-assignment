from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class RecallClassification(str, Enum):
    CLASS_I = "Class I"
    CLASS_II = "Class II"
    CLASS_III = "Class III"


class RecallRecord(BaseModel):
    id: str = Field(..., alias="recall_number")
    reason: str = Field(..., alias="reason_for_recall")
    status: str
    classification: RecallClassification
    product_description: str
    firm_name: str = Field(..., alias="recalling_firm")
    recall_initiation_date: str
    state: Optional[str] = None

    class Config:
        populate_by_name = True


class SearchRecallsInput(BaseModel):
    query: Optional[str] = Field(None, description="Search term for product name or recall reason")
    classification: Optional[RecallClassification] = Field(None, description="Filter by hazard class")
    year: Optional[int] = Field(None, description="Filter by year of recall (e.g. 2020)")
    limit: int = Field(10, ge=1, le=50)


class GetRecallStatsInput(BaseModel):
    pass
