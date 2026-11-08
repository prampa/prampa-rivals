#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_ue2.py - prampa build
===========================

Builds ``ue-v2-modified.luau.txt`` from ``ue-v2-cracked.luau.txt``.

What it changes
---------------
1. Rebrand
   - removes the ``--!nocheck`` / ``--!native`` directives
   - removes the huge ASCII-art banner comment at the top
   - replaces the Korean "free script" console banner with a branded one
   - renames the shared-env key ``Unnamed Enhancements - .gg/enhancements``
     to BRAND (both occurrences: the rawget guard and the assignment)

2. Title
   The two serialized constants ``[3166]`` / ``[7454]`` holding
   ``Unnamed Enhancements - .gg/enhancements`` are rewritten to MENU_TITLE.

3. Addon block (injected before the final ``return runApplication()``)
   - custom menu title (+ runtime fallback if the constants ever move)
   - "dynamic island" spawned centred at the top of the screen, 2 px down:
     Discord avatar / name / presence, FPS, ping, session uptime, local clock
   - click the island to open an animated, searchable song picker
   - music waves light up inside the island while a track is playing
   - optional corner watermark (wordmark only)
   - looping background music at 25 % volume, one track at a time

Music
-----
Roblox cannot stream an arbitrary https URL from a ``Sound``, so every track is
downloaded at runtime, written to the executor workspace and turned into an
asset with ``getcustomasset``.  That needs an executor with ``writefile`` and
``getcustomasset``; tracks are cached per URL afterwards.

MUSIC_TRACKS is a list of ``(title, file)`` pairs, max 12.  ``file`` is either
a name inside MUSIC_BASE, a full http(s) URL, or an ``rbxassetid://`` id.
Clicking a title plays it, clicking it again restarts it from 0:00, and
selecting another one stops the previous track - there is a single ``Sound``
instance, so tracks can never overlap.

Set MUSIC_VOLUME to 1.0 for full volume; 0.25 is a quarter.

Roblox decodes MP3 (CBR/VBR) and OGG Vorbis only.  A ``.webm``/``.opus`` file
renamed to ``.mp3`` - what yt-dlp and most "youtube to mp3" sites hand you -
downloads fine but the client rejects it with

    Failed to load sound rbxasset://.../prampa_music_x.mp3: unsupported file format

Convert it first:

    ffmpeg -i in.webm -c:a libvorbis -q:a 5 out.ogg

Discord presence
----------------
Presence is not available from Discord's REST API and using a user token would
mean running a self-bot.  This uses Lanyard instead:

    1. join  https://discord.gg/lanyard  once
    2. put your numeric user ID in DISCORD_USER_ID

Usage
-----
    python patch_ue2.py
    python patch_ue2.py <source.txt> <output.txt>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# EDIT THESE
# --------------------------------------------------------------------------

# Everything branded uses this: env key, watermark, console banner.
BRAND = "prampa"

MENU_TITLE = "Prampa Menu"

# Your numeric Discord user ID (17-20 digits), for Lanyard presence.
# Right click your name in Discord with Developer Mode on -> Copy User ID.
DISCORD_USER_ID = "1453886966599913708"

# Optional: force the displayed name instead of your Discord display name.
# Leave "" to use whatever Lanyard reports.
DISCORD_NAME = ""

# Island accent colour, RRGGBB.
ACCENT_HEX = "7C5CFF"

# Small "prampa" tag in the bottom-right corner.
SHOW_WATERMARK = True

# --------------------------------------------------------------------------
# background music / song picker
# --------------------------------------------------------------------------

# Folder the track files live in (must end with a slash).  A track's `file`
# may also be a full http(s) URL or an "rbxassetid://..." id, in which case
# this prefix is ignored.
MUSIC_BASE = "https://raw.githubusercontent.com/prampa/prampa-rivals/main/"

# (display title, file) - shown in the island's searchable dropdown.
# At most 12 tracks.  Keep the .ogg files in the same folder as MUSIC_BASE.
MUSIC_TRACKS = [
    ("Panik Atak", "song.ogg"),
    ("Dönüyo Başım 2.0", "song1.ogg"),
    ("El clasico", "song2.ogg"),
    ("Fedakar", "song3.ogg"),
    ("Gömün Beni Çukura", "song4.ogg"),
    ("harbiden şekermiş", "song5.ogg"),
    ("Hoşuna mı Gidiyor", "song6.ogg"),
    ("Radyoda Neşet", "song7.ogg"),
]

# 0.25 = 25 % volume.
MUSIC_VOLUME = 0.25

# --------------------------------------------------------------------------
# internals
# --------------------------------------------------------------------------

OLD_TITLE = "Unnamed Enhancements - .gg/enhancements"

SOURCE_NAME = "ue-v2-cracked.luau.txt"
OUTPUT_NAME = "ue-v2-modified.luau.txt"

# Same build, written under the name used on GitHub, so no manual copy is
# needed.  Set to "" to disable.
ALIAS_NAME = "rivals_menu.luau"

MARKER = "-- >>> prampa addon (patched by patch_ue2.py) >>>"
STALE_MARKERS = (
    "-- >>> UE v2 addon (patched by patch_ue2.py) >>>",
    MARKER,
)

PLACEHOLDER_ID = "[YOUR USER ID HERE]"
PLACEHOLDER_TITLE = "[YOUR TITLE HERE]"

# classic user token, and mfa tokens
TOKEN_RE = re.compile(
    r"^(?:mfa\.[A-Za-z0-9_-]{60,}"
    r"|[A-Za-z0-9_-]{20,32}\.[A-Za-z0-9_-]{5,10}\.[A-Za-z0-9_-]{25,60})$"
)


def lua_str(value: str) -> str:
    """Render *value* as a single-quoted Luau string literal."""
    out = (
        value.replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\r", "\\r")
        .replace("\n", "\\n")
        .replace("\t", "\\t")
        .replace("\x00", "")
    )
    return "'" + out + "'"


def fail(message: str) -> "NoReturn":
    print("error: " + message, file=sys.stderr)
    raise SystemExit(1)


