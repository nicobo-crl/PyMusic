# 🎵 PyMusic




A lightweight, web-based music streaming application built with Python (Flask). It mimics the Spotify UI to provide a seamless listening experience without ads.

## ✨ Screenshots


<img width="974" height="554" alt="Screenshot 2025-12-30 at 11-35-40 PyMusic(1)" src="https://github.com/user-attachments/assets/b250b63b-48cb-49f4-b5d7-59ec7dc34abb" />
<img width="973" height="799" alt="Screenshot 2025-12-30 at 11-24-31 PyMusic" src="https://github.com/user-attachments/assets/87e8682e-d669-4a1f-9fb7-1f1f47e3f306" />
<img width="970" height="801" alt="Screenshot 2025-12-30 112649" src="https://github.com/user-attachments/assets/c853d9df-e2e2-498b-8e8d-9b7dc60ad735" />
<img width="975" height="802" alt="Screenshot 2025-12-30 at 11-24-47 PyMusic" src="https://github.com/user-attachments/assets/9a275713-e756-4634-9c09-bcd4afca9891" />

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
## 🚀 Quick Start (Docker)

The easiest way to run PyMusic is using Docker. You do not need to install Python or FFmpeg.

1.  **Install Docker Desktop** (if you haven't already).
2.  **Download the [docker-compose.yml](https://github.com/nicobo-crl/PyMusic/blob/main/docker-compose.yml)** file from this repository.
3.  Open a terminal in the folder where you saved the file.
4.  Run this command:
    ```bash
    docker-compose up -d
    ```
5.  Open your browser to: `http://localhost:499`

*Default Login:* `admin` / `admin123`


   
## ⚖️ Disclaimer

This project is for **educational purposes only**. It demonstrates how to handle API requests, audio streaming, and frontend-backend integration in Python. 
*   Downloading or streaming copyrighted content without a license may violate laws in your country.
*   Scraping YouTube violates their Terms of Service.
*   Please support artists by using official streaming services.
  haha

## 📝 License

[MIT](https://choosealicense.com/licenses/mit/)
