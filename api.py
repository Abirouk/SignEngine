from fastapi import FastAPI
from typing import List

app = FastAPI()

@app.get("/playlist")
async def get_playlist() -> List[dict]:
    return [
        {"title": "Example Video 1", "url": "http://example.com/video1.mp4"},
        {"title": "Example Video 2", "url": "http://example.com/video2.mp4"},
    ]