# The injected Luau block.  @@...@@ are replaced with already-quoted literals.
ADDON_TEMPLATE = r"""
-- >>> prampa addon (patched by patch_ue2.py) >>>
-- Menu title, branded HUD, Discord presence (Lanyard), FPS / ping, song picker.
do
    local BRAND = @@BRAND@@
    local ADDON_TITLE = @@TITLE@@
    local DISCORD_ID = @@DISCORD_ID@@
    local DISCORD_NAME_OVERRIDE = @@DISCORD_NAME@@
    local ACCENT = @@ACCENT@@
    local SHOW_WATERMARK = @@WATERMARK@@
    local MUSIC_BASE = @@MUSIC_BASE@@
    local MUSIC_TRACKS = @@MUSIC_TRACKS@@
    local MUSIC_VOLUME = @@MUSIC_VOLUME@@
    local POLL_SECONDS = 20

    local env = getgenv and getgenv() or _G
    local Players = game:GetService('Players')
    local RunService = game:GetService('RunService')
    local UserInputService = game:GetService('UserInputService')
    local HttpService = game:GetService('HttpService')
    local SoundService = game:GetService('SoundService')
    local TweenService = game:GetService('TweenService')
    local LocalPlayer = Players.LocalPlayer

    local ISLAND_NAME = 'prampa_HUD'
    local WATERMARK_NAME = 'prampa_Watermark'
    local LANYARD = 'https://api.lanyard.rest/v1/users/'
    local CDN = 'https://cdn.discordapp.com/'
    local CYAN = Color3.fromRGB(0, 208, 255)

    local STATUS_COLORS = {
        online = Color3.fromRGB(35, 165, 90),
        idle = Color3.fromRGB(240, 178, 50),
        dnd = Color3.fromRGB(242, 63, 67),
        offline = Color3.fromRGB(128, 132, 142),
        unknown = Color3.fromRGB(150, 150, 160),
    }

    -----------------------------------------------------------------------
    -- small helpers
    -----------------------------------------------------------------------

    local function guiParent()
        if type(gethui) == 'function' then
            local ok, hui = pcall(gethui)
            if ok and hui then
                return hui
            end
        end

        local ok, core = pcall(function()
            return game:GetService('CoreGui')
        end)
        if ok and core then
            return core
        end

        return LocalPlayer:WaitForChild('PlayerGui')
    end

    local function httpGet(url)
        local ok, body = pcall(function()
            return game:HttpGet(url)
        end)
        if ok and type(body) == 'string' and body ~= '' then
            return body
        end

        if type(request) == 'function' then
            local ok2, res = pcall(request, { Url = url, Method = 'GET' })
            if ok2 and type(res) == 'table' and type(res.Body) == 'string' then
                return res.Body
            end
        end

        if type(syn) == 'table' and type(syn.request) == 'function' then
            local ok3, res = pcall(syn.request, { Url = url, Method = 'GET' })
            if ok3 and type(res) == 'table' and type(res.Body) == 'string' then
                return res.Body
            end
        end

        return nil
    end

    local function looksLikeAudio(body)
        if type(body) ~= 'string' or #body < 12 then
            return false
        end

        if body:sub(1, 4) == 'OggS' then
            return true
        end
        if body:sub(1, 4) == 'RIFF' then
            return true
        end
        if body:sub(1, 3) == 'ID3' then
            return true
        end

        -- bare MPEG frame sync: 0xFF followed by 111xxxxx
        return body:byte(1) == 0xFF and body:byte(2) >= 0xE0
    end

    local function assetFromUrl(url, fileName, expectAudio)
        if type(getcustomasset) ~= 'function' or type(writefile) ~= 'function' then
            return nil
        end

        -- reuse a file that is already in the workspace; the names passed in
        -- are content-addressed (avatar hash / music url hash), so a cache hit
        -- can never serve a stale image or song
        local cached = false
        if type(isfile) == 'function' then
            local okFile, exists = pcall(isfile, fileName)
            cached = okFile and exists == true
        end

        if not cached then
            local body = httpGet(url)
            if type(body) ~= 'string' or body == '' then
                return nil
            end

            if expectAudio and not looksLikeAudio(body) then
                warn(
                    '[' .. BRAND .. '] ' .. fileName .. ' is not MP3/OGG/WAV '
                        .. '(a .webm/.opus file renamed to .mp3 is the usual '
                        .. 'cause). Convert it with: ffmpeg -i in.webm -c:a '
                        .. 'libvorbis out.ogg'
                )
                return nil
            end

            if not pcall(writefile, fileName, body) then
                return nil
            end
        end

        local ok, asset = pcall(getcustomasset, fileName)
        if ok and type(asset) == 'string' and asset ~= '' then
            return asset
        end

        return nil
    end

    local statsService
    local function readPing()
        if not statsService then
            local ok, service = pcall(function()
                return game:GetService('Stats')
            end)
            if ok then
                statsService = service
            end
        end
        if not statsService then
            return 0
        end

        local ok, item = pcall(function()
            return statsService.Network.ServerStatsItem['Data Ping']
        end)
        if not ok or not item then
            return 0
        end

        local ok2, value = pcall(function()
            return item:GetValue()
        end)
        if ok2 and type(value) == 'number' then
            return value
        end

        return 0
    end

    local function colorHex(color)
        return string.format(
            '#%02X%02X%02X',
            math.floor(color.R * 255 + 0.5),
            math.floor(color.G * 255 + 0.5),
            math.floor(color.B * 255 + 0.5)
        )
    end

    local function escapeRich(text)
        local value = tostring(text)
        value = value:gsub('&', '&amp;')
        value = value:gsub('<', '&lt;')
        value = value:gsub('>', '&gt;')
        return value
    end

    local function formatUptime(seconds)
        seconds = math.max(0, math.floor(seconds))

        local hours = math.floor(seconds / 3600)
        local minutes = math.floor((seconds % 3600) / 60)
        local secs = seconds % 60

        if hours > 0 then
            return string.format('%dh %02dm', hours, minutes)
        end

        return string.format('%02d:%02d', minutes, secs)
    end

    local function localClock()
        local ok, value = pcall(function()
            return DateTime.now():ToLocalTime():FormatLocalTime('HH:mm', 'en-us')
        end)
        if ok and type(value) == 'string' and value ~= '' then
            return value
        end

        local ok2, fallback = pcall(function()
            return os.date('%H:%M')
        end)
        if ok2 and type(fallback) == 'string' then
            return fallback
        end

        return '--:--'
    end

    -----------------------------------------------------------------------
    -- menu title
    -----------------------------------------------------------------------

    local function isMenuTitle(text)
        if type(text) ~= 'string' then
            return false
        end

        local lower = text:lower()
        return lower:find('unnamed enhancements', 1, true) ~= nil
    end

    local function guiRoots()
        local roots = {}

        if type(env.Library) == 'table' and typeof(env.Library.ScreenGui) == 'Instance' then
            table.insert(roots, env.Library.ScreenGui)
        end

        local parent = guiParent()
        local ok, children = pcall(function()
            return parent:GetChildren()
        end)
        if ok then
            for _, child in ipairs(children) do
                if child:IsA('ScreenGui')
                    and child.Name ~= ISLAND_NAME
                    and child.Name ~= WATERMARK_NAME
                    and not table.find(roots, child) then
                    table.insert(roots, child)
                end
            end
        end

        return roots
    end

    local function applyTitle()
        local changed = false

        for _, gui in ipairs(guiRoots()) do
            local ok, descendants = pcall(function()
                return gui:GetDescendants()
            end)
            if ok then
                for _, obj in ipairs(descendants) do
                    if obj:IsA('TextLabel') and isMenuTitle(obj.Text) then
                        obj.Text = ADDON_TITLE
                        changed = true
                    end
                end
            end
        end

        return changed
    end

    local function watchTitle()
        task.spawn(function()
            for _ = 1, 480 do
                if applyTitle() then
                    return
                end
                task.wait(0.25)
            end
        end)

        task.spawn(function()
            while true do
                task.wait(2)

                if type(env.Library) == 'table'
                    and typeof(env.Library.ScreenGui) == 'Instance' then
                    local gui = env.Library.ScreenGui

                    if not gui:GetAttribute('prampa_TitleHook') then
                        gui:SetAttribute('prampa_TitleHook', true)

                        gui.DescendantAdded:Connect(function(obj)
                            if obj:IsA('TextLabel') then
                                task.defer(function()
                                    if obj.Parent and isMenuTitle(obj.Text) then
                                        obj.Text = ADDON_TITLE
                                    end
                                end)
                            end
                        end)
                    end

                    applyTitle()
                end
            end
        end)
    end

    -----------------------------------------------------------------------
    -- background music controller
    --   one Sound instance is reused for every track, so tracks can never
    --   play on top of each other; selecting the current one restarts it
    -----------------------------------------------------------------------

    local music = {
        tracks = MUSIC_TRACKS,
        current = nil,
        sound = nil,
        assets = {},
    }

    local function trackSource(track)
        local file = track and track.file
        if type(file) ~= 'string' or file == '' then
            return nil
        end
        if file:find('://', 1, true) then
            return file
        end
        return MUSIC_BASE .. file
    end

    local function fileNameFor(source)
        local name = source:match('([^/]+)$') or 'track.ogg'
        name = name:gsub('[^%w%._-]', '_')

        -- deterministic hash so a changed url never reuses a stale file
        local hash = 7
        for index = 1, #source do
            hash = (hash * 31 + source:byte(index)) % 1000003
        end

        return string.format('prampa_%d_%s', hash, name)
    end

    local function prepareMusic()
        local sound = Instance.new('Sound')
        sound.Name = 'prampa_Music'
        sound.Looped = true
        sound.Volume = MUSIC_VOLUME
        sound.Parent = SoundService

        music.sound = sound
        env.prampa_Music = sound
    end

    function music.isPlaying()
        return music.sound ~= nil and music.sound.IsPlaying == true
    end

    function music.play(index)
        local track = music.tracks[index]
        if not track or not music.sound then
            return false
        end

        -- clicking the current track restarts it instead of layering a copy
        if music.current == index and music.sound.SoundId ~= '' then
            music.sound.TimePosition = 0
            music.sound:Play()
            if music.onChange then
                music.onChange()
            end
            return true
        end

        local asset = music.assets[index]
        if asset == nil then
            local source = trackSource(track)
            asset = source and assetFromUrl(source, fileNameFor(source), true) or false
            music.assets[index] = asset
        end

        if not asset then
            warn('[' .. BRAND .. '] could not load "' .. tostring(track.title) .. '"')
            return false
        end

        music.sound:Stop()
        music.sound.SoundId = asset
        music.sound.TimePosition = 0
        music.sound:Play()
        music.current = index

        if music.onChange then
            music.onChange()
        end

        return true
    end

    function music.toggle()
        if not music.sound then
            return false
        end

        if music.sound.IsPlaying then
            music.sound:Pause()
        elseif music.current then
            music.sound:Play()
        elseif #music.tracks > 0 then
            music.play(1)
        end

        if music.onChange then
            music.onChange()
        end

        return music.isPlaying()
    end

    function music.setVolume(value)
        local number = tonumber(value)
        if number and music.sound then
            music.sound.Volume = math.clamp(number, 0, 1)
        end
    end

    -----------------------------------------------------------------------
    -- island
    -----------------------------------------------------------------------

    local function buildIsland()
        local screenGui = Instance.new('ScreenGui')
        screenGui.Name = ISLAND_NAME
        screenGui.ResetOnSpawn = false
        screenGui.IgnoreGuiInset = true
        screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
        screenGui.DisplayOrder = 999999
        screenGui.Parent = guiParent()

        local island = Instance.new('Frame')
        island.Name = 'Island'
        -- centred horizontally, 2 px below the top edge of the screen
        island.AnchorPoint = Vector2.new(0.5, 0)
        island.Position = UDim2.new(0.5, 0, 0, 2)
        island.Size = UDim2.fromOffset(0, 34)
        island.AutomaticSize = Enum.AutomaticSize.X
        island.BackgroundColor3 = Color3.fromRGB(15, 15, 18)
        island.BackgroundTransparency = 0.12
        island.BorderSizePixel = 0
        island.Active = true
        island.ClipsDescendants = true
        island.Parent = screenGui

        -- restore a dragged position from a previous run (offset based)
        local savedPosition = env.UE_ISLAND_POSITION
        if typeof(savedPosition) == 'UDim2' then
            island.AnchorPoint = Vector2.new(0, 0)
            island.Position = savedPosition
        end

        local corner = Instance.new('UICorner')
        corner.CornerRadius = UDim.new(1, 0)
        corner.Parent = island

        local stroke = Instance.new('UIStroke')
        stroke.Color = ACCENT
        stroke.Transparency = 0.6
        stroke.Thickness = 1
        stroke.Parent = island

        local gradient = Instance.new('UIGradient')
        gradient.Rotation = 90
        gradient.Color = ColorSequence.new({
            ColorSequenceKeypoint.new(0, Color3.fromRGB(35, 35, 42)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(15, 15, 18)),
        })
        gradient.Parent = island

        local padding = Instance.new('UIPadding')
        padding.PaddingLeft = UDim.new(0, 10)
        padding.PaddingRight = UDim.new(0, 12)
        padding.PaddingTop = UDim.new(0, 6)
        padding.PaddingBottom = UDim.new(0, 6)
        padding.Parent = island

        local layout = Instance.new('UIListLayout')
        layout.FillDirection = Enum.FillDirection.Horizontal
        layout.SortOrder = Enum.SortOrder.LayoutOrder
        layout.VerticalAlignment = Enum.VerticalAlignment.Center
        layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
        layout.Padding = UDim.new(0, 9)
        layout.Parent = island

        local avatarHolder = Instance.new('Frame')
        avatarHolder.Name = 'AvatarHolder'
        avatarHolder.BackgroundTransparency = 1
        avatarHolder.Size = UDim2.fromOffset(20, 20)
        avatarHolder.LayoutOrder = 0
        avatarHolder.Parent = island

        local avatar = Instance.new('ImageLabel')
        avatar.Name = 'Avatar'
        avatar.BackgroundColor3 = STATUS_COLORS.unknown
        avatar.BorderSizePixel = 0
        avatar.Size = UDim2.fromScale(1, 1)
        avatar.ImageTransparency = 1
        avatar.Parent = avatarHolder

        local avatarCorner = Instance.new('UICorner')
        avatarCorner.CornerRadius = UDim.new(1, 0)
        avatarCorner.Parent = avatar

        local dot = Instance.new('Frame')
        dot.Name = 'LiveDot'
        dot.AnchorPoint = Vector2.new(1, 1)
        dot.Position = UDim2.fromScale(1, 1)
        dot.BackgroundColor3 = STATUS_COLORS.unknown
        dot.BorderSizePixel = 0
        dot.Size = UDim2.fromOffset(9, 9)
        dot.ZIndex = 3
        dot.Visible = false
        dot.Parent = avatarHolder

        local dotCorner = Instance.new('UICorner')
        dotCorner.CornerRadius = UDim.new(1, 0)
        dotCorner.Parent = dot

        local dotStroke = Instance.new('UIStroke')
        dotStroke.Color = Color3.fromRGB(15, 15, 18)
        dotStroke.Thickness = 2
        dotStroke.Parent = dot

        local function makeLabel(name, text, color, order)
            local label = Instance.new('TextLabel')
            label.Name = name
            label.BackgroundTransparency = 1
            label.Size = UDim2.fromOffset(0, 20)
            label.AutomaticSize = Enum.AutomaticSize.X
            label.Font = Enum.Font.GothamMedium
            label.TextSize = 13
            label.TextColor3 = color
            label.Text = text
            label.TextXAlignment = Enum.TextXAlignment.Left
            label.LayoutOrder = order
            label.Parent = island
            return label
        end

        local nameLabel = makeLabel('DiscordLabel', 'discord  not linked', Color3.fromRGB(220, 220, 230), 1)
        nameLabel.RichText = true

        -- song waves, only animate while something is playing ---------------
        local waveHolder = Instance.new('Frame')
        waveHolder.Name = 'Waves'
        waveHolder.BackgroundTransparency = 1
        waveHolder.Size = UDim2.fromOffset(16, 14)
        waveHolder.LayoutOrder = 2
        waveHolder.Visible = false
        waveHolder.Parent = island

        local waveBars = {}
        for index = 1, 4 do
            local bar = Instance.new('Frame')
            bar.Name = 'Bar' .. index
            bar.BackgroundColor3 = ACCENT
            bar.BackgroundTransparency = 0.15
            bar.BorderSizePixel = 0
            bar.AnchorPoint = Vector2.new(0, 1)
            bar.Position = UDim2.fromOffset((index - 1) * 4, 14)
            bar.Size = UDim2.fromOffset(2, 3)
            bar.Parent = waveHolder

            local barCorner = Instance.new('UICorner')
            barCorner.CornerRadius = UDim.new(1, 0)
            barCorner.Parent = bar

            waveBars[index] = bar
        end

        local function makeSeparator(order)
            local sep = Instance.new('Frame')
            sep.Name = 'Separator'
            sep.BackgroundColor3 = Color3.fromRGB(255, 255, 255)
            sep.BackgroundTransparency = 0.8
            sep.BorderSizePixel = 0
            sep.Size = UDim2.fromOffset(1, 14)
            sep.LayoutOrder = order
            sep.Parent = island
            return sep
        end

        local sep1 = makeSeparator(3)
        local fpsLabel = makeLabel('FPSLabel', '0 FPS', Color3.fromRGB(220, 220, 230), 4)
        local sep2 = makeSeparator(5)
        local pingLabel = makeLabel('PingLabel', '-- MS', Color3.fromRGB(220, 220, 230), 6)
        local sep3 = makeSeparator(7)
        local uptimeLabel = makeLabel('UptimeLabel', '00:00', Color3.fromRGB(170, 170, 182), 8)
        local sep4 = makeSeparator(9)
        local clockLabel = makeLabel('ClockLabel', '--:--', Color3.fromRGB(170, 170, 182), 10)

        -----------------------------------------------------------------------
        -- song picker (opens instead of collapsing the island)
        -----------------------------------------------------------------------

        local PANEL_WIDTH = 300
        local ROW_HEIGHT = 26
        local ROW_GAP = 5
        local SEARCH_HEIGHT = 30

        local panel = Instance.new('Frame')
        panel.Name = 'SongPicker'
        panel.AnchorPoint = Vector2.new(0.5, 0)
        panel.Position = UDim2.new(0.5, 0, 0, 42)
        panel.Size = UDim2.fromOffset(0, 0)
        panel.BackgroundColor3 = Color3.fromRGB(14, 14, 18)
        panel.BackgroundTransparency = 0.05
        panel.BorderSizePixel = 0
        panel.ClipsDescendants = true
        panel.Active = true
        panel.Visible = false
        panel.ZIndex = 5
        panel.Parent = screenGui

        local panelCorner = Instance.new('UICorner')
        panelCorner.CornerRadius = UDim.new(0, 16)
        panelCorner.Parent = panel

        local panelStroke = Instance.new('UIStroke')
        panelStroke.Color = ACCENT
        panelStroke.Transparency = 0.55
        panelStroke.Thickness = 1
        panelStroke.Parent = panel

        local panelGradient = Instance.new('UIGradient')
        panelGradient.Rotation = 90
        panelGradient.Color = ColorSequence.new({
            ColorSequenceKeypoint.new(0, Color3.fromRGB(32, 32, 40)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(13, 13, 17)),
        })
        panelGradient.Parent = panel

        -- the liquid bloom that spills out of the island when opening
        local ripple = Instance.new('Frame')
        ripple.Name = 'Ripple'
        ripple.AnchorPoint = Vector2.new(0.5, 0)
        ripple.Position = UDim2.new(0.5, 0, 0, 0)
        ripple.BackgroundColor3 = ACCENT
        ripple.BackgroundTransparency = 1
        ripple.BorderSizePixel = 0
        ripple.Size = UDim2.fromOffset(40, 40)
        ripple.ZIndex = 1
        ripple.Parent = panel

        local rippleCorner = Instance.new('UICorner')
        rippleCorner.CornerRadius = UDim.new(1, 0)
        rippleCorner.Parent = ripple

        local content = Instance.new('Frame')
        content.Name = 'Content'
        content.BackgroundTransparency = 1
        content.Size = UDim2.fromScale(1, 1)
        content.ZIndex = 2
        content.Parent = panel

        local contentPadding = Instance.new('UIPadding')
        contentPadding.PaddingLeft = UDim.new(0, 10)
        contentPadding.PaddingRight = UDim.new(0, 10)
        contentPadding.PaddingTop = UDim.new(0, 10)
        contentPadding.PaddingBottom = UDim.new(0, 10)
        contentPadding.Parent = content

        local contentLayout = Instance.new('UIListLayout')
        contentLayout.FillDirection = Enum.FillDirection.Vertical
        contentLayout.SortOrder = Enum.SortOrder.LayoutOrder
        contentLayout.Padding = UDim.new(0, ROW_GAP)
        contentLayout.Parent = content

        local search = Instance.new('TextBox')
        search.Name = 'Search'
        search.BackgroundColor3 = Color3.fromRGB(24, 24, 30)
        search.BackgroundTransparency = 0.15
        search.BorderSizePixel = 0
        search.Size = UDim2.new(1, 0, 0, SEARCH_HEIGHT)
        search.Font = Enum.Font.GothamMedium
        search.TextSize = 13
        search.TextColor3 = Color3.fromRGB(235, 235, 245)
        search.PlaceholderText = 'search songs'
        search.PlaceholderColor3 = Color3.fromRGB(130, 130, 145)
        search.Text = ''
        search.ClearTextOnFocus = false
        search.TextXAlignment = Enum.TextXAlignment.Left
        search.LayoutOrder = 0
        search.ZIndex = 2
        search.Parent = content

        local searchCorner = Instance.new('UICorner')
        searchCorner.CornerRadius = UDim.new(0, 8)
        searchCorner.Parent = search

        local searchPadding = Instance.new('UIPadding')
        searchPadding.PaddingLeft = UDim.new(0, 8)
        searchPadding.PaddingRight = UDim.new(0, 8)
        searchPadding.Parent = search

        local TEXT_IDLE = Color3.fromRGB(205, 205, 216)
        local TEXT_ACTIVE = Color3.fromRGB(255, 255, 255)
        local HOVER_COLOR = Color3.fromRGB(36, 36, 45)

        local rows = {}

        for index, track in ipairs(music.tracks) do
            local button = Instance.new('TextButton')
            button.Name = 'Track' .. index
            button.BackgroundColor3 = HOVER_COLOR
            button.BackgroundTransparency = 1
            button.BorderSizePixel = 0
            button.Size = UDim2.new(1, 0, 0, ROW_HEIGHT)
            button.Font = Enum.Font.GothamMedium
            button.TextSize = 13
            button.TextColor3 = TEXT_IDLE
            button.TextXAlignment = Enum.TextXAlignment.Left
            button.Text = '    ' .. track.title
            button.TextTruncate = Enum.TextTruncate.AtEnd
            button.AutoButtonColor = false
            button.LayoutOrder = index
            button.ZIndex = 2
            button.Parent = content

            local rowCorner = Instance.new('UICorner')
            rowCorner.CornerRadius = UDim.new(0, 7)
            rowCorner.Parent = button

            local rowPadding = Instance.new('UIPadding')
            rowPadding.PaddingLeft = UDim.new(0, 8)
            rowPadding.Parent = button

            button.MouseEnter:Connect(function()
                if music.current ~= index then
                    button.BackgroundTransparency = 0.9
                end
            end)

            button.MouseLeave:Connect(function()
                if music.current ~= index then
                    button.BackgroundTransparency = 1
                end
            end)

            -- selecting a track plays it; selecting the same one restarts it
            button.Activated:Connect(function()
                music.play(index)
            end)

            rows[index] = {
                button = button,
                title = track.title,
                lower = track.title:lower(),
            }
        end

        local emptyLabel = Instance.new('TextLabel')
        emptyLabel.Name = 'NoMatches'
        emptyLabel.BackgroundTransparency = 1
        emptyLabel.Size = UDim2.new(1, 0, 0, ROW_HEIGHT)
        emptyLabel.Font = Enum.Font.GothamMedium
        emptyLabel.TextSize = 12
        emptyLabel.TextColor3 = Color3.fromRGB(140, 140, 152)
        emptyLabel.Text = 'no matching song'
        emptyLabel.TextXAlignment = Enum.TextXAlignment.Center
        emptyLabel.LayoutOrder = 100
        emptyLabel.Visible = false
        emptyLabel.ZIndex = 2
        emptyLabel.Parent = content

        local panelOpen = false
        local panelTween

        local function visibleRowCount()
            local count = 0
            for _, row in ipairs(rows) do
                if row.button.Visible then
                    count += 1
                end
            end
            if count == 0 then
                return 1
            end
            return count
        end

        local function targetPanelHeight()
            local count = visibleRowCount()
            return 10 + SEARCH_HEIGHT + ROW_GAP
                + count * ROW_HEIGHT + (count - 1) * ROW_GAP + 10
        end

        local function positionPanel()
            local absolute = island.AbsolutePosition
            local size = island.AbsoluteSize
            local camera = workspace.CurrentCamera
            local viewport = camera and camera.ViewportSize or Vector2.new(1920, 1080)
            local height = targetPanelHeight()

            local x = absolute.X + size.X / 2
            local y = absolute.Y + size.Y + 6

            if y + height > viewport.Y - 4 then
                y = math.max(4, absolute.Y - 6 - height)
            end

            panel.Position = UDim2.fromOffset(x, y)
        end

        local function refreshRows()
            for index, row in ipairs(rows) do
                local active = music.current == index

                row.button.TextColor3 = active and TEXT_ACTIVE or TEXT_IDLE
                row.button.Font = active and Enum.Font.GothamBold or Enum.Font.GothamMedium
                row.button.Text = (active and '•  ' or '    ') .. row.title
                row.button.BackgroundColor3 = active and ACCENT or HOVER_COLOR
                row.button.BackgroundTransparency = active and 0.82 or 1
            end
        end

        music.onChange = refreshRows

        local function resizePanel()
            if not panelOpen then
                return
            end

            positionPanel()

            if panelTween then
                panelTween:Cancel()
            end

            panelTween = TweenService:Create(
                panel,
                TweenInfo.new(0.24, Enum.EasingStyle.Quint, Enum.EasingDirection.Out),
                { Size = UDim2.fromOffset(PANEL_WIDTH, targetPanelHeight()) }
            )
            panelTween:Play()
        end

        local function openPanel()
            if panelOpen then
                return
            end
            panelOpen = true

            panel.Visible = true
            panel.Size = UDim2.fromOffset(PANEL_WIDTH, 0)
            panelCorner.CornerRadius = UDim.new(1, 0)
            positionPanel()

            -- liquid: round pill grows into a card while a soft disc blooms
            ripple.Size = UDim2.fromOffset(40, 40)
            ripple.BackgroundTransparency = 0.4

            TweenService:Create(
                ripple,
                TweenInfo.new(0.6, Enum.EasingStyle.Quint, Enum.EasingDirection.Out),
                {
                    Size = UDim2.fromOffset(PANEL_WIDTH * 2, PANEL_WIDTH * 2),
                    BackgroundTransparency = 1,
                }
            ):Play()

            TweenService:Create(
                panelCorner,
                TweenInfo.new(0.5, Enum.EasingStyle.Quint, Enum.EasingDirection.Out),
                { CornerRadius = UDim.new(0, 16) }
            ):Play()

            if panelTween then
                panelTween:Cancel()
            end

            panelTween = TweenService:Create(
                panel,
                TweenInfo.new(0.36, Enum.EasingStyle.Quint, Enum.EasingDirection.Out),
                { Size = UDim2.fromOffset(PANEL_WIDTH, targetPanelHeight()) }
            )
            panelTween:Play()
        end

        local function closePanel()
            if not panelOpen then
                return
            end
            panelOpen = false

            if panelTween then
                panelTween:Cancel()
            end

            panelTween = TweenService:Create(
                panel,
                TweenInfo.new(0.24, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
                { Size = UDim2.fromOffset(PANEL_WIDTH, 0) }
            )
            panelTween:Play()

            panelTween.Completed:Once(function()
                if not panelOpen then
                    panel.Visible = false
                end
            end)
        end

        local function togglePanel()
            if panelOpen then
                closePanel()
            else
                openPanel()
            end
        end

        local function applyFilter()
            local query = search.Text:lower()
            query = query:gsub('^%s+', ''):gsub('%s+$', '')

            local matches = 0
            for _, row in ipairs(rows) do
                local match = query == '' or row.lower:find(query, 1, true) ~= nil
                row.button.Visible = match
                if match then
                    matches += 1
                end
            end

            emptyLabel.Visible = matches == 0
            refreshRows()
            resizePanel()
        end

        search.TextChanged:Connect(applyFilter)

        -- wave animation ----------------------------------------------------
        task.spawn(function()
            local phase = 0

            while screenGui.Parent do
                local playing = music.isPlaying()

                waveHolder.Visible = playing

                if playing then
                    phase += 0.42

                    for index, bar in ipairs(waveBars) do
                        local height = 3 + 9 * (0.5 + 0.5 * math.sin(phase + index * 0.85))
                        bar.Size = UDim2.fromOffset(2, height)
                    end
                end

                task.wait(0.06)
            end
        end)

        -- presence --------------------------------------------------------
        local hasAvatar = false
        local manualStatus = nil
        local lastAvatarId = nil

        local function render(display, status, platform)
            local color = STATUS_COLORS[status] or STATUS_COLORS.unknown

            if not hasAvatar then
                avatar.BackgroundColor3 = color
            end
            dot.BackgroundColor3 = color
            stroke.Color = color
            stroke.Transparency = 0.55

            local text = '<font color="' .. colorHex(ACCENT) .. '">' .. escapeRich(BRAND) .. '</font>  '
                .. escapeRich(display)

            if type(status) == 'string' and status ~= '' and status ~= 'unknown' then
                local word = status
                if status ~= 'offline' and type(platform) == 'string' and platform ~= '' then
                    word = status .. ' (' .. platform .. ')'
                end
                text = text .. '  <font color="' .. colorHex(color) .. '">' .. escapeRich(word) .. '</font>'
            end

            nameLabel.Text = text
        end

        local function setAvatar(asset)
            if asset then
                avatar.Image = asset
                avatar.ImageTransparency = 0
                avatar.BackgroundTransparency = 1
                dot.Visible = true
                hasAvatar = true
            else
                avatar.ImageTransparency = 1
                avatar.BackgroundTransparency = 0
                dot.Visible = false
                hasAvatar = false
            end
        end

        local function refreshPresence()
            if manualStatus then
                render(DISCORD_NAME_OVERRIDE ~= '' and DISCORD_NAME_OVERRIDE or 'you', manualStatus, nil)
                return
            end

            if DISCORD_ID == '' then
                if DISCORD_NAME_OVERRIDE ~= '' then
                    render(DISCORD_NAME_OVERRIDE, 'unknown', nil)
                end
                return
            end

            local body = httpGet(LANYARD .. DISCORD_ID)
            if type(body) ~= 'string' then
                return
            end

            local ok, decoded = pcall(function()
                return HttpService:JSONDecode(body)
            end)
            if not ok or type(decoded) ~= 'table' then
                return
            end

            if decoded.success ~= true or type(decoded.data) ~= 'table' then
                render(DISCORD_NAME_OVERRIDE ~= '' and DISCORD_NAME_OVERRIDE or 'not linked', 'unknown', nil)
                return
            end

            local data = decoded.data
            local user = type(data.discord_user) == 'table' and data.discord_user or {}
            local status = type(data.discord_status) == 'string' and data.discord_status or 'offline'

            local display = DISCORD_NAME_OVERRIDE
            if display == '' then
                display = user.global_name
            end
            if type(display) ~= 'string' or display == '' then
                display = user.username
            end
            if type(display) ~= 'string' or display == '' then
                display = 'unknown'
            end

            local platform = 'desktop'
            if data.active_on_discord_mobile == true then
                platform = 'mobile'
            elseif data.active_on_discord_web == true then
                platform = 'web'
            end

            render(display, status, platform)

            local wantId = tostring(user.id or '')
            if wantId ~= '' and wantId ~= lastAvatarId then
                lastAvatarId = wantId

                local hash = user.avatar
                local url
                if type(hash) == 'string' and hash ~= '' then
                    url = CDN .. 'avatars/' .. wantId .. '/' .. hash .. '.png?size=64'
                else
                    url = CDN .. 'embed/avatars/0.png'
                end

                setAvatar(assetFromUrl(url, 'prampa_avatar_' .. wantId .. '.png'))
            end
        end

        -- dragging + collapse --------------------------------------------
        local dragging = false
        local moved = false
        local dragStart = Vector2.zero
        local startPos = island.Position

        island.InputBegan:Connect(function(input)
            if input.UserInputType == Enum.UserInputType.MouseButton1
                or input.UserInputType == Enum.UserInputType.Touch then
                dragging = true
                moved = false
                dragStart = input.Position

                -- the island spawns centred, so convert to an offset position
                -- the moment it is touched; movement then stays 1:1
                if island.AnchorPoint.X ~= 0 or island.AnchorPoint.Y ~= 0 then
                    local absPosition = island.AbsolutePosition
                    island.AnchorPoint = Vector2.new(0, 0)
                    island.Position = UDim2.fromOffset(absPosition.X, absPosition.Y)
                end

                startPos = island.Position

                local connection
                connection = input.Changed:Connect(function()
                    if input.UserInputState ~= Enum.UserInputState.End then
                        return
                    end

                    dragging = false
                    env.UE_ISLAND_POSITION = island.Position

                    if connection then
                        connection:Disconnect()
                    end

                    if not moved then
                        togglePanel()
                    end
                end)
            end
        end)

        UserInputService.InputChanged:Connect(function(input)
            if not dragging then
                return
            end
            if input.UserInputType ~= Enum.UserInputType.MouseMovement
                and input.UserInputType ~= Enum.UserInputType.Touch then
                return
            end

            local delta = input.Position - dragStart
            if not moved and delta.Magnitude > 4 then
                moved = true
            end

            local camera = workspace.CurrentCamera
            local viewport = camera and camera.ViewportSize or Vector2.new(1920, 1080)
            local size = island.AbsoluteSize

            local x = math.clamp(startPos.X.Offset + delta.X, 0, math.max(0, viewport.X - size.X))
            local y = math.clamp(startPos.Y.Offset + delta.Y, 0, math.max(0, viewport.Y - size.Y))

            island.Position = UDim2.fromOffset(x, y)

            if panelOpen then
                positionPanel()
            end
        end)

        -- fps ------------------------------------------------------------
        local fps = 0
        local fpsAccum = 0
        local fpsFrames = 0

        RunService.RenderStepped:Connect(function(dt)
            fpsAccum += dt
            fpsFrames += 1

            if fpsAccum >= 0.25 then
                fps = fpsFrames / fpsAccum
                fpsAccum = 0
                fpsFrames = 0
            end
        end)

        local function fpsColor(value)
            if value >= 120 then
                return Color3.fromRGB(120, 230, 150)
            elseif value >= 60 then
                return Color3.fromRGB(240, 210, 110)
            end
            return Color3.fromRGB(240, 110, 110)
        end

        local function pingColor(value)
            if value <= 0 then
                return Color3.fromRGB(150, 150, 160)
            elseif value < 60 then
                return Color3.fromRGB(120, 230, 150)
            elseif value < 120 then
                return Color3.fromRGB(240, 210, 110)
            end
            return Color3.fromRGB(240, 110, 110)
        end

        local startedAt = os.clock()

        task.spawn(function()
            refreshPresence()

            while screenGui.Parent do
                task.wait(POLL_SECONDS)
                refreshPresence()
            end
        end)

        task.spawn(function()
            while screenGui.Parent do
                local ping = readPing()

                fpsLabel.Text = string.format('%d FPS', math.floor(fps + 0.5))
                fpsLabel.TextColor3 = fpsColor(fps)

                if ping and ping > 0 then
                    pingLabel.Text = string.format('%d MS', math.floor(ping + 0.5))
                    pingLabel.TextColor3 = pingColor(ping)
                else
                    pingLabel.Text = '-- MS'
                    pingLabel.TextColor3 = pingColor(0)
                end

                task.wait(0.25)
            end
        end)

        task.spawn(function()
            while screenGui.Parent do
                uptimeLabel.Text = formatUptime(os.clock() - startedAt)
                clockLabel.Text = localClock()
                task.wait(1)
            end
        end)

        if type(env.Library) == 'table'
            and typeof(env.Library.ScreenGui) == 'Instance' then
            env.Library.ScreenGui.Destroying:Connect(function()
                screenGui:Destroy()
            end)
        end

        env.prampa_HUD = screenGui

        -- live controls ---------------------------------------------------
        env.UE_SetStatus = function(status)
            manualStatus = tostring(status)
            refreshPresence()
        end

        env.UE_ClearStatus = function()
            manualStatus = nil
            refreshPresence()
        end

        env.UE_RefreshDiscord = function()
            refreshPresence()
        end

        env.UE_ToggleIsland = function()
            island.Visible = not island.Visible

            if not island.Visible then
                closePanel()
            end
        end

        env.UE_ToggleSongPicker = togglePanel
        env.UE_PlayTrack = function(value)
            if type(value) == 'number' then
                return music.play(value)
            end

            local wanted = tostring(value):lower()
            for index, track in ipairs(music.tracks) do
                if track.title:lower():find(wanted, 1, true) then
                    return music.play(index)
                end
            end

            return false
        end

        print('[' .. BRAND .. '] HUD ready - drag to move, click for the song picker.')
        if DISCORD_ID == '' then
            print('[' .. BRAND .. '] no Discord user ID set; presence disabled.')
        end
    end

    -----------------------------------------------------------------------
    -- corner watermark
    -----------------------------------------------------------------------

    local function buildWatermark()
        local gui = Instance.new('ScreenGui')
        gui.Name = WATERMARK_NAME
        gui.ResetOnSpawn = false
        gui.IgnoreGuiInset = true
        gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
        gui.DisplayOrder = 999998
        gui.Parent = guiParent()

        local row = Instance.new('Frame')
        row.Name = 'Row'
        row.AnchorPoint = Vector2.new(1, 1)
        row.Position = UDim2.new(1, -14, 1, -12)
        row.Size = UDim2.fromOffset(0, 18)
        row.AutomaticSize = Enum.AutomaticSize.X
        row.BackgroundTransparency = 1
        row.Parent = gui

        local layout = Instance.new('UIListLayout')
        layout.FillDirection = Enum.FillDirection.Horizontal
        layout.VerticalAlignment = Enum.VerticalAlignment.Center
        layout.SortOrder = Enum.SortOrder.LayoutOrder
        layout.Padding = UDim.new(0, 6)
        layout.Parent = row

        local label = Instance.new('TextLabel')
        label.Name = 'Wordmark'
        label.BackgroundTransparency = 1
        label.Size = UDim2.fromOffset(0, 18)
        label.AutomaticSize = Enum.AutomaticSize.X
        label.Font = Enum.Font.GothamBold
        label.TextSize = 12
        label.Text = BRAND
        label.TextColor3 = Color3.fromRGB(210, 210, 222)
        label.TextTransparency = 0.6
        label.LayoutOrder = 0
        label.Parent = row

        env.prampa_Watermark = gui
    end

    -----------------------------------------------------------------------
    -- public helpers
    --   getgenv().UE_SetMenuTitle('x')
    --   getgenv().UE_SetDiscordName('x')
    --   getgenv().UE_SetStatus('dnd')
    --   getgenv().UE_ToggleIsland()
    --   getgenv().UE_ToggleSongPicker()
    --   getgenv().UE_PlayTrack(3) / UE_PlayTrack('fedakar')
    --   getgenv().UE_ToggleMusic() / UE_SetMusicVolume(0.5)
    --   getgenv().UE_DumpTextLabels()
    -----------------------------------------------------------------------

    env.UE_ToggleMusic = function()
        return music.toggle()
    end

    env.UE_SetMusicVolume = function(value)
        music.setVolume(value)
    end

    env.UE_SetMenuTitle = function(title)
        ADDON_TITLE = tostring(title)
        applyTitle()
    end

    env.UE_SetDiscordName = function(name)
        DISCORD_NAME_OVERRIDE = tostring(name)
        if env.UE_RefreshDiscord then
            env.UE_RefreshDiscord()
        end
    end

    env.UE_DumpTextLabels = function()
        for _, gui in ipairs(guiRoots()) do
            for _, obj in ipairs(gui:GetDescendants()) do
                if obj:IsA('TextLabel') and obj.Text ~= '' then
                    print(obj:GetFullName() .. ' = ' .. string.format('%q', obj.Text))
                end
            end
        end
    end

    -----------------------------------------------------------------------
    -- boot
    -----------------------------------------------------------------------

    task.spawn(function()
        local waited = 0

        while waited < 300 do
            if type(env.Library) == 'table'
                and typeof(env.Library.ScreenGui) == 'Instance' then
                watchTitle()
                prepareMusic()
                buildIsland()
                if SHOW_WATERMARK then
                    buildWatermark()
                end

                if #music.tracks > 0 then
                    task.spawn(function()
                        music.play(1)
                    end)
                end
                return
            end

            task.wait(0.2)
            waited += 0.2
        end

        warn('[' .. BRAND .. '] getgenv().Library never appeared; HUD not created.')
    end)
end
-- <<< prampa addon <<<
"""


