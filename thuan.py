import requests
import os
import time
import subprocess
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    """Tạo session với retry logic"""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def download_with_retry(session, url, headers, max_retries=3):
    """Tải file với retry logic"""
    for i in range(max_retries):
        try:
            response = session.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            return response.content
        except (requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout) as e:
            if i == max_retries - 1:
                print(f"❌ Lỗi tải {url}: {e}")
                raise
            print(f"⚠️  Thử lại lần {i+1} cho {url}")
            time.sleep(2 ** i)  # Exponential backoff

def remove_png_header(filepath):
    """Xóa PNG header nếu có"""
    try:
        with open(filepath, 'rb') as f:
            content = f.read()

        png_header = b'\x89PNG\r\n\x1a\n'
        if content.startswith(png_header):
            with open(filepath, 'wb') as f:
                f.write(content[8:])
            return True
        return False
    except Exception as e:
        print(f"❌ Lỗi xử lý file {filepath}: {e}")
        return False

def print_progress(current, total, filename=""):
    """Hiển thị thanh tiến trình"""
    percent = (current / total) * 100
    bar_length = 40
    filled_length = int(bar_length * current // total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    print(f'\r📥 [{bar}] {percent:.1f}% ({current}/{total}) {filename}', end='', flush=True)

def main():
    # Nhập từ người dùng
    m3u8_url = input("Nhập URL: ").strip()
    filename = input("Nhập tên file output (không cần đuôi .mp4): ").strip()
    referer = input("Nhập Referer (Enter để dùng mặc định): ").strip() or "https://hhpanda.ad"

    output_dir = filename
    os.makedirs(output_dir, exist_ok=True)

    # Tạo session
    session = create_session()
    headers = {"Referer": referer}

    print("🔍 Đang phân tích M3U8...")
    try:
        m3u8_data = session.get(m3u8_url, headers=headers, timeout=10).text
    except Exception as e:
        print(f"❌ Lỗi tải M3U8: {e}")
        return

    # Lấy danh sách file TS
    ts_urls = []
    for line in m3u8_data.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        ts_url = line if line.startswith("http") else urljoin(m3u8_url, line)
        ts_urls.append(ts_url)

    total_files = len(ts_urls)
    if total_files == 0:
        print("❌ Không tìm thấy file TS nào!")
        return

    print(f"📋 Tìm thấy {total_files} file TS")

    # Tải các file TS
    ts_files = []
    png_headers_found = 0

    for i, ts_url in enumerate(ts_urls, 1):
        filename_ts = f"{i:05d}.ts"  # i là số thứ tự, định dạng 5 chữ số: 00001.ts, 00002.ts...
        filepath = os.path.join(output_dir, filename_ts)

        print_progress(i-1, total_files, filename_ts)

        try:
            content = download_with_retry(session, ts_url, headers)

            with open(filepath, 'wb') as f:
                f.write(content)

            # Kiểm tra và xóa PNG header
            if remove_png_header(filepath):
                png_headers_found += 1

            ts_files.append(filepath)

        except Exception as e:
            print(f"\n❌ Lỗi tải {ts_url}: {e}")
            continue

    print_progress(total_files, total_files, "Hoàn thành!")
    print(f"\n✅ Đã tải {len(ts_files)}/{total_files} file")

    if png_headers_found > 0:
        print(f"🔧 Đã xử lý {png_headers_found} file có PNG header")

    if not ts_files:
        print("❌ Không có file nào được tải thành công!")
        return

    # Tạo file concat
    concat_file = "file_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for file in ts_files:
            f.write(f"file '{file}'\n")

    # Ghép video bằng ffmpeg
    print("🎬 Đang ghép video...")
    output_file = f"{filename}.mp4"

    try:
        cmd = [
            "ffmpeg", "-f", "concat", "-safe", "0",
            "-i", concat_file, "-c", "copy", output_file, "-y"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ Video đã được tạo: {output_file}")

            # Xóa file tạm
            cleanup = True
            if cleanup:
                import shutil
                shutil.rmtree(output_dir)
                os.remove(concat_file)
                print("🧹 Đã xóa file tạm")
        else:
            print(f"❌ Lỗi ffmpeg: {result.stderr}")

    except FileNotFoundError:
        print("❌ Không tìm thấy ffmpeg. Vui lòng cài đặt ffmpeg!")
    except Exception as e:
        print(f"❌ Lỗi ghép video: {e}")

if __name__ == "__main__":
    main()

