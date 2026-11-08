# Prampa Rivals Menu

A custom Roblox menu mod with dynamic island, music player, and Discord integration.

![Version](https://img.shields.io/badge/version-1.0-purple)
![Platform](https://img.shields.io/badge/platform-Roblox-red)

## Features

### 🎵 Music Player
- **8 Turkish songs** with searchable dropdown menu
- Click to play, click again to restart
- Only one song plays at a time (no overlap)
- Smooth volume control (25% default)
- Sound wave visualization

### 🏝️ Dynamic Island
- **Top-centered HUD** with smooth animations
- **Discord presence** via Lanyard integration
  - Avatar, name, status
  - Online/idle/DND indicators
- **Live stats**: FPS, Ping, Uptime, Clock
- **Draggable** - position it anywhere
- **Liquid dropdown animation** when clicked

### 🎨 UI/UX
- Purple accent theme (#7C5CFF)
- Smooth tween animations
- Search functionality
- Hover effects
- Responsive design

## Installation

1. Download `rivals_menu.luau`
2. Load it in your executor
3. Enjoy!

## Songs

| # | Song Title | Artist |
|---|------------|--------|
| 1 | Panik Atak | UZI |
| 2 | Dönüyo Başım 2.0 | |
| 3 | El clasico | |
| 4 | Fedakar | |
| 5 | Gömün Beni Çukura | |
| 6 | harbiden şekermiş | |
| 7 | Hoşuna mı Gidiyor | |
| 8 | Radyoda Neşet | |

## Configuration

To customize, edit `patch_ue2.py`:

```python
# Your Discord user ID (for presence)
DISCORD_USER_ID = "your_id_here"

# Menu branding
BRAND = "prampa"
MENU_TITLE = "Prampa Menu"

# Accent color (RGB hex)
ACCENT_HEX = "7C5CFF"

# Music volume (0.0 - 1.0)
MUSIC_VOLUME = 0.25

# Add/remove songs
MUSIC_TRACKS = [
    ("Song Title", "filename.ogg"),
    # ...
]
```

Then run:
```bash
python patch_ue2.py
```

## Requirements

- **Executor** with:
  - `writefile` support
  - `getcustomasset` support
  - `getgenv` support
- **Python 3.6+** (for building only)
- **FFmpeg** (for song conversion only)

## Building from Source

See [SETUP.md](SETUP.md) for detailed instructions on:
- Converting songs to OGG
- Rebuilding the menu
- Pushing updates

## Screenshots

### Dynamic Island
![Island Preview](https://via.placeholder.com/800x60/0F0F12/7C5CFF?text=Dynamic+Island)

### Song Picker Dropdown
![Dropdown Preview](https://via.placeholder.com/300x350/0E0E12/7C5CFF?text=Song+Dropdown)

### Sound Waves Animation
![Waves Preview](https://via.placeholder.com/60x20/0F0F12/7C5CFF?text=Waves)

## Technical Details

- **Base**: Unnamed Enhancements v2
- **Language**: Luau (Roblox Lua)
- **Music Loading**: Runtime download + `getcustomasset`
- **Discord Integration**: Lanyard REST API
- **Animation**: TweenService
- **File Size**: ~14.5 MB (includes base menu)

## Credits

- **Base Menu**: Unnamed Enhancements
- **Modifications**: Deepseek + Claude Sonnet
- **Music**: Various Turkish artists
- **Branding**: prampa

## License

This is a mod of proprietary software. Use at your own risk.

## Support

For issues or feature requests, open an issue on GitHub.

---

**Made with 💜 by prampa**