def parse_hex(value: str) -> "tuple[int, int, int]":
    text = value.strip().lstrip("#")
    if len(text) != 6 or any(c not in "0123456789abcdefABCDEF" for c in text):
        fail("ACCENT_HEX must be six hex digits, e.g. 7C5CFF")
    return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)


def main(argv: "list[str]") -> int:
    # the console codepage cannot always render track titles; never crash on it
    try:
        sys.stdout.reconfigure(errors="replace")
        sys.stderr.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass

    here = Path(__file__).resolve().parent
    source = Path(argv[1]).expanduser() if len(argv) > 1 else here / SOURCE_NAME
    output = Path(argv[2]).expanduser() if len(argv) > 2 else here / OUTPUT_NAME

    # ---- resolve Discord settings ---------------------------------------
    raw_id = DISCORD_USER_ID.strip()
    raw_name = DISCORD_NAME.strip()

    if raw_id == PLACEHOLDER_ID:
        raw_id = ""

    if TOKEN_RE.match(raw_id):
        fail(
            "DISCORD_USER_ID looks like a real Discord token.\n"
            "       No token is used anywhere in this addon. Presence is read from\n"
            "       Lanyard, which only needs your numeric user ID (17-20 digits).\n"
            "       Right click your name in Discord with Developer Mode enabled and\n"
            "       choose 'Copy User ID'."
        )

    if TOKEN_RE.match(raw_name):
        fail("DISCORD_NAME looks like a real Discord token; put a plain name.")

    presence_id = ""
    if raw_id:
        if raw_id.isdigit() and 15 <= len(raw_id) <= 25:
            presence_id = raw_id
        elif not raw_name:
            raw_name = raw_id
            print(
                "note: DISCORD_USER_ID is not numeric, so it will be shown as a "
                "plain name and Lanyard presence is disabled.",
                file=sys.stderr,
            )

    # ---- validate the track list ----------------------------------------
    if not (MUSIC_BASE.startswith("https://") or MUSIC_BASE.startswith("http://")):
        fail("MUSIC_BASE must be a full http(s) URL (keep the trailing '/').")

    tracks = []
    for entry in MUSIC_TRACKS:
        if not isinstance(entry, (tuple, list)) or len(entry) != 2:
            fail("each MUSIC_TRACKS entry must be (title, file).")
        title = str(entry[0]).strip()
        file = str(entry[1]).strip()
        if not title or not file:
            fail("MUSIC_TRACKS entries need both a title and a file.")
        if "\n" in title or "\r" in title:
            fail("track titles must be a single line: %r" % title)
        tracks.append((title, file))

    if len(tracks) > 12:
        fail("MUSIC_TRACKS holds %d tracks; the picker is limited to 12." % len(tracks))

    seen_files = set()
    for _, file in tracks:
        key = file.lower()
        if key in seen_files:
            fail("duplicate track file in MUSIC_TRACKS: %s" % file)
        seen_files.add(key)

    try:
        music_volume = float(MUSIC_VOLUME)
    except (TypeError, ValueError):
        fail("MUSIC_VOLUME must be a number between 0.0 and 1.0.")
    if not (0.0 <= music_volume <= 1.0):
        fail("MUSIC_VOLUME must be between 0.0 and 1.0 (0.25 = 25 %).")

    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,32}", BRAND):
        fail("BRAND must be 1-32 chars of letters, digits, '_', '-' or '.'.")

    accent = parse_hex(ACCENT_HEX)

    # ---- guard rails ----------------------------------------------------
    if not source.is_file():
        fail("source file not found: %s" % source)

    for label, value in (
        ("MENU_TITLE", MENU_TITLE),
        ("DISCORD_NAME", raw_name),
        ("BRAND", BRAND),
    ):
        if "\n" in value or "\r" in value:
            fail("%s must be a single line." % label)

    with open(source, "r", encoding="utf-8", newline="") as handle:
        raw = handle.read()

    newline = "\r\n" if "\r\n" in raw else "\n"

    if any(marker in raw for marker in STALE_MARKERS):
        fail(
            "the source file already contains the addon block.\n"
            "       Run this against a clean ue-v2-cracked.luau.txt."
        )

    if raw.count("return runApplication()") != 1:
        fail("could not find exactly one 'return runApplication()' anchor.")

    text = raw
    report = []

    # ---- 1. rebrand the shared-env key ----------------------------------
    old_key = lua_str(OLD_TITLE)
    new_key = lua_str(BRAND)

    guard_old = "rawget(sharedEnv, %s)" % old_key
    guard_new = "rawget(sharedEnv, %s)" % new_key
    store_old = "sharedEnv[%s] = control" % old_key
    store_new = "sharedEnv[%s] = control" % new_key

    key_hits = text.count(guard_old) + text.count(store_old)
    text = text.replace(guard_old, guard_new).replace(store_old, store_new)
    report.append("env key    : %d replacement(s) -> %r" % (key_hits, BRAND))
    if key_hits != 2:
        print(
            "warning: expected 2 env-key replacements, got %d." % key_hits,
            file=sys.stderr,
        )

    # ---- 2. drop the compiler directives -------------------------------
    text, directive_hits = re.subn(
        r"^--!(?:nocheck|native)[ \t]*\r?\n", "", text, flags=re.M
    )
    report.append("directives : %d removed" % directive_hits)

    # ---- 3. drop the ascii-art banner -----------------------------------
    art_start = text.find("--[[")
    art_end = text.find("]]", art_start) if art_start != -1 else -1
    art_ok = (
        art_start != -1
        and art_end != -1
        and art_start < 400
        and (art_end - art_start) < 6000
        and ("@@@@" in text[art_start:art_end] or ",,,,,," in text[art_start:art_end])
    )

    if art_ok:
        banner = newline.join(
            [
                "-- ================================================================",
                "--  %s build" % BRAND,
                "--  generated by patch_ue2.py - do not redistribute",
                "-- ================================================================",
            ]
        )
        text = text[:art_start] + banner + newline + text[art_end + 2 :]
        report.append("ascii art  : removed")
    else:
        report.append("ascii art  : not found (left as-is)")

    # ---- 4. rebrand the console banner ----------------------------------
    banner_re = re.compile(r"print\[\[[\s\S]{0,3000}?\]\]")
    new_print = "print(%s)" % lua_str("[%s] build loaded" % BRAND)
    text, print_hits = banner_re.subn(lambda m: new_print, text, count=1)
    report.append("console    : %d banner(s) rebranded" % print_hits)

    # ---- 5. rewrite the two constant-pool strings -----------------------
    pool_re = re.compile(r"(\[\d+\]\s*=\s*)" + re.escape(old_key))
    text, pool_hits = pool_re.subn(lambda m: m.group(1) + lua_str(MENU_TITLE), text)
    report.append("title      : %d constant(s) -> %r" % (pool_hits, MENU_TITLE))

    # ---- 5b. rebrand the theme JSON labels -------------------------------
    theme_old = '"ItemType":"%s"' % OLD_TITLE
    theme_hits = text.count(theme_old)
    text = text.replace(theme_old, '"ItemType":"%s"' % BRAND)
    report.append("themes     : %d label(s) -> %r" % (theme_hits, BRAND))

    # ---- 6. inject the addon --------------------------------------------
    track_lines = [
        "        { title = %s, file = %s }," % (lua_str(title), lua_str(file))
        for title, file in tracks
    ]
    lua_tracks = ("{\n" + "\n".join(track_lines) + "\n    }") if track_lines else "{}"

    addon = ADDON_TEMPLATE.replace("@@BRAND@@", lua_str(BRAND))
    addon = addon.replace("@@TITLE@@", lua_str(MENU_TITLE))
    addon = addon.replace("@@DISCORD_ID@@", lua_str(presence_id))
    addon = addon.replace("@@DISCORD_NAME@@", lua_str(raw_name))
    addon = addon.replace("@@MUSIC_BASE@@", lua_str(MUSIC_BASE))
    addon = addon.replace("@@MUSIC_TRACKS@@", lua_tracks)
    addon = addon.replace("@@MUSIC_VOLUME@@", "%.3f" % music_volume)
    addon = addon.replace("@@ACCENT@@", "Color3.fromRGB(%d, %d, %d)" % accent)
    addon = addon.replace("@@WATERMARK@@", "true" if SHOW_WATERMARK else "false")
    addon = addon.strip("\r\n") + newline

    if "@@" in addon:
        fail("a placeholder was left unresolved in the addon block.")

    anchor = text.rfind("return runApplication()")
    line_start = text.rfind("\n", 0, anchor) + 1
    text = text[:line_start] + addon + text[line_start:]

    # ---- write ----------------------------------------------------------
    with open(output, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)

    # keep the GitHub filename in sync so there is no manual copy step
    alias = output.parent / ALIAS_NAME if ALIAS_NAME else None
    alias_written = 0
    if alias is not None and alias.resolve() != output.resolve():
        try:
            with open(alias, "wb") as handle:
                handle.write(text.encode("utf-8"))
            alias_written = alias.stat().st_size
        except OSError as error:
            print("warning: could not write %s: %s" % (alias, error), file=sys.stderr)

    # ---- verify ---------------------------------------------------------
    with open(output, "r", encoding="utf-8", newline="") as handle:
        check = handle.read()

    problems = []
    if check.count(MARKER) != 1:
        problems.append("addon marker count != 1")
    if check.count("return runApplication()") != 1:
        problems.append("'return runApplication()' count != 1")
    if "@@" in check[check.find(MARKER) :]:
        problems.append("unresolved placeholder")
    if lua_str(MENU_TITLE) not in check:
        problems.append("title literal missing")
    if "--!native" in check or "--!nocheck" in check:
        problems.append("compiler directives still present")
    if check.count("sharedEnv[%s] = control" % lua_str(BRAND)) != 1:
        problems.append("brand env key missing")
    if not check.rstrip().endswith("return runApplication()"):
        problems.append("file no longer ends with 'return runApplication()'")

    print("source : %s (%d bytes)" % (source, len(raw.encode("utf-8"))))
    print("output : %s (%d bytes)" % (output, len(check.encode("utf-8"))))
    if alias_written:
        print("alias  : %s (%d bytes)" % (alias, alias_written))
    print("brand  : %s   accent: #%02X%02X%02X" % ((BRAND,) + accent))
    print("title  : %s" % MENU_TITLE)
    print("user id: %s" % (presence_id or "(none - presence disabled)"))
    print("tracks : %d" % len(tracks))
    for index, (title, file) in enumerate(tracks, start=1):
        print("  %2d. %-28s %s" % (index, title, file))
    for line in report:
        print("  " + line)
    print("anchor : inserted at line %d" % (check[: check.find(MARKER)].count("\n") + 1))

    if pool_hits != 2:
        print(
            "warning: expected 2 constant-pool rewrites, got %d. The visible "
            "title fallback still runs at startup." % pool_hits,
            file=sys.stderr,
        )

    if problems:
        print("verify : FAILED -> " + ", ".join(problems), file=sys.stderr)
        return 1

    print("verify : ok")

    if MENU_TITLE == PLACEHOLDER_TITLE:
        print("\nnote: MENU_TITLE is still the placeholder.")

    if presence_id == "":
        print(
            "\nnote: no numeric Discord user ID set, so the HUD cannot show\n"
            "      presence. Join https://discord.gg/lanyard and put your user ID\n"
            "      in DISCORD_USER_ID."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
