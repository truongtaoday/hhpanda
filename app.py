from flask import Flask, request, render_template, redirect, url_for, send_file, flash
import os
import requests
from urllib.parse import urljoin
import subprocess

app = Flask(__name__)
app.secret_key = 'secret'  # Để dùng flash

# Đường dẫn thư mục tạm
TEMP_DIR = "downloads"
os.makedirs(TEMP_DIR, exist_ok=True)

def remove_png_header(filepath):
    with open(filepath, 'rb') as f:
        content = f.read()
    png_header = b'\x89PNG\r\n\x1a\n'
    if content.startswith(png_header):
        with open(filepath, 'wb') as f:
            f.write(content[8:])

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        m3u8_url = request.form.get("m3u8_url", "").strip()
        filename = request.form.get("filename", "").strip()
        referer = "https://hhpanda.ad"

        if not m3u8_url:
            flash("Vui lòng nhập URL hợp lệ.", "danger")
            return redirect(url_for('index'))  # Sửa: phải nằm trong điều kiện if

        output_dir = os.path.join(TEMP_DIR, filename)
        os.makedirs(output_dir, exist_ok=True)

        headers = {"Referer": referer}
        try:
            m3u8_data = requests.get(m3u8_url, headers=headers).text
        except Exception as e:
            flash(f"Lỗi tải M3U8: {e}", "danger")
            return redirect(url_for('index'))

        ts_files = []
        for line in m3u8_data.splitlines():
            if line.startswith("#") or not line.strip():
                continue
            ts_url = line if line.startswith("http") else urljoin(m3u8_url, line)
            local_path = os.path.join(output_dir, os.path.basename(ts_url))
            try:
                r = requests.get(ts_url, headers=headers, timeout=10)
                with open(local_path, 'wb') as f:
                    f.write(r.content)
                ts_files.append(local_path)
            except:
                continue

        concat_path = os.path.join(TEMP_DIR, f"{filename}_file_list.txt")
        with open(concat_path, "w", encoding="utf-8") as f:
            for file in ts_files:
                abs_path = os.path.abspath(file).replace("\\", "/")
                f.write(f"file '{abs_path}'\n")

        # Xóa PNG header
        for file in ts_files:
            remove_png_header(file)

        output_mp4 = os.path.join(TEMP_DIR, f"{filename}.mp4")
        cmd = [
            "ffmpeg", "-f", "concat", "-safe", "0",
            "-i", concat_path,
            "-c", "copy", output_mp4, "-y"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
           flash(f"Lỗi ffmpeg: {result.stderr}", "danger")
        else:
           if os.path.exists(output_mp4):
              flash("Video đã được xử lý thành công!", "success")
              return redirect(url_for('download', filename=f"{filename}.mp4"))
           else:
              flash("Lỗi: không tạo được file MP4.", "danger")


    return render_template("index.html")

@app.route("/download/<filename>")
def download(filename):
    path = os.path.join(TEMP_DIR, filename)
    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
