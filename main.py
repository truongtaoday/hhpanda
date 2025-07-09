# main.py - Complete Flask M3U8 Downloader for IDX
import os
import sys
import requests
import subprocess
import uuid
import re
import shutil
from urllib.parse import urljoin, urlparse
from threading import Thread
from flask import Flask, request, render_template_string, send_from_directory, jsonify, redirect, url_for

# Flask app setup
app = Flask(__name__)

# HTML Templates as strings (để tránh cần tạo folder templates)
INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>M3U8 Video Downloader</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            max-width: 500px;
            width: 100%;
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 2.5em;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 600;
        }
        input[type="text"], input[type="url"] {
            width: 100%;
            padding: 15px;
            border: 2px solid #e1e1e1;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        input[type="text"]:focus, input[type="url"]:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .submit-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .submit-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        .error {
            background: #fee;
            color: #c33;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            border: 1px solid #fcc;
        }
        .info {
            background: #f0f8ff;
            color: #0066cc;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            border: 1px solid #cce7ff;
        }
        .help-text {
            font-size: 12px;
            color: #777;
            margin-top: 5px;
        }
        @media (max-width: 600px) {
            .container {
                padding: 20px;
                margin: 10px;
            }
            h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 M3U8 Downloader</h1>
        
        {% if error %}
        <div class="error">
            <strong>❌ Lỗi:</strong> {{ error }}
        </div>
        {% endif %}
        
        <div class="info">
            <strong>ℹ️ Hướng dẫn:</strong> Nhập URL file M3U8 và tên file để tải video về máy
        </div>
        
        <form action="/download" method="post" id="downloadForm">
            <div class="form-group">
                <label for="url">🔗 URL M3U8:</label>
                <input type="url" id="url" name="url" required 
                       placeholder="https://example.com/video.m3u8"
                       value="{{ request.form.get('url', '') }}">
                <div class="help-text">URL phải kết thúc bằng .m3u8</div>
            </div>
            
            <div class="form-group">
                <label for="filename">📁 Tên file (không cần .mp4):</label>
                <input type="text" id="filename" name="filename" required 
                       placeholder="video_cua_toi"
                       value="{{ request.form.get('filename', '') }}">
                <div class="help-text">Chỉ sử dụng chữ cái, số, gạch ngang và gạch dưới</div>
            </div>
            
            <div class="form-group">
                <label for="referer">🔗 Referer (tùy chọn):</label>
                <input type="url" id="referer" name="referer" 
                       placeholder="https://hhpanda.ad"
                       value="{{ request.form.get('referer', 'https://hhpanda.ad') }}">
                <div class="help-text">Trang web nguồn</div>
            </div>
            
            <button type="submit" class="submit-btn" id="submitBtn">
                🚀 Bắt đầu tải
            </button>
        </form>
    </div>

    <script>
        document.getElementById('downloadForm').addEventListener('submit', function(e) {
            const url = document.getElementById('url').value.trim();
            const filename = document.getElementById('filename').value.trim();
            const submitBtn = document.getElementById('submitBtn');
            
            if (!url || !filename) {
                e.preventDefault();
                alert('Vui lòng điền đầy đủ thông tin!');
                return;
            }
            

            }
            
            submitBtn.innerHTML = '⏳ Đang xử lý...';
            submitBtn.disabled = true;
        });
    </script>
