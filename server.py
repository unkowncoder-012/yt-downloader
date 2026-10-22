from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import yt_dlp
import os
import json
import queue
import threading
import subprocess

app = Flask(__name__)
CORS(app)

# Use standard Android Download folder path
DOWNLOAD_DIR = "/sdcard/Download/YT downloads"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def home():
    return send_file(os.path.join(BASE_DIR, "index.html"))

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"results": []})
    
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'skip_download': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch8:{query}", download=False)
            entries = info.get('entries', [])
            results = []
            for item in entries:
                if item:
                    results.append({
                        'id': item.get('id'),
                        'title': item.get('title'),
                        'uploader': item.get('uploader') or item.get('channel', 'YouTube'),
                        'duration': item.get('duration_string') or '',
                        'url': item.get('url') or f"https://www.youtube.com/watch?v={item.get('id')}",
                        'thumbnail': item.get('thumbnails')[-1]['url'] if item.get('thumbnails') else ''
                    })
            return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download-stream', methods=['POST'])
def download_stream():
    data = request.json
    url = data.get('url', '').strip()
    dl_type = data.get('type', 'single')
    res = data.get('resolution', 'best')

    if not url:
        return jsonify({"error": "URL is required"}), 400

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    def event_stream():
        q = queue.Queue()

        def hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                pct = round((downloaded / total * 100), 1) if total > 0 else 0
                q.put({
                    'status': 'downloading',
                    'percent': pct,
                    'speed': d.get('_speed_str', 'N/A'),
                    'eta': d.get('_eta_str', 'N/A'),
                    'filename': os.path.basename(d.get('filename', ''))
                })
            elif d['status'] == 'finished':
                q.put({'status': 'merging', 'message': 'Download complete. Merging streams...'})

        def worker():
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [hook],
                'merge_output_format': 'mp4',  # Always merge into standard MP4 for Android
            }

            if dl_type == 'audio':
                ydl_opts['format'] = 'ba/b'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
                ydl_opts['outtmpl'] = os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s')
                ydl_opts['noplaylist'] = not ('list=' in url and 'v=' not in url)

            elif dl_type == 'playlist':
                ydl_opts['outtmpl'] = os.path.join(DOWNLOAD_DIR, '%(playlist_title)s', '%(title)s.%(ext)s')
                ydl_opts['format'] = 'bv*+ba/b'
                ydl_opts['yes_playlist'] = True

            else:  # Single Video
                ydl_opts['outtmpl'] = os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s')
                ydl_opts['noplaylist'] = not ('list=' in url and 'v=' not in url)

                if res == 'best':
                    ydl_opts['format'] = 'bv*+ba/b'
                else:
                    ydl_opts['format'] = f'bv*[height<={res}]+ba/b[height<={res}]/b'

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                # Scan storage so it immediately displays in Android Gallery
                subprocess.run(['termux-media-scan', '-r', DOWNLOAD_DIR], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                q.put({'status': 'finished', 'message': 'Saved to Download/YT downloads!'})
            except Exception as err:
                q.put({'status': 'error', 'message': str(err)})
            finally:
                q.put(None)

        threading.Thread(target=worker, daemon=True).start()

        while True:
            item = q.get()
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"

    return Response(event_stream(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
