from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QListWidget, QPushButton, QHBoxLayout, QSlider, QLabel
from PyQt5.QtCore import Qt
from qasync import QEventLoop
import asyncio
from signengine.api_client import fetch_playlist
from signengine.player import PlaybackEngine

class SignEngineGUI(QMainWindow):
    def __init__(self, loop):
        super().__init__()
        self.setWindowTitle("SignEngine GUI")
        self.setGeometry(100, 100, 800, 600)

        # Main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)

        # Playlist
        self.playlist_label = QLabel("Playlist:")
        self.playlist = QListWidget()
        self.layout.addWidget(self.playlist_label)
        self.layout.addWidget(self.playlist)

        # Playback controls
        self.controls_layout = QHBoxLayout()
        self.play_button = QPushButton("Play")
        self.pause_button = QPushButton("Pause")
        self.stop_button = QPushButton("Stop")
        self.controls_layout.addWidget(self.play_button)
        self.controls_layout.addWidget(self.pause_button)
        self.controls_layout.addWidget(self.stop_button)
        self.layout.addLayout(self.controls_layout)

        # Volume control
        self.volume_label = QLabel("Volume:")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(50)
        self.layout.addWidget(self.volume_label)
        self.layout.addWidget(self.volume_slider)

        # Playback engine with provided event loop
        self.loop = loop
        self.player = PlaybackEngine(loop=self.loop)

        # Connect signals
        self.play_button.clicked.connect(self.handle_play)
        self.pause_button.clicked.connect(self.handle_pause)
        self.stop_button.clicked.connect(self.handle_stop)
        self.volume_slider.valueChanged.connect(self.handle_volume)

        # Load playlist
        self.loop.create_task(self.load_playlist())

    async def load_playlist(self):
        """Fetch playlist from the API and populate the list."""
        try:
            playlist = await fetch_playlist()
            if not playlist:
                self.playlist.addItem("Failed to fetch playlist or empty playlist.")
                return

            self.playlist.clear()
            self.playlist_data = playlist
            for item in playlist:
                self.playlist.addItem(item["title"])
            self.playlist.itemDoubleClicked.connect(self.play_selected_video)
        except Exception as e:
            self.playlist.addItem(f"Error loading playlist: {str(e)}")

    def play_selected_video(self, item):
        """Play the video selected from the playlist."""
        video_title = item.text()
        video_url = next((entry["url"] for entry in self.playlist_data if entry["title"] == video_title), None)
        if video_url:
            self.loop.create_task(self.player.play(video_url))

    def handle_play(self):
        """Handle play button click."""
        selected_item = self.playlist.currentItem()
        if selected_item:
            self.play_selected_video(selected_item)

    def handle_pause(self):
        """Handle pause button click."""
        self.loop.create_task(self.player.pause())

    def handle_stop(self):
        """Handle stop button click."""
        self.loop.create_task(self.player.stop())

    def handle_volume(self, value):
        """Handle volume slider change."""
        self.loop.create_task(self.player.set_volume(value))


if __name__ == "__main__":
    import sys
    from qasync import QEventLoop

    app = QApplication(sys.argv)

    # Create and set the asyncio event loop
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    gui = SignEngineGUI(loop)
    gui.show()

    # Run the PyQt app with asyncio event loop
    with loop:
        loop.run_forever()