import vlc
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import re

# Logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("PlaybackEngine")

# Async wrapper around VLC for video playback.
class PlaybackEngine:

    def __init__(self, video_output: Optional[int] = None, loop: Optional[asyncio.AbstractEventLoop] = None):
        # Initialize the playback engine
        logger.info("Initializing Playback Engine")
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        
        # Use provided loop or the running loop
        if loop:
            self.loop = loop
        else:
            self.loop = asyncio.get_running_loop()

        # Thread pool for non-async VLC operations
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Set video output if provided
        if video_output:
            self._set_video_output(video_output)

    def _set_video_output(self, video_output: int):
        logger.info(f"Setting video output to: {video_output}")
        if hasattr(self.player, "set_nsobject") and callable(self.player.set_nsobject):  # macOS
            self.player.set_nsobject(video_output)
        elif hasattr(self.player, "set_hwnd") and callable(self.player.set_hwnd):  # Windows
            self.player.set_hwnd(video_output)
        elif hasattr(self.player, "set_xwindow") and callable(self.player.set_xwindow):  # Linux
            self.player.set_xwindow(video_output)
        else:
            logger.warning("Unknown platform or unsupported video output method.")

    async def play(self, media_path: Optional[str]):
        VALID_SCHEMES = re.compile(r'^(http|https|file)://')
        if not media_path or not VALID_SCHEMES.match(media_path):
            logger.warning(f"Invalid media path: {media_path}")
            return

        try:
            # Check current media path
            current_media = self.player.get_media()
            current_media_path = (
                current_media.get_mrl() if current_media and current_media.get_mrl() else None
            )

            if current_media_path == media_path:
                logger.info("Media already loaded. Restarting playback...")
                await self.loop.run_in_executor(self.executor, self.player.play)
                return

            # Stop current playback only if playing
            if await self.is_playing():
                logger.info("Stopping current playback before starting new media...")
                await self.loop.run_in_executor(self.executor, self.player.stop)
                logger.debug("stop() executed during play transition")

            # Load and play new media
            logger.info(f"Loading media: {media_path}")
            media = await self.loop.run_in_executor(self.executor, self.instance.media_new, media_path)
            if not media:
                logger.error("Failed to create media object. Check the path or URL.")
                return

            self.player.set_media(media)
            logger.info("Starting playback...")
            await self.loop.run_in_executor(self.executor, self.player.play)
            logger.info("Playback started successfully.")
        except Exception as e:
            logger.error(f"Error during playback: {e}")

    async def stop(self):
        logger.info("Stopping playback...")
        await self.loop.run_in_executor(self.executor, self.player.stop)

    async def pause(self):
        if await self.loop.run_in_executor(self.executor, self.player.is_playing):
            logger.info("Pausing playback")
            await self.loop.run_in_executor(self.executor, self.player.pause)
        else:
            logger.warning("Player is not currently playing.")

    async def set_volume(self, volume: int):
        logger.info(f"Setting volume to: {volume}")
        await self.loop.run_in_executor(self.executor, self.player.audio_set_volume, volume)

    async def get_volume(self) -> int:
        return await self.loop.run_in_executor(self.executor, self.player.audio_get_volume)

    async def seek(self, position: float):
        logger.info(f"Seeking to position: {position * 100:.2f}%")
        if 0.0 <= position <= 1.0:
            await self.loop.run_in_executor(self.executor, self.player.set_position, position)
        else:
            logger.warning("Invalid seek position. Must be between 0.0 and 1.0.")

    async def get_position(self) -> float:
        return await self.loop.run_in_executor(self.executor, self.player.get_position)

    async def is_playing(self) -> bool:
        is_playing = await self.loop.run_in_executor(self.executor, self.player.is_playing)
        logger.info(f"is_playing() returned: {is_playing}")
        return is_playing