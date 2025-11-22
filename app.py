from flask import Flask, render_template, request, jsonify, Response, stream_with_context, session, redirect, url_for
import yt_dlp
import requests
import re
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

APP_PASSWORD = "mko09ijn"

# --- HELPER FUNCTIONS ---

def search_deezer(query):
    url = f"https://api.deezer.com/search?q={query}"
    try:
        response = requests.get(url)
        data = response.json()
        songs = []
        if 'data' in data:
            for item in data['data']:
                songs.append({
                    'id': item['id'],
                    'title': item['title'],
                    'artist': item['artist']['name'],
                    'album': item['album']['title'],
                    'cover': item['album']['cover_medium'], 
                    'cover_xl': item['album']['cover_xl'],
                    'duration': item['duration']
                })
        return songs
    except Exception as e:
        return []

def get_chart():
    url = "https://api.deezer.com/chart"
    try:
        response = requests.get(url)
        data = response.json()
        songs = []
        if 'tracks' in data and 'data' in data['tracks']:
            for item in data['tracks']['data']:
                songs.append({
                    'id': item['id'],
                    'title': item['title'],
                    'artist': item['artist']['name'],
                    'album': item['album']['title'],
                    'cover': item['album']['cover_medium'], 
                    'cover_xl': item['album']['cover_xl'],
                    'duration': item['duration']
                })
        return songs
    except Exception as e:
        return []

def get_youtube_stream_url(artist, title):
    query = f"{artist} - {title} audio"
    
    # --- CRITICAL FIX FOR IPHONE ---
    # 1. We search for 'bestaudio[ext=m4a]' to force AAC format.
    # 2. We use 'ipv4' to prevent IPv6 timeouts on some networks.
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/best', 
        'quiet': True,
        'noplaylist': True,
        'geo_bypass': True,
        'source_address': '0.0.0.0', # Force IPv4
    }
    
    search_query = f"ytsearch1:{query}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(search_query, download=False)
            video = info['entries'][0] if 'entries' in info else info
            return {'url': video['url']}
        except Exception as e:
            print(f"Error: {e}")
            return None

def clean_string(s):
    s = re.sub(r'\([^)]*\)', '', s)
    s = re.sub(r'\[[^]]*\]', '', s)
    return s.strip()

def fetch_lyrics(artist, title):
    search_url = "https://lrclib.net/api/search"
    headers = {'User-Agent': 'PySpotifyClone/1.0'}
    params = {'artist_name': artist, 'track_name': title}
    try:
        resp = requests.get(search_url, params=params, headers=headers)
        data = resp.json()
        if isinstance(data, list):
            for item in data:
                if item.get('syncedLyrics'): return item['syncedLyrics']
        clean_title = clean_string(title)
        if clean_title != title:
            params['track_name'] = clean_title
            resp = requests.get(search_url, params=params, headers=headers)
            data = resp.json()
            if isinstance(data, list):
                for item in data:
                    if item.get('syncedLyrics'): return item['syncedLyrics']
        params = {'q': clean_title} 
        resp = requests.get(search_url, params=params, headers=headers)
        data = resp.json()
        if isinstance(data, list):
            for item in data:
                if item.get('syncedLyrics'):
                    if artist.lower() in item['artistName'].lower() or item['artistName'].lower() in artist.lower():
                        return item['syncedLyrics']
        return None
    except:
        return None

# --- ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == APP_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Incorrect Password")
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/search')
def search():
    if not session.get('logged_in'): return jsonify([])
    return jsonify(search_deezer(request.args.get('q')))

@app.route('/chart')
def chart():
    if not session.get('logged_in'): return jsonify([])
    return jsonify(get_chart())

@app.route('/play')
def play():
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(get_youtube_stream_url(request.args.get('artist'), request.args.get('title')))

@app.route('/lyrics')
def lyrics():
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'lyrics': fetch_lyrics(request.args.get('artist'), request.args.get('title'))})

@app.route('/stream_proxy')
def stream_proxy():
    if not session.get('logged_in'): return "Unauthorized", 401
    
    url = request.args.get('url')
    if not url: return "No URL", 400
    
    # 1. Forward Headers from iPhone (Crucial for 'Range' support)
    headers = {}
    if 'Range' in request.headers:
        headers['Range'] = request.headers['Range']
    
    try:
        # 2. Make request to YouTube with the Range header
        req = requests.get(url, stream=True, headers=headers)
        
        # 3. Filter headers to pass back (exclude hop-by-hop headers)
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        response_headers = [(name, value) for (name, value) in req.headers.items()
                            if name.lower() not in excluded_headers]
        
        # 4. Create the response
        # Safari expects a 206 Partial Content status if it asked for a Range
        resp = Response(stream_with_context(req.iter_content(chunk_size=8192)),
                        status=req.status_code,
                        headers=response_headers,
                        content_type=req.headers.get('content-type'))
        
        return resp
    except Exception as e:
        print(f"Stream Error: {e}")
        return f"Error: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=4999)