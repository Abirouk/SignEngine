import vlc
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

#Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("PlaybackEngine")

# Async wrapper around VLC for video playback.
class PlaybackEngine:

    def __init__(self, video_output: Optional[int] = None):

        #Initialize the playback engine.
        logger.info("Initializing Playback Engine")
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        # Initialize the playback engine
        self.loop = asyncio.get_running_loop()

        # Thread pool for non-async VLC operations
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Set video output if provided
        if video_output:
            self._set_video_output(video_output)

    def _set_video_output(self, video_output: int):

        logger.info(f"Setting video output to: {video_output}")

        if hasattr(self.player, "set_hwnd"):  # Windows
            self.player.set_hwnd(video_output)
        elif hasattr(self.player, "set_xwindow"):  # Linux
            self.player.set_xwindow(video_output)
        elif hasattr(self.player, "set_nsobject"):  # macOS
            self.player.set_nsobject(video_output)
        else:
            logger.warning("Unknown platform. Video output not set.")

    #Play a video file/stream
    async def play(self, media_path: str):

        logger.info(f"Loading media: {media_path}")
        try:
            media = await self.loop.run_in_executor(
                self.executor, self.instance.media_new, media_path
            )
            if not media:
                logger.error("Failed to create media object. Check the path or URL.")
                return

            # Debugging lines
            logger.debug(f"Media object created: {media}")
            logger.debug("Setting media to player...")

            await self.loop.run_in_executor(self.executor, self.player.set_media, media)
            logger.info("Starting playback...")
            await self.loop.run_in_executor(self.executor, self.player.play)
            logger.info("Playback started successfully.")
        except Exception as e:
            logger.error(f"Error during playback: {e}")

    #Pause the vid playback
    async def pause(self):

        if await self.loop.run_in_executor(self.executor, self.player.is_playing):
            logger.info("Pausing playback")
            await self.loop.run_in_executor(self.executor, self.player.pause)
        else:
            logger.warning("Player is not currently playing.")

    #Stop the vid placback
    async def stop(self):

        logger.info("Stopping playback")
        await self.loop.run_in_executor(self.executor, self.player.stop)

    #Set the volume level
    async def set_volume(self, volume: int):

        logger.info(f"Setting volume to: {volume}")
        await self.loop.run_in_executor(self.executor, self.player.audio_set_volume, volume)

    #Get the volume level
    async def get_volume(self) -> int:

        return await self.loop.run_in_executor(self.executor, self.player.audio_get_volume)

    #Seek to a specific position in the vid
    async def seek(self, position: float):

        logger.info(f"Seeking to position: {position * 100:.2f}%")
        if 0.0 <= position <= 1.0:
            await self.loop.run_in_executor(self.executor, self.player.set_position, position)
        else:
            logger.warning("Invalid seek position. Must be between 0.0 and 1.0.")

    #Get the current playback position
    async def get_position(self) -> float:

        return await self.loop.run_in_executor(self.executor, self.player.get_position)

    #Check if the player is currently playing
    async def is_playing(self) -> bool:

        return await self.loop.run_in_executor(self.executor, self.player.is_playing)