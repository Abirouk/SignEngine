import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, call
from signengine.player import PlaybackEngine

# Constants for testing
VIDEO_OUTPUT_ID = 12345678
MEDIA_PATH = "http://example.com/video.mp4"
VOLUME_LEVEL = 50


# Fixture: Fresh event loop for each test
@pytest.fixture
def event_loop():
    """Ensure a fresh event loop for each test."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


# Fixture: Mock VLC module and its components
@pytest.fixture
def mock_vlc(mocker):
    """Mock VLC module and components."""
    mock_vlc_instance = Mock()
    mock_media_player = Mock()
    mock_media = Mock()

    # Mock platform-specific video output methods
    mock_media_player.set_nsobject = Mock()
    mock_media_player.set_hwnd = Mock()
    mock_media_player.set_xwindow = Mock()

    # Mock VLC behaviors
    mock_vlc_instance.media_player_new.return_value = mock_media_player
    mock_vlc_instance.media_new.return_value = mock_media

    mocker.patch("signengine.player.vlc.Instance", return_value=mock_vlc_instance)
    return mock_vlc_instance, mock_media_player, mock_media


# Fixture: Initialize PlaybackEngine with mocked VLC
@pytest.fixture
def playback_engine(mock_vlc):
    """Initialize PlaybackEngine with mocked VLC."""
    return PlaybackEngine(video_output=VIDEO_OUTPUT_ID)


# Test: Initialization
def test_playback_engine_init(mock_vlc, playback_engine):
    """Test that PlaybackEngine initializes correctly."""
    mock_vlc_instance, mock_media_player, _ = mock_vlc
    mock_vlc_instance.media_player_new.assert_called_once()
    mock_media_player.set_nsobject.assert_called_once_with(VIDEO_OUTPUT_ID)  # Adjust for platform


# Test: Play media
@pytest.mark.asyncio
async def test_playback_engine_play(mock_vlc, playback_engine, event_loop):
    """Test that the play method sets the media and starts playback."""
    _, mock_media_player, mock_media = mock_vlc

    # Act
    await playback_engine.play(MEDIA_PATH)

    # Assert
    mock_media_player.set_media.assert_called_once_with(mock_media)
    mock_media_player.play.assert_called_once()
    mock_vlc[0].media_new.assert_called_once_with(MEDIA_PATH)


# Test: Pause playback
@pytest.mark.asyncio
async def test_playback_engine_pause(mock_vlc, playback_engine, event_loop):
    """Test that the pause method pauses playback."""
    _, mock_media_player, _ = mock_vlc
    await playback_engine.pause()
    mock_media_player.pause.assert_called_once()


# Test: Stop playback
@pytest.mark.asyncio
async def test_playback_engine_stop(mock_vlc, playback_engine, event_loop):
    """Test that the stop method stops playback."""
    _, mock_media_player, _ = mock_vlc
    await playback_engine.stop()
    mock_media_player.stop.assert_called_once()


# Test: Set volume
@pytest.mark.asyncio
async def test_playback_engine_set_volume(mock_vlc, playback_engine, event_loop):
    """Test that the set_volume method adjusts volume."""
    _, mock_media_player, _ = mock_vlc
    await playback_engine.set_volume(VOLUME_LEVEL)
    mock_media_player.audio_set_volume.assert_called_once_with(VOLUME_LEVEL)


# Test: Invalid media play
@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_path", [None, "", "invalid://url"])
async def test_playback_engine_invalid_play(mock_vlc, playback_engine, invalid_path, event_loop):
    """Test that invalid paths do not start playback."""
    _, mock_media_player, _ = mock_vlc
    await playback_engine.play(invalid_path)
    mock_media_player.set_media.assert_not_called()
    mock_media_player.play.assert_not_called()


# Test: Repeat play
@pytest.mark.asyncio
async def test_playback_engine_repeat_play(mock_vlc, playback_engine, event_loop):
    """Test that playing new media stops the current playback."""
    _, mock_media_player, mock_media = mock_vlc

    # Act: First play
    await playback_engine.play(MEDIA_PATH)
    # Mock a second media path
    new_media_path = "http://example.com/new_video.mp4"
    await playback_engine.play(new_media_path)

    # Assert
    mock_media_player.stop.assert_called_once()  # Current playback should be stopped
    mock_media_player.set_media.assert_has_calls(
        [call(mock_media), call(mock_media)], any_order=False
    )
    mock_media_player.play.assert_called()


# Test: Exception handling during playback
@pytest.mark.asyncio
async def test_playback_engine_handles_exceptions(mocker, playback_engine, event_loop):
    """Test that exceptions during playback are handled gracefully."""
    mocker.patch(
        "signengine.player.vlc.MediaPlayer.play", side_effect=Exception("Unexpected Error")
    )
    result = await playback_engine.play(MEDIA_PATH)
    assert result is None