"""Schemas for the health-check endpoint."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response payload for `GET /api/health`."""

    status: str = Field(..., examples=["ok"])
    app_name: str = Field(..., examples=["Citeflow"])
    version: str = Field(..., examples=["0.1.0"])
