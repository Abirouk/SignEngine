import os
import logging
import httpx
from typing import List, Dict, AsyncGenerator, Callable

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Utils")

# Check if a remote URL is accessible. True if it is.
async def check_remote_url(url: str) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.head(url, timeout=5, follow_redirects=True)
            return response.status_code == 200
    except httpx.RequestError as e:
        logger.warning(f"Failed to check remote URL '{url}': {e}")
        return False

# Validate a single playlist item. True if the item is valid (file exists or URL is accessible).
async def validate_item(item: Dict[str, str]) -> bool:
    url = item.get("url", "")
    if not url:
        logger.warning(f"Item missing URL: {item}")
        return False

    if url.startswith(("http://", "https://")):
        return await check_remote_url(url)
    return os.path.exists(url)

# Validate all items in the playlist asynchronously.
async def validate_playlist(playlist: List[Dict[str, str]]) -> List[Dict[str, str]]:
    logger.info("Validating playlist...")
    valid_items = []

    for item in playlist:
        if "title" in item and "url" in item and await validate_item(item):
            valid_items.append(item)

    logger.info(f"Validation complete. {len(valid_items)} valid items found.")
    return valid_items

# Summarize and log validation results.
def summarize_validation_results(playlist: List[Dict[str, str]], validated: List[Dict[str, str]]) -> None:
    failed_items = [item for item in playlist if item not in validated]
    logger.info(f"Validation Summary: {len(validated)} passed, {len(failed_items)} failed.")

    if failed_items:
        logger.warning("Failed Items:")
        for item in failed_items:
            logger.warning(f"Title: {item.get('title', 'Untitled')}, URL: {item.get('url')}")