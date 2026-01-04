# app__webapi/controllers/walnut_pairs__controller.py
"""Walnut pair API controller."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from application_layer.dtos.walnut_comparison__dto import WalnutComparisonDTO
from application_layer.queries.walnut_comparison__query import IWalnutComparisonQuery
from app__webapi.dependencies import get_walnut_comparison_query
from app__webapi.routes import (
    WALNUT_PAIRS_BASE,
    WALNUT_PAIRS_BY_WALNUT,
    WALNUT_PAIRS_LIST,
    WALNUT_PAIRS_SPECIFIC,
)

router = APIRouter(tags=["walnut-pairs"])


@router.get(
    WALNUT_PAIRS_LIST,
    response_model=List[WalnutComparisonDTO],
    summary="Get all walnut pairs",
    description="Returns a list of all walnut pair results, ordered by similarity score (highest first).",
)
async def get_all_pairs_async(
    query: IWalnutComparisonQuery = Depends(get_walnut_comparison_query),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Maximum number of results to return"),
    offset: Optional[int] = Query(0, ge=0, description="Number of results to skip"),
) -> List[WalnutComparisonDTO]:
    """
    Get all walnut pair results.
    
    Returns all pair results sorted by final similarity score (highest first).
    Supports pagination with limit and offset parameters.
    """
    pairs = await query.get_all_pairs_async()
    
    # Apply pagination if specified
    if offset is not None:
        pairs = pairs[offset:]
    if limit is not None:
        pairs = pairs[:limit]
    
    return pairs


@router.get(
    WALNUT_PAIRS_BY_WALNUT,
    response_model=List[WalnutComparisonDTO],
    summary="Get pairs for a specific walnut",
    description="Returns all pair results for a specific walnut, ordered by similarity score.",
)
async def get_pairs_by_walnut_id_async(
    walnut_id: str,
    query: IWalnutComparisonQuery = Depends(get_walnut_comparison_query),
) -> List[WalnutComparisonDTO]:
    """
    Get all pair results for a specific walnut.
    
    Returns all comparisons where the specified walnut is either the primary
    or compared walnut, sorted by final similarity score (highest first).
    """
    return await query.get_pairs_by_walnut_id_async(walnut_id)


@router.get(
    WALNUT_PAIRS_SPECIFIC,
    response_model=WalnutComparisonDTO,
    summary="Get specific pair",
    description="Returns the pair result between two specific walnuts.",
)
async def get_pair_async(
    walnut_id: str,
    compared_walnut_id: str,
    query: IWalnutComparisonQuery = Depends(get_walnut_comparison_query),
) -> WalnutComparisonDTO:
    """
    Get a specific pair between two walnuts.
    
    Returns the comparison result between the two specified walnuts.
    """
    pair = await query.get_pair_async(walnut_id, compared_walnut_id)
    if pair is None:
        raise HTTPException(
            status_code=404,
            detail=f"Pair not found between walnut {walnut_id} and {compared_walnut_id}",
        )
    return pair

