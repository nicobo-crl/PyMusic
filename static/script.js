const audioPlayer = document.getElementById('audioPlayer');
const playPauseBtn = document.getElementById('playPauseBtn');
const progressBar = document.getElementById('progressBar');
const fpLyricsContainer = document.getElementById('fpLyricsContainer'); 
const volumeSlider = document.getElementById('volumeSlider');
const fpProgressBar = document.getElementById('fpProgressBar');
const fpVolumeSlider = document.getElementById('fpVolumeSlider');

let currentLyrics = []; 
let currentSong = null; 
let playbackQueue = [];
let likedSongsCache = []; 
let ctxSelectedSong = null;

window.onload = async () => {
    try {
        const savedVol = localStorage.getItem('playerVolume');
        if(savedVol !== null) {
            audioPlayer.volume = parseFloat(savedVol);
            volumeSlider.value = savedVol;
            if(fpVolumeSlider) {
                fpVolumeSlider.value = savedVol;
                updateSliderFill(fpVolumeSlider);
            }
        }
        await fetchLikes(); 
        showHome();
        updateQueueUI();
    } catch (e) { console.error(e); }
};

// --- DYNAMIC BACKGROUND COLOR ---
function extractColor(imgSrc) {
    const img = new Image();
    img.crossOrigin = "Anonymous";
    img.src = imgSrc;
    img.onload = function() {
        const canvas = document.createElement('canvas');
        canvas.width = 1; canvas.height = 1;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, 1, 1);
        const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data;
        
        // Brighter gradient logic
        const bg = document.getElementById('fullPlayerBg');
        if(bg) bg.style.background = `radial-gradient(circle at 30% 30%, rgb(${r},${g},${b}), #000)`;
    }
    img.onerror = () => {
        const bg = document.getElementById('fullPlayerBg');
        if(bg) bg.style.background = '#1a1a1a'; 
    }
}

// --- HELPER: Update Slider Fill (iOS Style) ---
function updateSliderFill(el) {
    if(!el) return;
    const val = (el.value - el.min) / (el.max - el.min) * 100;
    el.style.backgroundSize = val + '% 100%';
}

// --- VOLUME CONTROL ---
function handleVolume(vol) {
    audioPlayer.volume = vol;
    localStorage.setItem('playerVolume', vol);
    volumeSlider.value = vol;
    if(fpVolumeSlider) {
        fpVolumeSlider.value = vol;
        updateSliderFill(fpVolumeSlider);
    }
}

volumeSlider.addEventListener('input', (e) => handleVolume(e.target.value));
if(fpVolumeSlider) fpVolumeSlider.addEventListener('input', (e) => handleVolume(e.target.value));


// --- DB LIKES LOGIC ---
async function fetchLikes() {
    try {
        const res = await fetch('/api/likes');
        likedSongsCache = await res.json();
    } catch (e) { console.error("Failed to fetch likes", e); }
}

function getLikedSongs() { return likedSongsCache; }

async function toggleLike(event, songStr) {
    if(event) event.stopPropagation(); 
    const song = typeof songStr === 'string' ? JSON.parse(decodeURIComponent(songStr)) : songStr;
    const idx = likedSongsCache.findIndex(s => s.id === song.id);
    const isLiked = idx !== -1;
    
    if (isLiked) likedSongsCache.splice(idx, 1);
    else {
        likedSongsCache.unshift(song);
        triggerCache(song);
    }
    
    if(event && event.target) {
        event.target.className = isLiked ? "far fa-heart like-btn" : "fas fa-heart liked like-btn";
    }
    updatePlayerLikeBtn();
    if(document.getElementById('nav-library').classList.contains('active')) renderSongList(likedSongsCache);

    await fetch('/api/toggle_like', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({song: song})
    });
}

async function toggleLikeCurrent() {
    if(!currentSong) return;
    await toggleLike(null, currentSong);
}

function updatePlayerLikeBtn() {
    if(!currentSong) return; 
    const is = likedSongsCache.some(s => s.id === currentSong.id);
    const btn = document.getElementById('playerLikeBtn');
    if(btn) btn.className = is ? "fas fa-heart like-btn liked" : "far fa-heart like-btn";
}

// --- CACHING LOGIC ---
async function triggerCache(song) {
    try {
        await fetch('/api/cache_song', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(song)
        });
    } catch (e) { console.error("Cache trigger failed", e); }
}

