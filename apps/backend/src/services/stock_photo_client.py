"""Stock photo API client — Unsplash integration.

Aligned with PRD V3.1 §AssetPool / TASK_V2.7.1.
"""

import os
from typing import Dict, List

import httpx

from src.core.config import settings


class StockPhotoClient:
    """Client for stock photo APIs. MVP: Unsplash only."""

    def __init__(self):
        self.unsplash_key = settings.UNSPLASH_API_KEY
        self.unsplash_url = settings.UNSPLASH_API_URL

    async def search_unsplash(
        self,
        query: str,
        per_page: int = 20,
        page: int = 1,
    ) -> List[Dict]:
        """Search Unsplash for photos. Returns preview results."""
        if not self.unsplash_key:
            return []

        url = f"{self.unsplash_url}/search/photos"
        headers = {"Authorization": f"Client-ID {self.unsplash_key}"}
        params = {"query": query, "per_page": per_page, "page": page}

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()

        results = []
        for photo in data.get("results", []):
            results.append({
                "stock_source": "unsplash",
                "stock_id": photo.get("id"),
                "preview_url": photo.get("urls", {}).get("small"),
                "download_url": photo.get("urls", {}).get("regular"),
                "thumb_url": photo.get("urls", {}).get("thumb"),
                "description": photo.get("description") or photo.get("alt_description") or "",
                "author_name": photo.get("user", {}).get("name", ""),
                "author_username": photo.get("user", {}).get("username", ""),
                "author_link": photo.get("user", {}).get("links", {}).get("html", ""),
                "width": photo.get("width"),
                "height": photo.get("height"),
            })
        return results

    async def download_image(
        self,
        download_url: str,
        dest_path: str,
    ) -> bool:
        """Download an image from Unsplash to local storage."""
        if not self.unsplash_key:
            return False

        # Unsplash requires triggering download endpoint for attribution tracking
        # For MVP, we download directly from the provided URL
        async with httpx.AsyncClient(timeout=60) as client:
            headers = {"Authorization": f"Client-ID {self.unsplash_key}"}
            resp = await client.get(download_url, headers=headers, follow_redirects=True)
            if resp.status_code == 200:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(dest_path, "wb") as f:
                    f.write(resp.content)
                return True
        return False

    def get_attribution(self, photo: Dict) -> Dict:
        """Generate attribution metadata for a stock photo."""
        return {
            "source": photo.get("stock_source", "unsplash"),
            "photographer": photo.get("author_name", ""),
            "photographer_url": f"https://unsplash.com/@{photo.get('author_username', '')}",
            "photo_url": f"https://unsplash.com/photos/{photo.get('stock_id', '')}",
            "license": "Unsplash License (free for commercial and non-commercial use)",
        }


# Global client instance
stock_client = StockPhotoClient()
