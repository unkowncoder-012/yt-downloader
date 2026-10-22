#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "=== 1. Checking Storage Access ==="
if [ ! -d "$HOME/storage" ]; then
    termux-setup-storage
    sleep 2
else
    echo "Storage access already granted."
fi

echo "=== 2. Upgrading System & Installing Dependencies ==="
# Resume and repair any broken dpkg states
dpkg --configure -a 2>/dev/null || true

# Set non-interactive mode and keep existing configs to prevent prompts from pausing execution
export DEBIAN_FRONTEND=noninteractive
APT_OPTS='-o Dpkg::Options::=--force-confold -o Dpkg::Options::=--force-confdef'

# Full upgrade ensures libc++ and all shared dependencies match ffmpeg's build
pkg update -y
pkg upgrade -y $APT_OPTS

# Install packages
pkg install python ffmpeg termux-api -y $APT_OPTS

# Verify ffmpeg links correctly; reinstall automatically if a symbol error occurs
if ! ffmpeg -version >/dev/null 2>&1; then
    echo "FFmpeg library mismatch detected. Reinstalling ffmpeg..."
    pkg install --reinstall ffmpeg -y $APT_OPTS
fi

echo "=== 3. Installing Python Dependencies ==="
# Termux manages pip packages through system break flags
pip install --break-system-packages flask flask-cors yt-dlp

echo "=== 4. Creating Global Command ==="
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"

cat <<EOF > "$PREFIX/bin/yt-downloader"
#!/data/data/com.termux/files/usr/bin/bash
echo "Acquiring wake lock to prevent background sleep..."
termux-wake-lock

echo "Starting YouTube Downloader..."
(sleep 2 && am start -a android.intent.action.VIEW -d "http://127.0.0.1:5000") &

# Run server from the installation directory
python "$INSTALL_DIR/server.py"

# Release lock when closed
termux-wake-unlock
EOF

chmod +x "$PREFIX/bin/yt-downloader"

echo ""
echo "=========================================="
echo " Setup Complete!"
echo " From now on, just type: yt-downloader"
echo "=========================================="

