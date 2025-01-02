import httpx
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("APIClient")

# Constants
API_URL = "http://127.0.0.1:8000/playlist"  # To update with the actual endpoint later

# Returns a list of playlist items, where each item is a dictionary with 'title' and 'url' keys.
async def fetch_playlist() -> List[Dict[str, str]]:
    logger.info("Fetching playlist from API...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(API_URL)
            response.raise_for_status()  #Http errors are raised here
            playlist = response.json()
            
            if not isinstance(playlist, list):
                logger.error("Unexpected response format: Expected a list.")
                return []
            
            logger.info(f"Playlist fetched successfully: {len(playlist)} items.")
            return playlist
    except httpx.HTTPStatusError as http_error:
        logger.error(f"HTTP error while fetching playlist: {http_error}")
    except httpx.RequestError as req_error:
        logger.error(f"Network error while fetching playlist: {req_error}")
    except Exception as unexpected_error:
        logger.error(f"Unexpected error occurred: {unexpected_error}")
    return []
