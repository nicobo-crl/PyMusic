# 🎵 PyMusic

A lightweight, web-based music streaming application built with Python (Flask). It mimics the Spotify UI to provide a seamless listening experience without ads.

## ✨ Screenshots
<img width="550" height="300" alt="Screenshot 2025-11-21 194453" src="https://github.com/user-attachments/assets/76b35f2c-ab38-4111-a5ad-db08272225f1" />
<img width="550" height="300" alt="Screenshot 2025-11-21 194406" src="https://github.com/user-attachments/assets/d9f5a366-ccbf-4d70-b1f5-57d13194b41f" />

## ✨ Features

*   **Instant Streaming:** Streams audio directly from YouTube (via `yt-dlp`) with low latency.
*   **Rich Metadata:** Uses the **Deezer API** for high-quality album art, correct song titles, and artist names.
*   **Synced Lyrics:** Automatically fetches and highlights lyrics line-by-line using **LRCLIB**.
*   **Smart Search:** aggressive fallback search to find lyrics even if titles don't match perfectly.
*   **Favourites System:** Saves your liked songs to your browser's local storage.
*   **System Integration:** Supports Windows/Mac Media keys (Play/Pause/Next) and displays info in the control center.
*   **User Authentication:** A simple user authentication system with roles (admin and user).
*   **Admin Panel:** A simple admin panel to manage users.

## 🛠️ Tech Stack

*   **Backend:** Python, Flask
*   **Frontend:** HTML5, CSS3, Vanilla JavaScript
*   **Database:** SQLite
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

**Note:** On the first run, an admin account is created with the username `admin` and a default password. You will be prompted to change this password upon your first login.

## ⚖️ Disclaimer

This project is for **educational purposes only**. It demonstrates how to handle API requests, audio streaming, and frontend-backend integration in Python.
*   Downloading or streaming copyrighted content without a license may violate laws in your country.
*   Scraping YouTube violates their Terms of Service.
*   Please support artists by using official streaming services.

## 📝 License

[MIT](https://choosealicense.com/licenses/mit/)
