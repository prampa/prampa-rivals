# Prampa Rivals Setup Instructions

## Current Status

✅ **DONE**:
- Dynamic island with liquid dropdown animation implemented
- Song search functionality with dropdown menu (12 songs max)
- Click song to play, click again to restart (no double playing)
- Sound waves visualization inside the dynamic island
- Proper song handling (only one song plays at a time)
- `rivals_menu.luau` generated and ready

❌ **TODO**:
- Convert webm songs to OGG format
- Push OGG files to GitHub

---

## Step 1: Install FFmpeg

You need ffmpeg to convert the webm songs to OGG format (Roblox requires MP3 or OGG).

### Option A: Download Manually
1. Go to https://ffmpeg.org/download.html
2. Download the Windows build
3. Extract and add to PATH

### Option B: Use Chocolatey
```powershell
choco install ffmpeg
```

### Option C: Use winget (Windows 11)
```powershell
winget install ffmpeg
```

---

## Step 2: Convert Songs to OGG

Once ffmpeg is installed, run the conversion script:

```powershell
python convert_songs.py
```

This will convert all songs in the `songs/` folder to OGG format:
- `songs/Dönüyo Başım 2.0 [5Kf_KpOtp-U].webm` → `song1.ogg`
- `songs/El clasico [BLDpFXx6ovk].webm` → `song2.ogg`
- `songs/Fedakar [Myb-MXbjQLE].webm` → `song3.ogg`
- `songs/Gömün Beni Çukura [RdD6Ev-oBQo].webm` → `song4.ogg`
- `songs/harbiden şekermiş [HzR58sSdPuE].webm` → `song5.ogg`
- `songs/Hoşuna mı Gidiyor [4Azfzlb-hG8].webm` → `song6.ogg`
- `songs/Radyoda Neşet [cXmQgovnvxg].webm` → `song7.ogg`

**Note**: `song.ogg` (Panik Atak by UZI) should already exist or needs to be converted separately.

---

## Step 3: Push to GitHub

### Create/Update GitHub Repository

1. Create a new repo on GitHub named `prampa-rivals` (or use existing)
2. Add it as remote:

```powershell
git remote add origin https://github.com/prampa/prampa-rivals.git
```

3. Add the OGG files:

```powershell
git add song.ogg song1.ogg song2.ogg song3.ogg song4.ogg song5.ogg song6.ogg song7.ogg
git add rivals_menu.luau
git commit -m "Add converted OGG songs and updated menu"
git branch -M main
git push -u origin main
```

---

## Song Configuration

The songs are configured in `patch_ue2.py`:

```python
MUSIC_TRACKS = [
    ("Panik Atak", "song.ogg"),           # Panik Atak by UZI
    ("Dönüyo Başım 2.0", "song1.ogg"),
    ("El clasico", "song2.ogg"),
    ("Fedakar", "song3.ogg"),
    ("Gömün Beni Çukura", "song4.ogg"),
    ("harbiden şekermiş", "song5.ogg"),
    ("Hoşuna mı Gidiyor", "song6.ogg"),
    ("Radyoda Neşet", "song7.ogg"),
]
```

Song names are extracted from filenames. If you want artist names, edit the tuples in `MUSIC_TRACKS`.

---

## Features Implemented

### Dynamic Island
- Positioned at top center of screen (2px down)
- Shows:
  - Discord avatar/name/status (via Lanyard)
  - FPS counter
  - Ping (MS)
  - Session uptime
  - Local clock
- Draggable
- Collapsible with liquid animation

### Dropdown Menu
- Click island to open animated dropdown
- Search bar to filter songs
- List of 8 songs (max 12 supported)
- Click song name to play
- Click again to restart from 0:00
- Only one song plays at a time
- Sound waves animate inside island when playing

### Animations
- Liquid water effect when opening dropdown (bloom/ripple)
- Sound waves next to/inside dynamic island
- Smooth tween animations (TweenService)
- Hover effects on song rows

---

## File Structure

```
C:\RivalsTesting\
├── songs/                      # Original webm files
│   ├── Dönüyo Başım 2.0 [5Kf_KpOtp-U].webm
│   ├── El clasico [BLDpFXx6ovk].webm
│   ├── Fedakar [Myb-MXbjQLE].webm
│   ├── Gömün Beni Çukura [RdD6Ev-oBQo].webm
│   ├── harbiden şekermiş [HzR58sSdPuE].webm
│   ├── Hoşuna mı Gidiyor [4Azfzlb-hG8].webm
│   └── Radyoda Neşet [cXmQgovnvxg].webm
├── song.ogg - song7.ogg        # Converted OGG files (to be generated)
├── patch_ue2.py                # Patcher script
├── convert_songs.py            # Song conversion script
├── rivals_menu.luau            # Generated menu (ready to use)
├── ue-v2-cracked.luau.txt      # Source
└── ue-v2-modified.luau.txt     # Patched output
```

---

## Troubleshooting

### "unsupported file format" error in Roblox
- Roblox only supports MP3 and OGG Vorbis
- `.webm` files with Opus audio won't work
- Make sure you convert with: `ffmpeg -i in.webm -c:a libvorbis -q:a 5 out.ogg`

### Songs not loading
- Check that OGG files are pushed to GitHub
- Verify the URL is correct in `patch_ue2.py`:
  ```python
  MUSIC_BASE = "https://raw.githubusercontent.com/prampa/prampa-rivals/main/"
  ```
- Make sure the executor supports `writefile` and `getcustomasset`

### Dropdown not opening
- Check executor console for errors
- Make sure the island is visible at the top of screen
- Try clicking directly on the island (not labels)

---

## Next Steps After Setup

1. ✅ Install ffmpeg
2. ✅ Run `python convert_songs.py`
3. ✅ Verify `.ogg` files are created
4. ✅ Push to GitHub
5. ✅ Test in-game

---

## Credits

- Base: Unnamed Enhancements v2
- Dynamic Island & Song Picker: Deepseek + Claude
- Music: Various Turkish artists