// --- CONTEXT MENU LOGIC ---
document.addEventListener('click', () => {
    const menu = document.getElementById('contextMenu');
    if(menu) menu.style.display = 'none';
});

function showCtxMenu(e, song) {
    e.preventDefault();
    ctxSelectedSong = song;
    const menu = document.getElementById('contextMenu');
    if(menu) {
        menu.style.display = 'block';
        menu.style.left = `${e.pageX}px`;
        menu.style.top = `${e.pageY}px`;
    }
}
function ctxAddToQueue() { if(ctxSelectedSong) addToQueue(ctxSelectedSong); }
function ctxToggleLike() { if(ctxSelectedSong) toggleLike(null, ctxSelectedSong); }

// --- NAVIGATION ---
function updateNavHighlight(section) {
    document.querySelectorAll('.sidebar li').forEach(li => li.classList.remove('active'));
    const desktopNav = document.getElementById(`nav-${section}`);
    if(desktopNav) desktopNav.classList.add('active');
    
    document.querySelectorAll('.bottom-nav .nav-item').forEach(item => item.classList.remove('active'));
    const icons = {'home':0, 'search':1, 'library':2, 'queue':3};
    const mobItems = document.querySelectorAll('.bottom-nav .nav-item');
    if(mobItems[icons[section]]) mobItems[icons[section]].classList.add('active');
}

function showHome() {
    updateNavHighlight('home');
    document.getElementById('sectionTitle').innerText = "Home";
    const recents = document.getElementById('recentsContainer');
    const recs = document.getElementById('recommendationsContainer');
    const chartT = document.getElementById('chartTitle');
    
    if(recents) recents.style.display = 'block';
    if(recs) recs.style.display = 'block';
    if(chartT) {
        chartT.style.display = 'block';
        chartT.innerText = "Top Charts";
    }
    loadRecents(); loadRecommendations(); loadCharts();
}

function showQueue() {
    updateNavHighlight('queue');
    document.getElementById('sectionTitle').innerText = "Play Queue";
    document.getElementById('recentsContainer').style.display = 'none';
    document.getElementById('recommendationsContainer').style.display = 'none';
    document.getElementById('chartTitle').style.display = 'none';
    renderSongList(playbackQueue, true); 
}

function focusSearch() { updateNavHighlight('search'); document.getElementById('searchInput').focus(); }

async function showFavourites() {
    updateNavHighlight('library');
    document.getElementById('sectionTitle').innerText = "Your Favourites";
    document.getElementById('recentsContainer').style.display = 'none';
    document.getElementById('recommendationsContainer').style.display = 'none';
    document.getElementById('chartTitle').style.display = 'none';
    await fetchLikes();
    renderSongList(likedSongsCache);
}

// --- RECS & RECENTS ---
function getLocalStorageSafe(key) { try { return JSON.parse(localStorage.getItem(key) || '[]'); } catch { return []; } }
function getRecents() { return getLocalStorageSafe('recentSongs'); }
function addToRecents(s){ let r=getRecents(); r=r.filter(x=>x.id!==s.id); r.unshift(s); if(r.length>10)r.pop(); localStorage.setItem('recentSongs',JSON.stringify(r)); }

// --- RENDER LISTS ---
function renderSongList(songs, isQueueView = false) {
    const list = document.getElementById('resultsList');
    list.innerHTML = '';
    
    if (isQueueView && songs.length === 0) { list.innerHTML = '<p style="text-align:center;margin-top:20px;color:#777;">Queue empty.</p>'; return; }
    if (!isQueueView && songs.length === 0) { list.innerHTML = '<p style="padding:20px; color:gray;">No songs found.</p>'; return; }
    
    const likedSongs = getLikedSongs();

    songs.forEach((song, index) => {
        const isLiked = likedSongs.some(s => s.id === song.id);
        const heartClass = isLiked ? "fas fa-heart liked" : "far fa-heart";
        const item = document.createElement('div');
        item.className = 'song-item';
        item.oncontextmenu = (e) => showCtxMenu(e, song);

        let queueBtn = '';
        const songStr = encodeURIComponent(JSON.stringify(song));
        
        if (isQueueView) {
            queueBtn = `<i class="fas fa-trash like-btn" onclick="removeFromQueue(${index}, event)"></i>`;
        } else {
            queueBtn = `<i class="fas fa-list-ul like-btn" onclick="addToQueue(JSON.parse(decodeURIComponent('${songStr}')), event)"></i>`;
        }

        const cachedIcon = song.cached ? `<i class="fas fa-check-circle download-icon" title="Downloaded"></i>` : ``;

        item.innerHTML = `
            <img src="${song.cover}" class="song-list-cover" loading="lazy">
            <div class="song-info">
                <div class="song-title">
                    ${song.title}
                    ${cachedIcon}
                </div>
                <div class="song-artist">${song.artist}</div>
            </div>
            <div class="actions">
                ${queueBtn}
                <i class="${heartClass} like-btn" onclick="toggleLike(event, '${songStr}')"></i>
            </div>
        `;
        item.onclick = (e) => { if (!e.target.classList.contains('like-btn')) loadSong(song); };
        list.appendChild(item);
    });
}

