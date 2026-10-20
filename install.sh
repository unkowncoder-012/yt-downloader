#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "=== 1. Requesting Storage Access ==="
termux-setup-storage
sleep 2

echo "=== 2. Installing Core Packages ==="
pkg update -y
pkg install python ffmpeg -y

echo "=== 3. Installing Python Dependencies ==="
pip install --upgrade pip
pip install flask flask-cors yt-dlp

echo "=== 4. Creating Global Command ==="
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"

cat <<LAUNCHER > "$PREFIX/bin/yt-downloader"
#!/data/data/com.termux/files/usr/bin/bash
echo "Starting YouTube Downloader..."
(sleep 2 && am start -a android.intent.action.VIEW -d "http://127.0.0.1:5000") &
python "$INSTALL_DIR/server.py"
LAUNCHER

chmod +x "$PREFIX/bin/yt-downloader"

echo ""
echo "=========================================="
echo " Setup Complete!"
echo " From now on, just type: yt-downloader"
echo "=========================================="
