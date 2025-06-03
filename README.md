# Discord RAT

A Discord-controlled remote administration tool to manage and control computers remotely through Discord bot commands.
Please leave a star ⭐!

> **Warning**  
> This tool is for educational and authorized use only. Misuse may be illegal. I am not responsible for anything you do with this program.
``UAC and screenshare command not working right now, will be fixed soon``

## Features

### Screen & Display Management
- Take screenshots of specific monitors or all displays
- Real-time screen sharing to Discord voice channels
- Monitor detection and selection
- Periodic screenshot sharing

### File Management
- Browse directories and list files
- Upload files directly to Discord
- Download files from URLs
- Copy, delete, and manage files remotely

### System Information & Control
- Comprehensive system information (hardware, network, etc.)
- Remote shutdown, restart, and logoff capabilities
- Administrator privilege checking and elevation
- Execute shell commands remotely

### Audio & Voice Features
- Join Discord voice channels and stream microphone
- List and select audio input devices
- Real-time audio streaming

### Administrative Tools
- Toggle system features (UAC, Windows Defender, Firewall)
- Task Manager access control
- Process management and termination
- Startup program management

### Surveillance Capabilities
- Webcam access and photo capture
- Clipboard content monitoring
- Keylogger functionality with configurable intervals

### Credential Management
- Extract saved credentials from browsers (Chrome, Opera (GX), Edge and Firefox)
- Support for multiple credential storage services (Steam, EpicGames, Discord)
- Secure credential extraction

### Interactive Features
- Display custom message boxes on target system
- Open websites remotely
- Text-to-speech functionality
- Wallpaper modification
- Input device control (mouse/keyboard lock/unlock)
- Keyboard layout switching

## Installation

### Prerequisites
- Python 3.7 or higher
- Windows operating system
- Discord bot token

### Required Dependencies
```bash
pip install discord.py
pip install psutil
pip install mss
pip install sounddevice
pip install numpy
pip install opencv-python
pip install pillow
pip install pyperclip
pip install keyboard
pip install requests
```

### Setup
1. Clone or download the repository
2. Install all required dependencies using pip
3. Create a Discord bot and obtain the bot token
4. Replace `YOUR_BOT_TOKEN_HERE` with your actual bot token
5. Customize the command prefix if desired (default is `!`)
6. Run the script with appropriate permissions

## Configuration

### Basic Configuration
```python
TOKEN = 'YOUR_BOT_TOKEN_HERE'  # Replace with your Discord bot token
command_pref = '!'             # Command prefix (default: !)
```

### Discord Bot Setup
1. Go to Discord Developer Portal
2. Create a new application and bot
3. Copy the bot token
4. Invite the bot to your server with appropriate permissions
5. Ensure the bot has permissions for:
   - Send Messages
   - Attach Files
   - Connect to Voice Channels
   - Speak in Voice Channels

## Command Reference

### Screen & Display Commands
- `!screenshot [monitor_num]` - Take screenshot of specific monitor or all
- `!getmonitors` - List all available monitors
- `!screenshare <monitor_num> [voice_channel_id]` - Start screen sharing
- `!simpleshare <monitor_num> [interval]` - Periodic screenshots

### File Management Commands
- `!ls <directory>` - List files in directory
- `!file delete <path>` - Delete file or folder
- `!file upload <path>` - Upload file to Discord
- `!file get <url> <path>` - Download file from URL
- `!file copy <src> <dst>` - Copy file or directory

### System Information Commands
- `!info system` - Display system information
- `!info hardware` - Show CPU, RAM, and disk information
- `!info network` - Display IP and network interface information
- `!admincheck` - Check administrator privileges

### System Control Commands
- `!shutdown` / `!shutdown cancel` - Shutdown system or cancel shutdown
- `!restart` - Restart the system
- `!logoff` - Log off current user
- `!cmd <command>` - Execute shell command

### Audio Commands
- `!voice <channel_link>` - Join voice channel and stream microphone
- `!voice leave` / `!disconnect` - Leave voice channel
- `!audio` - List available audio input devices
- `!selectaudio <number>` - Select audio input device
- `!mute` / `!unmute` - Mute or unmute microphone

### Administrative Commands (Requires Admin)
- `!uac` - Attempt to gain administrator privileges
- `!disableuac` - Disable User Account Control
- `!disabledefender` - Disable Windows Defender
- `!disablefirewall` - Disable Windows Firewall
- `!disabletaskmgr` / `!enabletaskmgr` - Toggle Task Manager access

### Surveillance Commands
- `!getcams` - List available webcams
- `!selectcam <number>` - Select webcam
- `!webcampic` - Take picture with selected webcam
- `!clipboard` - Get clipboard content
- `!keylogger start` / `!keylogger stop` - Control keylogger

### Process Management
- `!tasklist` - Show running processes
- `!prockill <process_name>` - Terminate a process

### Credential Commands
- `!steal` - List supported credential services
- `!steal <service>` - Extract credentials from specified service

### Interactive Commands
- `!troll tts <message>` - Text-to-speech output
- `!troll bluescreen` - Trigger blue screen effect
- `!troll wallpaper <url>` - Change desktop wallpaper
- `!troll lock/unlock mouse` - Control mouse access
- `!troll lock/unlock keyboard` - Control keyboard access
- `!troll azerty/qwerty` - Switch keyboard layout
- `!troll revertall` - Revert all modifications
- `!message <text>` - Display message box
- `!website <url>` - Open website in default browser

### Utility Commands
- `!startup add/remove` - Manage startup programs
- `!uploadlink <url>` - Download and process file from URL
- `!exit` - Terminate the RAT application

## Usage Examples

### Taking a Screenshot
```
!screenshot
!screenshot 1
```

### File Operations
```
!ls C:\Users
!file upload C:\document.txt
!file delete C:\temp\oldfile.txt
```

### System Information
```
!info system
!info hardware
!admincheck
```

### Remote Control
```
!shutdown
!restart
!cmd dir
```

## Contributing

Contributions are welcome. Whether it's a bug fix, feature, etc.., feel free to open an issue or submit a pull request. Please follow the code style and include clear documentation for any changes, for new commands, use 1 comment above the function to explain wwhat it is.

## DISCLAIMER

This tool is intended for legitimate system administration purposes only. Users are responsible for ensuring compliance with all applicable laws and regulations. Only use this software on systems you own or have explicit permission to access. The developers are not responsible for any misuse of this software. MIT License - see the [LICENSE](LICENSE) file for details.