// --- QUEUE & PLAYBACK ---
function addToQueue(song, event) {
    if(event) event.stopPropagation();
    playbackQueue.push(song); updateQueueUI();
}
function updateQueueUI() {
    const count = document.getElementById('queueCount');
    if(!count) return;
    if(playbackQueue.length > 0) { count.style.display='inline-block'; count.innerText=playbackQueue.length; }
    else count.style.display='none';
}
function playNextInQueue(isUserAction = false) {
    if (playbackQueue.length > 0) {
        const nextSong = playbackQueue.shift();
        updateQueueUI(); loadSong(nextSong);
        if(document.getElementById('nav-queue').classList.contains('active')) renderSongList(playbackQueue, true);
    } else { if(!isUserAction) playAutoRecommendation(); }
}
function removeFromQueue(index, event) {
    if(event) event.stopPropagation();
    playbackQueue.splice(index, 1); updateQueueUI(); renderSongList(playbackQueue, true);
}

// --- FETCHERS ---
async function loadCharts() { 
    const list = document.getElementById('resultsList'); 
    list.innerHTML='<div class="loading-text" style="padding:20px;">Loading Charts...</div>'; 
    try{ const res=await fetch('/chart'); renderSongList(await res.json()); }catch(e){} 
}
async function performSearch() { 
    updateNavHighlight('search'); 
    const q=document.getElementById('searchInput').value; 
    if(!q)return; 
    document.getElementById('recentsContainer').style.display='none'; 
    document.getElementById('recommendationsContainer').style.display='none'; 
    document.getElementById('chartTitle').style.display='none'; 
    document.getElementById('sectionTitle').innerText="Search Results"; 
    const list=document.getElementById('resultsList'); 
    list.innerHTML='<div class="loading-text" style="padding:20px;">Searching...</div>'; 
    try{ const res=await fetch(`/search?q=${encodeURIComponent(q)}`); renderSongList(await res.json()); }catch(e){} 
}

// --- RECOMMENDATIONS ---
async function loadRecents(){ 
    const r=getRecents(); 
    const c=document.getElementById('recentsList'); 
    const w=document.getElementById('recentsContainer'); 
    if(!c || !w) return;
    if(r.length===0){w.style.display='none';return;} 
    w.style.display='block'; 
    c.innerHTML=''; 
    r.forEach(s=>{ 
        const d=document.createElement('div'); 
        d.className='recent-card'; 
        d.innerHTML=`<img src="${s.cover}"><div class="recent-title">${s.title}</div>`; 
        d.oncontextmenu = (e) => showCtxMenu(e, s); 
        d.onclick=()=>loadSong(s); 
        c.appendChild(d); 
    }); 
}
async function loadRecommendations() {
    const recents = getRecents(); 
    const container = document.getElementById('recommendationsContainer'); 
    const list = document.getElementById('recommendationsList');
    if(!container || !list) return;

    if(recents.length === 0 || !recents.find(s=>s.artist_id)) { container.style.display = 'none'; return; }
    try { 
        const res = await fetch(`/recommend?artist_id=${recents.find(s=>s.artist_id).artist_id}`); 
        const data = await res.json(); 
        if(data.length === 0) { container.style.display = 'none'; return; } 
        container.style.display = 'block'; 
        list.innerHTML = ''; 
        data.forEach(song => { 
            const div = document.createElement('div'); 
            div.className = 'recent-card'; 
            div.innerHTML = `<img src="${song.cover}"><div class="recent-title">${song.title}</div>`; 
            div.oncontextmenu = (e) => showCtxMenu(e, song); 
            div.onclick = () => loadSong(song); 
            list.appendChild(div); 
        }); 
    } catch(e) { container.style.display = 'none'; }
}
async function playAutoRecommendation() { 
    if(!currentSong || !currentSong.artist_id) return; 
    try { 
        const res = await fetch(`/recommend?artist_id=${currentSong.artist_id}`); 
        const data = await res.json(); 
        if(data && data.length > 0) loadSong(data[Math.floor(Math.random()*data.length)]); 
    } catch(e) {} 
}

