#!/usr/bin/env python3
import shutil
from pathlib import Path

songs = Path("songs")
mapping = {
    "Dönüyo Başım 2.0 [5Kf_KpOtp-U].webm": "song1.ogg",
    "El clasico [BLDpFXx6ovk].webm": "song2.ogg",
    "Fedakar [Myb-MXbjQLE].webm": "song3.ogg",
    "Gömün Beni Çukura [RdD6Ev-oBQo].webm": "song4.ogg",
    "harbiden şekermiş [HzR58sSdPuE].webm": "song5.ogg",
    "Hoşuna mı Gidiyor [4Azfzlb-hG8].webm": "song6.ogg",
    "Radyoda Neşet [cXmQgovnvxg].webm": "song7.ogg",
}

for src, dst in mapping.items():
    src_path = songs / src
    dst_path = Path(dst)
    if src_path.exists():
        shutil.copy(src_path, dst_path)
        print(f"✓ {dst}")
    else:
        print(f"✗ {src} not found")

print("\nDone. Note: Roblox might reject these because webm != ogg, but worth a shot.")
