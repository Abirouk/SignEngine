import pytest
from signengine.utils import validate_playlist


@pytest.fixture
def mock_playlist():
    return [
        {"title": "Valid Local Video", "url": "/path/to/local.mp4"},
        {"title": "Invalid URL", "url": "http://example.com/video.missing"},
        {"title": "Missing Title", "url": "/path/to/untitled.mp4"},
        {"title": "Valid Remote Video", "url": "http://example.com/video.mp4"},
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mock_exists,mock_urls,expected_count",
    [
        ([True, False, True], [True, False], 2),  # Valid local and valid remote
        ([False, False, False], [False, False], 0),  # No valid entries
    ],
)
async def test_validate_playlist(mocker, mock_playlist, mock_exists, mock_urls, expected_count):
    """Test validate_playlist handles mixed valid/invalid local files and URLs."""
    # Arrange
    mocker.patch("os.path.exists", side_effect=mock_exists)  # Mock local file existence
    mocker.patch("signengine.utils.check_remote_url", side_effect=mock_urls)  # Mock remote URL checks

    # Act
    validated = await validate_playlist(mock_playlist)

    # Assert
    assert len(validated) == expected_count


@pytest.mark.asyncio
async def test_validate_playlist_with_empty_playlist():
    """Test validate_playlist with an empty playlist."""
    # Act
    validated = await validate_playlist([])

    # Assert
    assert validated == []


@pytest.mark.asyncio
async def test_validate_playlist_with_partial_data(mocker):
    """Test validate_playlist with incomplete playlist items."""
    # Arrange
    incomplete_playlist = [
        {"title": "Video with No URL"},  # Missing 'url'
        {"url": "/path/to/video.mp4"},  # Missing 'title'
    ]
    mocker.patch("os.path.exists", return_value=True)  # Mock all paths as valid

    # Act
    validated = await validate_playlist(incomplete_playlist)

    # Assert
    assert validated == []  # Both items should be filtered out


@pytest.mark.asyncio
async def test_validate_playlist_with_all_invalid_entries(mocker):
    """Test validate_playlist where all entries are invalid."""
    # Arrange
    invalid_playlist = [
        {"title": "Invalid Video", "url": "/invalid/path.mp4"},
        {"title": "Another Invalid", "url": "http://invalid-url.com"},
    ]
    mocker.patch("os.path.exists", return_value=False)  # Mock all paths as invalid
    mocker.patch("signengine.utils.check_remote_url", return_value=False)  # Mock remote URLs as invalid

    # Act
    validated = await validate_playlist(invalid_playlist)

    # Assert
    assert validated == []


@pytest.mark.asyncio
async def test_validate_playlist_with_mixed_entries(mocker):
    """Test validate_playlist with a mix of valid and invalid entries."""
    # Arrange
    mixed_playlist = [
        {"title": "Valid Local", "url": "/valid/local.mp4"},
        {"title": "Invalid Local", "url": "/invalid/local.mp4"},
        {"title": "Valid Remote", "url": "http://valid-url.com/video.mp4"},
        {"title": "Invalid Remote", "url": "http://invalid-url.com/video.mp4"},
    ]
    mocker.patch("os.path.exists", side_effect=[True, False])  # Mock local file existence
    mocker.patch("signengine.utils.check_remote_url", side_effect=[True, False])  # Mock remote URL checks

    # Act
    validated = await validate_playlist(mixed_playlist)

    # Assert
    assert len(validated) == 2
    assert validated[0]["title"] == "Valid Local"
    assert validated[1]["title"] == "Valid Remote"