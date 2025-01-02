import pytest
import httpx
from signengine.api_client import fetch_playlist

# Reusable mock response class
class MockResponse:
    """Simulates an HTTP response for testing purposes."""

    def __init__(self, json_data=None, status_code=200, raise_for_status=False):
        self._json_data = json_data or []
        self.status_code = status_code
        self.raise_for_status_flag = raise_for_status

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.raise_for_status_flag:
            raise httpx.HTTPStatusError("HTTP Error", request=None, response=None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mock_data,expected_length",
    [
        ([{"title": "Video 1", "url": "http://example.com/video1.mp4"}], 1),
        ([], 0),
    ],
)
async def test_fetch_playlist_success(mocker, mock_data, expected_length):
    """Test successful playlist fetch with valid and empty responses."""
    # Arrange
    mocker.patch("httpx.AsyncClient.get", return_value=MockResponse(json_data=mock_data))

    # Act
    playlist = await fetch_playlist()

    # Assert
    assert len(playlist) == expected_length
    assert playlist == mock_data


@pytest.mark.asyncio
async def test_fetch_playlist_http_error(mocker):
    """Test that fetch_playlist handles HTTP errors gracefully."""
    # Arrange
    mocker.patch(
        "httpx.AsyncClient.get",
        return_value=MockResponse(status_code=500, raise_for_status=True),
    )

    # Act
    playlist = await fetch_playlist()

    # Assert
    assert playlist == []


@pytest.mark.asyncio
async def test_fetch_playlist_timeout(mocker):
    """Test fetch_playlist handles request timeouts."""
    # Arrange
    mocker.patch("httpx.AsyncClient.get", side_effect=httpx.RequestError("Timeout"))

    # Act
    playlist = await fetch_playlist()

    # Assert
    assert playlist == []
