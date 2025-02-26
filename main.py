from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import requests
import uvicorn
import os
import json
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/callback"

def get_access_token(auth_code: str):
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": REDIRECT_URI,
        },
        auth=(CLIENT_ID, CLIENT_SECRET),
    )
    tokens = response.json()
    access_token = tokens["access_token"]
    refresh_token = tokens.get("refresh_token")

    if refresh_token:
        with open("refresh_token.txt", "w") as f:
            f.write(refresh_token)

    return {"Authorization": "Bearer " + access_token}

def refresh_access_token():
    if not os.path.exists("refresh_token.txt"):
        return None

    with open("refresh_token.txt", "r") as f:
        refresh_token = f.read()

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        auth=(CLIENT_ID, CLIENT_SECRET),
    )

    tokens = response.json()
    access_token = tokens["access_token"]
    return {"Authorization": "Bearer " + access_token}

def get_top_tracks(time_range="medium_term", limit=50):
    headers = refresh_access_token()
    if not headers:
        return None

    print(f"Fetching top {limit} tracks for time range: {time_range}...")

    response = requests.get(
        f"https://api.spotify.com/v1/me/top/tracks?limit={limit}&time_range={time_range}",
        headers=headers
    )

    if response.status_code == 401:
        print("Token expired. Refreshing token...")
        headers = refresh_access_token()
        response = requests.get(
            f"https://api.spotify.com/v1/me/top/tracks?limit={limit}&time_range={time_range}",
            headers=headers
        )

    data = response.json()
    items = data.get("items", [])
    print(f"Fetched {len(items)} tracks.")

    top_tracks = [
        {
            "song": item["name"],
            "artist": item["artists"][0]["name"],
            "album": item["album"]["name"],
            "popularity": item["popularity"],
            "image": item["album"]["images"][0]["url"] if item["album"]["images"] else None
        }
        for item in items
    ]

    return top_tracks

def get_older_top_tracks():
    medium_term_tracks = get_top_tracks(time_range="medium_term", limit=50)
    if not medium_term_tracks:
        return None

    long_term_tracks = get_top_tracks(time_range="long_term", limit=50)
    if not long_term_tracks:
        return None

    medium_term_song_names = {track["song"] for track in medium_term_tracks}

    older_tracks = [
        track for track in long_term_tracks
        if track["song"] not in medium_term_song_names
    ]

    return older_tracks

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/auth")
async def auth():
    scope = [
        "user-top-read"
    ]
    auth_url = (
        f"https://accounts.spotify.com/authorize?"
        f"response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&scope={' '.join(scope)}"
    )
    return RedirectResponse(url=auth_url)

@app.get("/callback")
async def callback(code: str):
    headers = get_access_token(code)
    return RedirectResponse(url="/")

@app.get("/api/older-tracks")
async def get_older_tracks():
    headers = refresh_access_token()
    if not headers:
        return JSONResponse(content={"error": "Not authenticated"}, status_code=401)

    older_tracks = get_older_top_tracks()
    if not older_tracks:
        return JSONResponse(content={"error": "Failed to fetch tracks"}, status_code=500)

    return JSONResponse(content={"older_tracks": older_tracks})

if __name__ == "__main__":
    uvicorn.run(app)