</body>
</html>
"""

PROGRESS_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Đang tải - M3U8 Downloader</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            max-width: 500px;
            width: 100%;
            text-align: center;
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
            font-size: 2.5em;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 20px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(45deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.3s ease;
        }
        .progress-percent {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }
        .status-message {
            font-size: 16px;
            color: #666;
            margin: 15px 0;
        }
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #e0e0e0;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .success {
            color: #28a745;
            font-weight: bold;
        }
        .error {
            color: #dc3545;
            font-weight: bold;
        }
        .download-btn {
            display: inline-block;
            padding: 15px 30px;
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
            text-decoration: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            margin: 20px 10px;
        }
        .back-btn {
            display: inline-block;
            padding: 12px 25px;
            background: #6c757d;
            color: white;
            text-decoration: none;
            border-radius: 10px;
            font-size: 16px;
            margin: 10px;
        }
        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 Đang tải video</h1>
        
        <div class="progress-bar">
            <div class="progress-fill" id="progressFill"></div>
        </div>
        <div class="progress-percent" id="progressPercent">0%</div>
        <div class="status-message" id="statusMessage">Đang khởi tạo...</div>
        
        <div class="spinner" id="spinner"></div>
        
        <div id="downloadSection" class="hidden">
            <p class="success">✅ Tải xuống hoàn tất!</p>
            <a href="#" id="downloadLink" class="download-btn">📥 Tải về máy</a>
        </div>
        
        <div id="errorSection" class="hidden">
            <p class="error" id="errorMessage">❌ Có lỗi xảy ra</p>
        </div>
        
        <a href="/" class="back-btn">🔙 Về trang chủ</a>
    </div>

    <script>
        const taskId = '{{ task_id }}';
        const progressFill = document.getElementById('progressFill');
        const progressPercent = document.getElementById('progressPercent');
        const statusMessage = document.getElementById('statusMessage');
        const spinner = document.getElementById('spinner');
        const downloadSection = document.getElementById('downloadSection');
        const downloadLink = document.getElementById('downloadLink');
        const errorSection = document.getElementById('errorSection');
        const errorMessage = document.getElementById('errorMessage');
        
        function updateProgress() {
            fetch(`/api/progress/${taskId}`)
                .then(response => response.json())
                .then(data => {
                    const percent = data.percent || 0;
                    const status = data.status || 'Đang xử lý...';
                    
                    progressFill.style.width = `${percent}%`;
                    progressPercent.textContent = `${percent}%`;
                    statusMessage.textContent = status;
                    
                    if (data.error) {
                        spinner.style.display = 'none';
                        errorSection.classList.remove('hidden');
                        errorMessage.textContent = `❌ ${status}`;
                        return;
                    }
                    
                    if (percent >= 100 && data.file) {
                        spinner.style.display = 'none';
                        downloadSection.classList.remove('hidden');
                        downloadLink.href = `/downloaded/${data.file}`;
                        fetch(`/cleanup/${taskId}`, {method: 'POST'});
                        return;
                    }
                    
                    setTimeout(updateProgress, 1000);
                })
                .catch(error => {
                    console.error('Error:', error);
                    spinner.style.display = 'none';
                    errorSection.classList.remove('hidden');
                    errorMessage.textContent = '❌ Lỗi kết nối server';
                });
        }
        
        updateProgress();
    </script>
</body>
</html>
"""

# M3U8 Downloader Class
class M3U8Downloader:
    def __init__(self):
        self.progress = {}
        
    def download_m3u8(self, m3u8_url, filename, referer="https://hhpanda.ad", task_id=None):
        """Download M3U8 video with progress tracking"""
        try:
            os.makedirs("uploads", exist_ok=True)
            output_dir = os.path.join("uploads", filename)
            os.makedirs(output_dir, exist_ok=True)
            
            headers = {"Referer": referer}
            
            if task_id:
                self.progress[task_id] = {"status": "Đang tải danh sách...", "percent": 10}
            
            response = requests.get(m3u8_url, headers=headers, timeout=30)
            response.raise_for_status()
            m3u8_data = response.text
            
            # Get TS file URLs
            ts_urls = []
            for line in m3u8_data.splitlines():
                if line.startswith("#") or not line.strip():
                    continue
                ts_url = line if line.startswith("http") else urljoin(m3u8_url, line)
                ts_urls.append(ts_url)
            
            if not ts_urls:
                raise Exception("Không tìm thấy file video trong M3U8")
            
            if task_id:
                self.progress[task_id] = {"status": f"Tìm thấy {len(ts_urls)} file. Đang tải...", "percent": 20}
            
            # Download TS files
            ts_files = []
            for i, ts_url in enumerate(ts_urls):
                filepath = os.path.join(output_dir, f"segment_{i:04d}.ts")
                
                try:
                    r = requests.get(ts_url, headers=headers, timeout=30)
                    r.raise_for_status()
                    
                    with open(filepath, 'wb') as f:
                        f.write(r.content)
                    
                    ts_files.append(filepath)
                    
                    if task_id:
                        progress_percent = 20 + (i + 1) / len(ts_urls) * 60
                        self.progress[task_id] = {
                            "status": f"Tải file {i+1}/{len(ts_urls)}", 
                            "percent": int(progress_percent)
                        }
                        
                except Exception as e:
                    print(f"Lỗi tải file {ts_url}: {str(e)}")
                    continue
            
            if not ts_files:
                raise Exception("Không tải được file nào")
            
            # Create concat file
            concat_file = os.path.join(output_dir, "file_list.txt")
            with open(concat_file, "w", encoding="utf-8") as f:
                for file in ts_files:
                    f.write(f"file '{os.path.basename(file)}'\n")
            
            if task_id:
                self.progress[task_id] = {"status": "Xử lý header PNG...", "percent": 85}
            
            # Remove PNG headers
            for file in ts_files:
                self.remove_png_header(file)
            
            if task_id:
                self.progress[task_id] = {"status": "Đang ghép video...", "percent": 90}
            
            # Check if ffmpeg is available
            try:
                subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            except:
                # If ffmpeg not available, just concatenate files
                output_mp4 = os.path.join("uploads", f"{filename}.mp4")
                with open(output_mp4, 'wb') as outfile:
                    for file in ts_files:
                        with open(file, 'rb') as infile:
                            outfile.write(infile.read())
            else:
                # Use ffmpeg for better quality
                output_mp4 = os.path.join("uploads", f"{filename}.mp4")
                cmd = [
                    "ffmpeg", "-f", "concat", "-safe", "0",
                    "-i", concat_file, "-c", "copy", output_mp4, "-y"
                ]
                
                result = subprocess.run(cmd, cwd=output_dir, capture_output=True, text=True)
                
                if result.returncode != 0:
                    # Fallback to simple concatenation
                    with open(output_mp4, 'wb') as outfile:
                        for file in ts_files:
                            with open(file, 'rb') as infile:
                                outfile.write(infile.read())
            
            # Cleanup temp files
            try:
                shutil.rmtree(output_dir)
            except:
                pass
            
            if task_id:
                self.progress[task_id] = {"status": "Hoàn thành!", "percent": 100, "file": f"{filename}.mp4"}
            
            return output_mp4
            
        except Exception as e:
            if task_id:
                self.progress[task_id] = {"status": f"Lỗi: {str(e)}", "percent": 0, "error": True}
            raise e
    
    def remove_png_header(self, filepath):
        """Remove PNG header from TS files if present"""
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            
            png_header = b'\x89PNG\r\n\x1a\n'
            if content.startswith(png_header):
                with open(filepath, 'wb') as f:
                    f.write(content[8:])
        except Exception as e:
            print(f"Lỗi xử lý header PNG: {str(e)}")
    
    def download_async(self, m3u8_url, filename, referer="https://hhpanda.ad", task_id=None):
        """Download M3U8 in background thread"""
        thread = Thread(target=self.download_m3u8, args=(m3u8_url, filename, referer, task_id))
        thread.daemon = True
        thread.start()
        return thread
    
    def get_progress(self, task_id):
        """Get download progress"""
        return self.progress.get(task_id, {"status": "Không tìm thấy", "percent": 0})
    
    def cleanup_progress(self, task_id):
        """Clean up progress tracking"""
        if task_id in self.progress:
            del self.progress[task_id]

