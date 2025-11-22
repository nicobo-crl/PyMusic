from flask import Flask, render_template, request, jsonify, Response, stream_with_context, session, redirect, url_for
import yt_dlp
import requests
import re
import secrets
import random

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
                    'artist_id': item['artist']['id'], # NEEDED FOR RECOMMENDATIONS
                    'album': item['album']['title'],
                    'cover': item['album']['cover_medium'], 
                    'cover_xl': item['album']['cover_xl'],
                    'duration': item['duration']
                })
        return songs
    except Exception as e:
        return []

def get_recommendations(artist_id):
    """
    Fetches tracks from similar artists.
    """
    try:
        # 1. Get Related Artists
        rel_url = f"https://api.deezer.com/artist/{artist_id}/related"
        rel_data = requests.get(rel_url).json()
        
        songs = []
        artists_to_check = []
        
        # Add the original artist to the mix
        artists_to_check.append(artist_id)
        
        # Add up to 4 related artists
        if 'data' in rel_data:
            for art in rel_data['data'][:4]:
                artists_to_check.append(art['id'])
        
        # 2. Get Top Tracks for these artists
        for aid in artists_to_check:
            top_url = f"https://api.deezer.com/artist/{aid}/top?limit=3"
            top_data = requests.get(top_url).json()
            if 'data' in top_data:
                for item in top_data['data']:
                    songs.append({
                        'id': item['id'],
                        'title': item['title'],
                        'artist': item['artist']['name'],
                        'artist_id': item['artist']['id'],
                        'album': item['album']['title'],
                        'cover': item['album']['cover_medium'], 
                        'cover_xl': item['album']['cover_xl'],
                        'duration': item['duration']
                    })
        
        # Shuffle to make it feel like a radio
        random.shuffle(songs)
        return songs
    except Exception as e:
        print(f"Rec Error: {e}")
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
                    'artist_id': item['artist']['id'],
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
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/best', # iPhone Fix
        'quiet': True,
        'noplaylist': True,
        'geo_bypass': True,
        'source_address': '0.0.0.0',
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

@app.route('/recommend')
def recommend():
    if not session.get('logged_in'): return jsonify([])
    artist_id = request.args.get('artist_id')
    if not artist_id: return jsonify([])
    return jsonify(get_recommendations(artist_id))

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
    
    headers = {}
    if 'Range' in request.headers:
        headers['Range'] = request.headers['Range']
    
    try:
        req = requests.get(url, stream=True, headers=headers)
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        response_headers = [(name, value) for (name, value) in req.headers.items()
                            if name.lower() not in excluded_headers]
        return Response(stream_with_context(req.iter_content(chunk_size=8192)),
                        status=req.status_code,
                        headers=response_headers,
                        content_type=req.headers.get('content-type'))
    except Exception as e:
        return f"Error: {e}", 500

if __name__ == '__main__':
    # CHANGED PORT TO 499
    # Note: On Linux/Mac, ports < 1024 require sudo. On Windows, this is fine.
    app.run(host='0.0.0.0', debug=True, port=4999)