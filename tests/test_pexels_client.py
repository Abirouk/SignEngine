import pytest
import httpx
from unittest.mock import AsyncMock
from signengine.api_clients.pexels_client import PexelsClient

MOCK_API_KEY = "MOCK_API_KEY"

# Test the fetch_videos method with a valid query.
@pytest.mark.asyncio
async def test_fetch_videos_success(mocker):
    client = PexelsClient(api_key=MOCK_API_KEY)
    # Mock response data
    mock_response_data = {
        "videos": [
            {"id": 1, "video_files": [{"link": "http://example.com/video1.mp4"}]},
            {"id": 2, "video_files": [{"link": "http://example.com/video2.mp4"}]},
        ]
    }
    # Mock the httpx.AsyncClient.get response
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value=mock_response_data)
    mock_response.raise_for_status = AsyncMock(return_value=None)  # Ensure it's properly awaited
    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    # Act: Fetch videos
    results = await client.fetch_videos(query="nature", per_page=3, page=1)

    # Assert: Verify the results
    assert len(results) == 2
    assert results[0]["url"] == "http://example.com/video1.mp4"
    assert results[1]["url"] == "http://example.com/video2.mp4"

@pytest.mark.asyncio
async def test_fetch_videos_invalid_api_key(mocker):
    client = PexelsClient(api_key="INVALID_KEY")
    
    # Mock the HTTP 401 Unauthorized error with properly awaited methods
    async def mock_get(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status_code = 401

            async def json(self):
                return {}

            async def raise_for_status(self):
                raise httpx.HTTPStatusError(
                    "401 Unauthorized",
                    request=httpx.Request("GET", "https://api.pexels.com/videos/search"),
                    response=httpx.Response(status_code=401),
                )
        
        return MockResponse()

    # Patch `httpx.AsyncClient.get` with the mock
    mocker.patch("httpx.AsyncClient.get", side_effect=mock_get)

    # Act: Call fetch_videos
    results = await client.fetch_videos(query="nature", per_page=3, page=1)

    # Assert: Ensure the client gracefully handles the 401 and returns an empty list
    assert results == []

# Test the fetch_videos method when a network error occurs.
@pytest.mark.asyncio
async def test_fetch_videos_network_error(mocker):
    client = PexelsClient(api_key=MOCK_API_KEY)
    # Mock a network error
    mocker.patch("httpx.AsyncClient.get", side_effect=httpx.RequestError("Network error"))

    # Act: Fetch videos
    results = await client.fetch_videos(query="nature", per_page=3, page=1)

    # Assert: Ensure the results are empty
    assert results == []

# Test the fetch_videos method when an unexpected error occurs.
@pytest.mark.asyncio
async def test_fetch_videos_unexpected_error(mocker):
    client = PexelsClient(api_key=MOCK_API_KEY)
    # Mock an unexpected error
    mocker.patch("httpx.AsyncClient.get", side_effect=Exception("Unexpected error"))

    # Act: Fetch videos
    results = await client.fetch_videos(query="nature", per_page=3, page=1)

    # Assert: Ensure the results are empty
    assert results == []