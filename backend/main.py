from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict
import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from transformers import pipeline
import os

app = FastAPI()
@app.get("/")
def read_root():
    return {"Hello": "World"}

# Allow frontend local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- Your Model Configs ---------
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
MAX_COMMENTS = 200
COMMENTS_PER_CHUNK = 10

# --------- Input/Output Models ---------
class SummarizeRequest(BaseModel):
    video_url: str

class SummarizeResponse(BaseModel):
    n_comments: int
    n_positive: int
    n_negative: int
    summary: str
    raw_summary_chunks: Any

# --------- Helpers from your code ---------
def extract_video_id(url: str) -> str:
    m = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    if not m:
        raise ValueError(f"Cannot parse ID from URL: {url}")
    return m.group(1)

def get_comments(youtube, vid: str, limit: int):
    comments, token = [], None
    while len(comments) < limit:
        resp = youtube.commentThreads().list(
            part="snippet",
            videoId=vid,
            maxResults=min(100, limit - len(comments)),
            pageToken=token,
            textFormat="plainText"
        ).execute()
        for item in resp["items"]:
            comments.append(item["snippet"]["topLevelComment"]["snippet"]["textDisplay"])
        token = resp.get("nextPageToken")
        if not token:
            break
    return comments

sentiment_analyzer = pipeline("sentiment-analysis")
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

@app.post("/summarize", response_model=SummarizeResponse)
def summarize_comments(req: SummarizeRequest):
    try:
        vid_id = extract_video_id(req.video_url)
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        comments = get_comments(youtube, vid_id, MAX_COMMENTS)
        if len(comments) == 0:
            raise HTTPException(status_code=404, detail=f"No comments found.")

        # Sentiment analysis
        results = sentiment_analyzer(comments, batch_size=32)
        pos = sum(1 for r in results if r["label"] == "POSITIVE")
        neg = len(results) - pos

        # Chunk-wise summarization
        chunk_summaries = []
        for i in range(0, len(comments), COMMENTS_PER_CHUNK):
            chunk = comments[i:i+COMMENTS_PER_CHUNK]
            joined = "  \n".join(chunk)
            sum_text = summarizer(
                joined,
                max_length=60,
                min_length=20,
                do_sample=False
            )[0]["summary_text"]
            chunk_summaries.append(sum_text)

        final_input = "  \n".join(chunk_summaries)
        decision = summarizer(
            final_input,
            max_length=60,
            min_length=15,
            do_sample=False
        )[0]["summary_text"]

        return SummarizeResponse(
            n_comments = len(comments),
            n_positive = pos,
            n_negative = neg,
            summary = decision,
            raw_summary_chunks = chunk_summaries
        )

    except HttpError as he:
        raise HTTPException(status_code=500, detail=f"YouTube API error: {he}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