// --- PLAYER & LYRICS ---
audioPlayer.onended = () => playNextInQueue();
async function loadSong(song) {
    currentSong = song;
    addToRecents(song);
    
    const isLiked = likedSongsCache.some(s => s.id === song.id);
    if (isLiked) triggerCache(song);

    // Mini Player UI
    document.getElementById('trackName').innerText = song.title;
    document.getElementById('artistName').innerText = "Loading...";
    document.getElementById('albumArt').src = song.cover_xl;
    
    // Full Player UI
    document.getElementById('fpTrackName').innerText = song.title;
    document.getElementById('fpArtistName').innerText = "Loading...";
    document.getElementById('fpAlbumArt').src = song.cover_xl;
    
    // Set Dynamic Background
    extractColor(song.cover_xl);

    updatePlayerLikeBtn();
    
    // Reset Lyrics (Full Player)
    if(fpLyricsContainer) fpLyricsContainer.innerHTML = '<div style="margin-top:50px; text-align:center; color:rgba(255,255,255,0.6);">Searching Lyrics...</div>';
    
    currentLyrics = []; 
    updatePlayButton(false);

    if ('mediaSession' in navigator) {
        navigator.mediaSession.metadata = new MediaMetadata({ title: song.title, artist: song.artist, album: song.album, artwork: [{ src: song.cover_xl, sizes: '512x512', type: 'image/jpeg' }] });
        navigator.mediaSession.setActionHandler('nexttrack', () => playNextInQueue(true));
        navigator.mediaSession.setActionHandler('previoustrack', () => { audioPlayer.currentTime = 0; });
        navigator.mediaSession.setActionHandler('play', togglePlay);
        navigator.mediaSession.setActionHandler('pause', togglePlay);
    }

    try {
        const audioRes = await fetch(`/play?artist=${encodeURIComponent(song.artist)}&title=${encodeURIComponent(song.title)}&id=${song.id}`);
        const audioData = await audioRes.json();
        
        if(audioData.error) throw new Error("Song not found");
        
        document.getElementById('artistName').innerText = song.artist;
        document.getElementById('fpArtistName').innerText = song.artist;
        
        if (audioData.source === 'local') {
            console.log("Playing from cache");
            audioPlayer.src = audioData.url; 
        } else {
            console.log("Streaming from web");
            audioPlayer.src = `/stream_proxy?url=${encodeURIComponent(audioData.url)}`;
        }
        
        audioPlayer.play().catch(e => console.log("Auto-play prevented", e));
        
        const lyricsRes = await fetch(`/lyrics?artist=${encodeURIComponent(song.artist)}&title=${encodeURIComponent(song.title)}`);
        const lyData = await lyricsRes.json();
        if (lyData.text) { 
            if(lyData.type === 'synced') {
                parseLyrics(lyData.text); 
                renderLyrics(); 
            } else {
                const plainHtml = `<div style="white-space: pre-wrap; padding: 20px; text-align:center; line-height: 1.6;">${lyData.text}</div>`;
                if(fpLyricsContainer) fpLyricsContainer.innerHTML = plainHtml;
            }
        }
        else {
            const errHtml = '<div style="padding: 50px; opacity: 0.5; text-align:center;">Lyrics not available.</div>';
            if(fpLyricsContainer) fpLyricsContainer.innerHTML = errHtml;
        }
    } catch (e) {
        document.getElementById('artistName').innerText = song.artist;
        document.getElementById('fpArtistName').innerText = song.artist;
        console.error(e);
    }
}

function parseLyrics(s){ 
    const lines=s.split('\n'); 
    const regex=/^\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)/; 
    currentLyrics=[]; 
    lines.forEach(line=>{
        const match=line.match(regex); 
        if(match && match[4].trim()) {
            const min = parseInt(match[1]);
            const sec = parseInt(match[2]);
            const ms = parseFloat("0." + match[3]);
            currentLyrics.push({time: min*60 + sec + ms, text: match[4].trim()});
        }
    }); 
}

