from flask import Flask, render_template, request, jsonify, Response, stream_with_context, session, redirect, url_for, send_file
import yt_dlp
import requests
import re
import sqlite3
import random
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "super_secret_key_change_this_in_production" 
DB_NAME = "pymusic.db"

# --- DATABASE SETUP ---
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        # Users Table
        c.execute('''CREATE TABLE IF NOT EXISTS users 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      username TEXT UNIQUE NOT NULL, 
                      password TEXT NOT NULL, 
                      role TEXT NOT NULL)''')
        
        # Likes Table (New)
        # Stores song_id to prevent duplicates, and song_data (JSON) so we don't have to re-fetch from Deezer
        c.execute('''CREATE TABLE IF NOT EXISTS likes 
                     (user_id INTEGER, 
                      song_id TEXT, 
                      song_data TEXT, 
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                      PRIMARY KEY (user_id, song_id))''')
        
        # Cache Table
        c.execute('''CREATE TABLE IF NOT EXISTS cache
                     (song_id TEXT PRIMARY KEY,
                      filepath TEXT NOT NULL,
                      created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')

        # Default Admin
        c.execute("SELECT * FROM users WHERE username = ?", ('admin',))
        if not c.fetchone():
            hashed_pw = generate_password_hash("mko09ijn")
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', hashed_pw, 'admin'))
        conn.commit()

init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def get_cache_size():
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(CACHE_DIR):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def sanitize_song_id(song_id):
    """Prevents path traversal by keeping only alphanumeric chars."""
    return "".join(c for c in song_id if c.isalnum())

def clear_cache():
    conn = get_db_connection()
    conn.execute("DELETE FROM cache")
    conn.commit()
    conn.close()
    for f in os.listdir(CACHE_DIR):
        os.remove(os.path.join(CACHE_DIR, f))

# --- HELPER FUNCTIONS (Keep existing ones exactly as they were) ---
# Copy: search_deezer, get_chart, get_recommendations, get_youtube_stream_url, fetch_lyrics
# ... (I am hiding them to save space, ensure you keep them in your file!) ...

def search_deezer(query):
    # ... (Keep existing code) ...
    url = f"https://api.deezer.com/search?q={query}"
    try:
        response = requests.get(url)
        data = response.json()
        songs = []
        if 'data' in data:
            for item in data['data']:
                artist_name = item.get('artist', {}).get('name', 'Unknown')
                artist_id = item.get('artist', {}).get('id', 0)
                songs.append({
                    'id': str(item['id']), # Ensure ID is string for DB consistency
                    'title': item['title'],
                    'artist': artist_name,
                    'artist_id': artist_id,
                    'album': item['album']['title'],
                    'cover': item['album']['cover_medium'], 
                    'cover_xl': item['album']['cover_xl'],
                    'duration': item['duration']
                })
        return songs
    except: return []

def get_chart():
    # ... (Keep existing code) ...
    try:
        url = "https://api.deezer.com/chart"
        response = requests.get(url).json()
        songs = []
        if 'tracks' in response and 'data' in response['tracks']:
            for item in response['tracks']['data']:
                songs.append({
                    'id': str(item['id']),
                    'title': item['title'],
                    'artist': item['artist']['name'],
                    'artist_id': item['artist']['id'],
                    'album': item['album']['title'],
                    'cover': item['album']['cover_medium'], 
                    'cover_xl': item['album']['cover_xl'],
                    'duration': item['duration']
                })
        return songs
    except: return []

def get_recommendations(artist_id):
    # ... (Keep existing code) ...
    try:
        if not artist_id or artist_id == 'undefined': return []
        rel_url = f"https://api.deezer.com/artist/{artist_id}/related?limit=3"
        rel_data = requests.get(rel_url).json()
        songs = []
        artists_to_check = [artist_id]
        if 'data' in rel_data:
            for art in rel_data['data']: artists_to_check.append(art['id'])
        for aid in artists_to_check:
            top_url = f"https://api.deezer.com/artist/{aid}/top?limit=5"
            try:
                top_data = requests.get(top_url, timeout=2).json()
                if 'data' in top_data:
                    for item in top_data['data']:
                        songs.append({
                            'id': str(item['id']),
                            'title': item['title'],
                            'artist': item['artist']['name'],
                            'artist_id': item['artist']['id'],
                            'album': item.get('album', {}).get('title', 'Single'),
                            'cover': item.get('album', {}).get('cover_medium', ''), 
                            'cover_xl': item.get('album', {}).get('cover_xl', ''),
                            'duration': item['duration']
                        })
            except: continue
        random.shuffle(songs)
        return songs[:15]
    except: return []

CACHE_DIR = "cache"
MAX_CACHE_SIZE_MB = 100
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def evict_cache():
    """Evicts oldest files if cache size exceeds the limit."""
    cache_size_mb = get_cache_size() / (1024 * 1024)
    if cache_size_mb > MAX_CACHE_SIZE_MB:
        conn = get_db_connection()
        files_to_delete = conn.execute("SELECT * FROM cache ORDER BY created_at ASC").fetchall()

        songs_deleted = []
        while cache_size_mb > MAX_CACHE_SIZE_MB:
            if not files_to_delete:
                break

            song_to_delete = files_to_delete.pop(0)
            file_path = song_to_delete['filepath']

            if os.path.exists(file_path):
                file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                os.remove(file_path)
                cache_size_mb -= file_size_mb
                songs_deleted.append(song_to_delete['song_id'])

        if songs_deleted:
            # Create a string of placeholders for the IN clause
            placeholders = ','.join('?' for _ in songs_deleted)
            conn.execute(f"DELETE FROM cache WHERE song_id IN ({placeholders})", songs_deleted)
            conn.commit()

        conn.close()

def get_youtube_stream_url(artist, title, song_id):
    song_id = sanitize_song_id(song_id)
    safe_filename = f"{song_id}.m4a"
    cached_path = os.path.join(CACHE_DIR, safe_filename)
    part_path = cached_path + ".part"

    if os.path.exists(cached_path):
        return {'url': f"/stream_proxy?song_id={song_id}"}

    # If another process is downloading, wait for it to finish
    if os.path.exists(part_path):
        return {'status': 'downloading', 'message': 'Song is currently being downloaded, please try again shortly.'}

    query = f"{artist} - {title} audio"
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/best',
        'quiet': True,
        'noplaylist': True,
        'geo_bypass': True,
        'outtmpl': part_path,
        'retries': 3,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.extract_info(f"ytsearch1:{query}", download=True)
            if os.path.exists(part_path):
                os.rename(part_path, cached_path)
                conn = get_db_connection()
                conn.execute("INSERT INTO cache (song_id, filepath) VALUES (?, ?)", (song_id, cached_path))
                conn.commit()
                conn.close()
                evict_cache()  # Check and evict if necessary
                return {'url': f"/stream_proxy?song_id={song_id}"}
        except Exception as e:
            app.logger.error(f"Error downloading {query}: {e}")
            if os.path.exists(part_path):
                os.remove(part_path)
            return None
    return None

def fetch_lyrics(artist, title):
    # ... (Keep existing code) ...
    search_url = "https://lrclib.net/api/search"
    headers = {'User-Agent': 'PyMusic/1.0'}
    params = {'artist_name': artist, 'track_name': title}
    try:
        resp = requests.get(search_url, params=params, headers=headers)
        data = resp.json()
        if isinstance(data, list):
            for item in data:
                if item.get('syncedLyrics'): return item['syncedLyrics']
        return None
    except: return None

# --- LIKE API ROUTES (NEW) ---

@app.route('/api/toggle_like', methods=['POST'])
def toggle_like():
    if not session.get('user_id'): return "Unauthorized", 401
    
    data = request.json
    song = data.get('song')
    if not song: return "No song data", 400
    
    song_id = str(song['id'])
    user_id = session['user_id']
    
    conn = get_db_connection()
    # Check if exists
    exists = conn.execute("SELECT * FROM likes WHERE user_id = ? AND song_id = ?", (user_id, song_id)).fetchone()
    
    if exists:
        # Unlike
        conn.execute("DELETE FROM likes WHERE user_id = ? AND song_id = ?", (user_id, song_id))
        action = "unliked"
    else:
        # Like (Store the full song JSON so we can render it later without API calls)
        conn.execute("INSERT INTO likes (user_id, song_id, song_data) VALUES (?, ?, ?)", 
                     (user_id, song_id, json.dumps(song)))
        action = "liked"
        
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "action": action})

@app.route('/api/likes')
def get_likes():
    if not session.get('user_id'): return jsonify([])
    
    conn = get_db_connection()
    # Get likes ordered by newest first
    rows = conn.execute("SELECT song_data FROM likes WHERE user_id = ? ORDER BY timestamp DESC", (session['user_id'],)).fetchall()
    conn.close()
    
    # Convert JSON strings back to objects
    songs = [json.loads(row['song_data']) for row in rows]
    return jsonify(songs)

# --- AUTH ROUTES (Keep existing) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('index'))
        else: return render_template('login.html', error="Invalid Credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- ADMIN ROUTES (Keep existing) ---
@app.route('/admin')
def admin_panel():
    if not session.get('user_id') or session.get('role') != 'admin': return redirect(url_for('index'))
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    cache_items = conn.execute('SELECT * FROM cache').fetchall()
    conn.close()
    cache_size_mb = get_cache_size() / (1024 * 1024)
    return render_template('admin.html', users=users, cache_items=cache_items, cache_size_mb=f"{cache_size_mb:.2f}")

@app.route('/admin/clear_cache')
def admin_clear_cache():
    if not session.get('user_id') or session.get('role') != 'admin': return "Unauthorized", 401
    clear_cache()
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_cached_song/<song_id>')
def admin_delete_cached_song(song_id):
    if not session.get('user_id') or session.get('role') != 'admin': return "Unauthorized", 401
    song_id = sanitize_song_id(song_id)
    conn = get_db_connection()
    conn.execute("DELETE FROM cache WHERE song_id = ?", (song_id,))
    conn.commit()
    conn.close()

    safe_filename = f"{song_id}.m4a"
    file_path = os.path.join(CACHE_DIR, safe_filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    return redirect(url_for('admin_panel'))

@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
def admin_edit_user(user_id):
    if not session.get('user_id') or session.get('role') != 'admin': return "Unauthorized", 401

    conn = get_db_connection()

    if request.method == 'POST':
        username = request.form.get('username').strip()
        role = request.form.get('role', 'user')
        password = request.form.get('password')

        if not username:
            # Handle error
            return "Username is required", 400

        if password:
            hashed_pw = generate_password_hash(password)
            conn.execute("UPDATE users SET username = ?, role = ?, password = ? WHERE id = ?",
                         (username, role, hashed_pw, user_id))
        else:
            conn.execute("UPDATE users SET username = ?, role = ? WHERE id = ?",
                         (username, role, user_id))

        conn.commit()
        conn.close()
        return redirect(url_for('admin_panel'))

    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if not user:
        return "User not found", 404
    return render_template('edit_user.html', user=user)

@app.route('/add_user', methods=['POST'])
def add_user():
    if not session.get('user_id') or session.get('role') != 'admin': return "Unauthorized", 401
    username = request.form.get('username').strip()
    password = request.form.get('password')
    role = request.form.get('role', 'user')
    if not username or not password: return "Missing fields", 400
    hashed_pw = generate_password_hash(password)
    try:
        conn = get_db_connection()
        conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_pw, role))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError: return "Username already exists", 400
    return redirect(url_for('admin_panel'))

@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if not session.get('user_id') or session.get('role') != 'admin': return "Unauthorized", 401
    if user_id == session.get('user_id'): return "Cannot delete yourself", 400
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

# --- MAIN ROUTES (Keep existing) ---
@app.route('/')
def index():
    if not session.get('user_id'): return redirect(url_for('login'))
    return render_template('index.html', username=session.get('username'), role=session.get('role'))

@app.route('/search')
def search():
    if not session.get('user_id'): return jsonify([])
    return jsonify(search_deezer(request.args.get('q')))

@app.route('/chart')
def chart():
    if not session.get('user_id'): return jsonify([])
    return jsonify(get_chart())

@app.route('/recommend')
def recommend():
    if not session.get('user_id'): return jsonify([])
    return jsonify(get_recommendations(request.args.get('artist_id')))

@app.route('/play')
def play():
    if not session.get('user_id'): return jsonify({'error': 'Unauthorized'}), 401
    song_id = request.args.get('song_id')
    artist = request.args.get('artist')
    title = request.args.get('title')

    if not song_id or not artist or not title:
        return jsonify({'error': 'Missing required parameters'}), 400

    return jsonify(get_youtube_stream_url(artist, title, song_id))

@app.route('/lyrics')
def lyrics():
    if not session.get('user_id'): return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'lyrics': fetch_lyrics(request.args.get('artist'), request.args.get('title'))})

@app.route('/stream_proxy')
def stream_proxy():
    if not session.get('user_id'): return "Unauthorized", 401

    song_id = request.args.get('song_id')
    if not song_id: return "Missing song_id", 400

    song_id = sanitize_song_id(song_id)
    safe_filename = f"{song_id}.m4a"
    file_path = os.path.join(CACHE_DIR, safe_filename)

    if not os.path.exists(file_path):
        return "File not found", 404

    range_header = request.headers.get('Range', None)
    if not range_header:
        return send_file(file_path, mimetype='audio/mp4')

    size = os.path.getsize(file_path)
    byte1, byte2 = 0, None

    m = re.search(r'(\d+)-(\d*)', range_header)
    g = m.groups()

    if g[0]: byte1 = int(g[0])
    if g[1]: byte2 = int(g[1])

    length = size - byte1
    if byte2 is not None:
        length = byte2 - byte1 + 1

    data = None
    with open(file_path, 'rb') as f:
        f.seek(byte1)
        data = f.read(length)

    rv = Response(data, 206, mimetype="audio/mp4", content_type="audio/mp4", direct_passthrough=True)
    rv.headers.add('Content-Range', f'bytes {byte1}-{byte1 + length - 1}/{size}')
    rv.headers.add('Accept-Ranges', 'bytes')
    return rv

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)