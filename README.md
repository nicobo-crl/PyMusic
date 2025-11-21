# 🎵 PyMusic

A lightweight, web-based music streaming application built with Python (Flask). It mimics the Spotify UI to provide a seamless listening experience without ads.

## ✨ Features

*   **Instant Streaming:** Streams audio directly from YouTube (via `yt-dlp`) with low latency.
*   **Rich Metadata:** Uses the **Deezer API** for high-quality album art, correct song titles, and artist names.
*   **Synced Lyrics:** Automatically fetches and highlights lyrics line-by-line using **LRCLIB**.
*   **Smart Search:** aggressive fallback search to find lyrics even if titles don't match perfectly.
*   **Favourites System:** Saves your liked songs to your browser's local storage.
*   **System Integration:** Supports Windows/Mac Media keys (Play/Pause/Next) and displays info in the control center.

## 🛠️ Tech Stack

*   **Backend:** Python, Flask
*   **Frontend:** HTML5, CSS3, Vanilla JavaScript
*   **APIs/Libraries:** 
    *   `yt-dlp` (Audio extraction)
    *   Deezer API (Metadata)
    *   LRCLIB (Lyrics)

## 🚀 How to Run

### Prerequisites
1.  **Python 3.x** installed.
2.  **FFmpeg** installed on your system (required by yt-dlp for audio processing).

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/nicobo-crl/PyMusic
    cd PyMusic
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Run the application:
    ```bash
    python app.py
    ```

4.  Open your browser and go to:
    `localhost:5000`

## ⚖️ Disclaimer

This project is for **educational purposes only**. It demonstrates how to handle API requests, audio streaming, and frontend-backend integration in Python. 
*   Downloading or streaming copyrighted content without a license may violate laws in your country.
*   Scraping YouTube violates their Terms of Service.
*   Please support artists by using official streaming services.
  haha

## 📝 License

[MIT](https://choosealicense.com/licenses/mit/)