function renderLyrics(){ 
    if(!fpLyricsContainer) return;
    const container = fpLyricsContainer;
    container.innerHTML = '';
    const spacerTop = document.createElement('div'); spacerTop.style.height = "40vh"; container.appendChild(spacerTop);
    currentLyrics.forEach((l,i)=>{
        const p=document.createElement('p'); 
        p.innerText=l.text; 
        p.id=`line-${i}`; 
        p.className='lyric-line'; 
        p.onclick=()=>{audioPlayer.currentTime=l.time}; 
        container.appendChild(p);
    }); 
    const spacerBot = document.createElement('div'); spacerBot.style.height = "40vh"; container.appendChild(spacerBot);
}

function syncLyrics(t){ 
    if(!currentLyrics.length) return; 
    let idx = -1; 
    for(let i=0; i<currentLyrics.length; i++){
        if(t >= currentLyrics[i].time) idx = i;
        else break;
    } 
    
    if(idx !== -1 && fpLyricsContainer){
        const container = fpLyricsContainer;
        if(container.offsetParent === null) return;
        
        container.querySelectorAll('.lyric-line').forEach(e => e.classList.remove('active')); 
        const el = document.getElementById(`line-${idx}`); 
        if(el){
            el.classList.add('active'); 
            const scrollPos = el.offsetTop - (container.clientHeight / 2) + (el.clientHeight / 2);
            container.scrollTo({ top: scrollPos, behavior: 'smooth' });
        }
    } 
}

audioPlayer.addEventListener('playing', () => { updatePlayButton(true); });
audioPlayer.addEventListener('pause', () => { updatePlayButton(false); });

function togglePlay() { 
    if (audioPlayer.paused && audioPlayer.src) audioPlayer.play(); 
    else audioPlayer.pause(); 
}

function updatePlayButton(p) { 
    const html = p ? '<i class="fas fa-circle-pause" style="font-size:38px;"></i>' : '<i class="fas fa-circle-play" style="font-size:38px;"></i>';
    playPauseBtn.innerHTML = html;
    
    const fpHtml = p ? '<i class="fas fa-circle-pause"></i>' : '<i class="fas fa-circle-play"></i>';
    const fpBtn = document.getElementById('fpPlayBtn');
    if(fpBtn) fpBtn.innerHTML = fpHtml;
}

audioPlayer.ontimeupdate = () => { 
    if (audioPlayer.duration) { 
        const pct = (audioPlayer.currentTime / audioPlayer.duration) * 100;
        
        progressBar.value = pct; 
        document.getElementById('currentTime').innerText = formatTime(audioPlayer.currentTime); 
        document.getElementById('duration').innerText = formatTime(audioPlayer.duration); 
        
        if(fpProgressBar) {
            fpProgressBar.value = pct;
            updateSliderFill(fpProgressBar);
            document.getElementById('fpCurrentTime').innerText = formatTime(audioPlayer.currentTime);
            document.getElementById('fpDuration').innerText = formatTime(audioPlayer.duration);
        }

        syncLyrics(audioPlayer.currentTime); 
    } 
};

progressBar.oninput = () => { audioPlayer.currentTime = (progressBar.value / 100) * audioPlayer.duration; }
if(fpProgressBar) {
    fpProgressBar.oninput = () => { 
        audioPlayer.currentTime = (fpProgressBar.value / 100) * audioPlayer.duration; 
        updateSliderFill(fpProgressBar);
    }
}

function formatTime(s) { const m=Math.floor(s/60), sc=Math.floor(s%60); return `${m}:${sc<10?'0':''}${sc}`; }
document.getElementById('searchInput').addEventListener("keypress", (e) => { if (e.key === "Enter") performSearch(); });

// --- FULL SCREEN PLAYER TOGGLE ---
function toggleNowPlayingModal() {
    const player = document.getElementById('fullPlayer');
    if(!player) return;
    player.classList.add('active');
}

function closeFullPlayer() {
    const player = document.getElementById('fullPlayer');
    if(player) player.classList.remove('active');
}

function toggleMobileLyrics() {
    const panel = document.getElementById('fpLyricsView');
    panel.classList.toggle('mobile-active');
}

document.querySelector('.now-playing').addEventListener('click', () => {
    if(currentSong) toggleNowPlayingModal();
});