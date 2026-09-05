"""GeoKZ desktop client package.

The desktop layer talks to GeoKZ exclusively through the HTTP API. It must not import
SQLAlchemy models or bypass backend-owned review/provenance rules.
"""

from app.desktop.api_client import GeoKZApiClient, GeoKZApiError

__all__ = ["GeoKZApiClient", "GeoKZApiError"]