# Global downloader instance
downloader = M3U8Downloader()

# Utility functions


def sanitize_filename(filename):
    """Sanitize filename"""
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.strip('. ')
    if not filename:
        filename = "video"
    return filename

# Flask Routes
@app.route('/')
def index():
    return render_template_string(INDEX_TEMPLATE)

@app.route('/download', methods=["POST"])
def download():
    try:
        m3u8_url = request.form.get("url", "").strip()
        filename = request.form.get("filename", "").strip()
        referer = request.form.get("referer", "https://hhpanda.ad").strip()
        
        if not m3u8_url:
            return render_template_string(INDEX_TEMPLATE, error="Vui lòng nhập URL M3U8")
        
        
        if not filename:
            return render_template_string(INDEX_TEMPLATE, error="Vui lòng nhập tên file")
        
        filename = sanitize_filename(filename)
        task_id = str(uuid.uuid4())
        
        downloader.download_async(m3u8_url, filename, referer, task_id)
        
        return redirect(url_for('progress', task_id=task_id))
        
    except Exception as e:
        return render_template_string(INDEX_TEMPLATE, error=f"Lỗi: {str(e)}")

@app.route('/progress/<task_id>')
def progress(task_id):
    return render_template_string(PROGRESS_TEMPLATE, task_id=task_id)

@app.route('/api/progress/<task_id>')
def api_progress(task_id):
    progress_data = downloader.get_progress(task_id)
    return jsonify(progress_data)

@app.route('/downloaded/<path:filename>')
def serve_file(filename):
    try:
        if not filename.endswith('.mp4'):
            return "File không hợp lệ", 400
        
        file_path = os.path.join("uploads", filename)
        if not os.path.exists(file_path):
            return "File không tồn tại", 404
        
        return send_from_directory("uploads", filename, as_attachment=True)
    except Exception as e:
        return f"Lỗi tải file: {str(e)}", 500

@app.route('/cleanup/<task_id>', methods=['POST'])
def cleanup(task_id):
    """Clean up progress tracking"""
    downloader.cleanup_progress(task_id)
    return jsonify({"status": "cleaned"})

@app.errorhandler(404)
def not_found(error):
    return render_template_string(INDEX_TEMPLATE, error="Trang không tìm thấy"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template_string(INDEX_TEMPLATE, error="Lỗi server nội bộ"), 500

if __name__ == '__main__':
    # Create uploads directory
    os.makedirs("uploads", exist_ok=True)
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)