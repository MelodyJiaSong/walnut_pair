# app__webapi/routes.py
"""Route constants for WebAPI endpoints."""
from typing import Final

# Base API prefix
API_V1_PREFIX: Final[str] = "/api/v1"

# Walnut pairs routes
WALNUT_PAIRS_BASE: Final[str] = f"{API_V1_PREFIX}/walnut-pairs"
WALNUT_PAIRS_LIST: Final[str] = "/"
WALNUT_PAIRS_BY_WALNUT: Final[str] = "/walnut/{{walnut_id}}"
WALNUT_PAIRS_SPECIFIC: Final[str] = "/walnut/{{walnut_id}}/compared/{{compared_walnut_id}}"

