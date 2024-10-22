# Spotify-Adapter
Service for interfacing with the Spotify API


## Usage

You need to configure a .env file with your Spotify App information like this:

```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret

```

`uvicorn app.main:app --reload --port 8080`

This services currently runs on `http://127.0.0.1:8080` by default for testing.
