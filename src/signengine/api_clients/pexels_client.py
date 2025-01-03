import httpx
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("PexelsClient")

class PexelsClient:
    BASE_URL = "https://api.pexels.com/videos/search"

    def __init__(self, api_key: str):
        self.api_key = api_key  # Use instance-level API key

    async def fetch_videos(self, query: str, per_page: int = 10, page: int = 1) -> List[Dict[str, str]]:
        """Fetch videos from Pexels API."""
        headers = {"Authorization": self.api_key}
        params = {"query": query, "per_page": per_page, "page": page}

        logger.info(f"Fetching videos from Pexels with query '{query}'...")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.BASE_URL, headers=headers, params=params)
                await response.raise_for_status()

                data = await response.json()
                videos = []

                for video in data.get("videos", []):
                    videos.append({
                        "title": video.get("id", "Untitled"),
                        "url": video.get("video_files", [{}])[0].get("link", ""),
                    })

                logger.info(f"Successfully fetched {len(videos)} videos.")
                return videos

        except httpx.HTTPStatusError as http_error:
            logger.error(f"HTTP error while fetching videos: {http_error}")
        except httpx.RequestError as req_error:
            logger.error(f"Network error while fetching videos: {req_error}")
        except Exception as unexpected_error:
            logger.error(f"Unexpected error occurred: {unexpected_error}")

        return []