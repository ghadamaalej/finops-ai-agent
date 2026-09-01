"""Backward-compatible import for the canonical resource-based cost service."""

from app.services.cost_service import CostService

__all__ = ["CostService"]
