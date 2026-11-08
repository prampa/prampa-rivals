#!/usr/bin/env python3
"""Convert webm songs to OGG format for Roblox"""

import subprocess
import sys
from pathlib import Path

SONGS_DIR = Path("songs")
OUTPUT_DIR = Path(".")

# Song mapping: webm file -> output ogg name
SONGS = {
    "Dönüyo Başım 2.0 [5Kf_KpOtp-U].webm": "song1.ogg",
    "El clasico [BLDpFXx6ovk].webm": "song2.ogg",
    "Fedakar [Myb-MXbjQLE].webm": "song3.ogg",
    "Gömün Beni Çukura [RdD6Ev-oBQo].webm": "song4.ogg",
    "harbiden şekermiş [HzR58sSdPuE].webm": "song5.ogg",
    "Hoşuna mı Gidiyor [4Azfzlb-hG8].webm": "song6.ogg",
    "Radyoda Neşet [cXmQgovnvxg].webm": "song7.ogg",
}

def check_ffmpeg():
    """Check if ffmpeg is available"""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def convert_song(input_path, output_path):
    """Convert a single webm to OGG"""
    print(f"Converting {input_path.name} -> {output_path.name}...")
    
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-i", str(input_path),
                "-c:a", "libvorbis",
                "-q:a", "5",
                "-y",  # overwrite
                str(output_path)
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"  ✓ {output_path.name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed: {e}")
        return False

def main():
    if not check_ffmpeg():
        print("ERROR: ffmpeg not found!")
        print("Download from: https://ffmpeg.org/download.html")
        print("Or use: winget install ffmpeg")
        return 1
    
    if not SONGS_DIR.exists():
        print(f"ERROR: {SONGS_DIR} directory not found!")
        return 1
    
    success_count = 0
    for webm_name, ogg_name in SONGS.items():
        input_path = SONGS_DIR / webm_name
        output_path = OUTPUT_DIR / ogg_name
        
        if not input_path.exists():
            print(f"SKIP: {webm_name} not found")
            continue
        
        if convert_song(input_path, output_path):
            success_count += 1
    
    print(f"\nConverted {success_count}/{len(SONGS)} songs")
    return 0

if __name__ == "__main__":
    sys.exit(main())
