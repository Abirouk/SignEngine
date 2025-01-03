import pytest
from unittest.mock import Mock, AsyncMock, call
from signengine.player import PlaybackEngine

# Constants for testing
VIDEO_OUTPUT_ID = 12345678
MEDIA_PATH = "http://example.com/video.mp4"
VOLUME_LEVEL = 50

# Fixture to mock vlc module and its components
@pytest.fixture
def mock_vlc(mocker):
    mock_vlc_instance = Mock()
    mock_media_player = Mock()
    mock_media = Mock()

    # Mock VLC behaviors
    mock_vlc_instance.media_player_new.return_value = mock_media_player
    mock_vlc_instance.media_new.return_value = mock_media

    mocker.patch("signengine.player.vlc.Instance", return_value=mock_vlc_instance)
    return mock_vlc_instance, mock_media_player, mock_media

# Fixture to initialize PlaybackEngine with mocked VLC
@pytest.fixture
def playback_engine(mock_vlc):
    return PlaybackEngine(video_output=VIDEO_OUTPUT_ID)


# Test Initialization
def test_playback_engine_init(mock_vlc, playback_engine):
    mock_vlc_instance, mock_media_player, _ = mock_vlc
    mock_vlc_instance.media_player_new.assert_called_once()
    mock_media_player.set_nsobject.assert_called_once_with(VIDEO_OUTPUT_ID)  # Adjust for platform


# Test Play
@pytest.mark.asyncio
async def test_playback_engine_play(mock_vlc, playback_engine):
    _, mock_media_player, mock_media = mock_vlc

    # Act
    await playback_engine.play(MEDIA_PATH)

    # Assert
    mock_media_player.set_media.assert_called_once_with(mock_media)
    mock_media_player.play.assert_called_once()
    mock_vlc[0].media_new.assert_called_once_with(MEDIA_PATH)


# Test Pause
@pytest.mark.asyncio
async def test_playback_engine_pause(mock_vlc, playback_engine):
    _, mock_media_player, _ = mock_vlc
    await playback_engine.pause()
    mock_media_player.pause.assert_called_once()


# Test Stop
@pytest.mark.asyncio
async def test_playback_engine_stop(mock_vlc, playback_engine):
    _, mock_media_player, _ = mock_vlc
    await playback_engine.stop()
    mock_media_player.stop.assert_called_once()


# Test Set Volume
@pytest.mark.asyncio
async def test_playback_engine_set_volume(mock_vlc, playback_engine):
    _, mock_media_player, _ = mock_vlc
    await playback_engine.set_volume(VOLUME_LEVEL)
    mock_media_player.audio_set_volume.assert_called_once_with(VOLUME_LEVEL)


# Test Invalid Play
@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_path", [None, "", "invalid://url"])
async def test_playback_engine_invalid_play(mock_vlc, playback_engine, invalid_path):
    _, mock_media_player, _ = mock_vlc
    await playback_engine.play(invalid_path)
    mock_media_player.set_media.assert_not_called()
    mock_media_player.play.assert_not_called()


# Test Repeat Play
@pytest.mark.asyncio
async def test_playback_engine_repeat_play(mock_vlc, playback_engine):
    _, mock_media_player, mock_media = mock_vlc
    await playback_engine.play(MEDIA_PATH)
    new_media_path = "http://example.com/new_video.mp4"
    await playback_engine.play(new_media_path)
    mock_media_player.stop.assert_called_once()
    mock_media_player.set_media.assert_has_calls(
        [call(mock_media), call(mock_media)], any_order=False
    )
    mock_media_player.play.assert_called()


# Test Exception Handling
@pytest.mark.asyncio
async def test_playback_engine_handles_exceptions(mocker, playback_engine):
    mocker.patch(
        "signengine.player.vlc.MediaPlayer.play", side_effect=Exception("Unexpected Error")
    )
    result = await playback_engine.play(MEDIA_PATH)
    assert result is None