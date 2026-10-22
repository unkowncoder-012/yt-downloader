#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "=== 1. Checking Storage Access ==="
if [ ! -d "$HOME/storage" ]; then
    termux-setup-storage
    sleep 2
else
    echo "Storage access already granted."
fi

echo "=== 2. Updating Repositories & Installing Dependencies ==="
pkg update -y
pkg install python ffmpeg termux-api -y

echo "=== 3. Installing Python Dependencies ==="
# Do NOT upgrade pip here; Termux manages pip through pkg
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

