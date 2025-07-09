# Hướng dẫn cài đặt M3U8 Downloader trên IDX

## 1. Tạo files cần thiết

### Tạo file `requirements.txt`:
```
Flask==2.3.3
requests==2.31.0
```

### Thay thế nội dung file `main.py` bằng code complete ở trên

## 2. Cài đặt dependencies

Trong terminal của IDX, chạy:
```bash
pip install -r requirements.txt
```

## 3. Cài đặt ffmpeg (tùy chọn - để chất lượng tốt hơn)

```bash
# Cách 1: Thử apt-get
sudo apt-get update
sudo apt-get install -y ffmpeg

# Cách 2: Nếu không được, dùng conda
conda install -c conda-forge ffmpeg

# Cách 3: Tải binary
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar -xf ffmpeg-release-amd64-static.tar.xz
sudo mv ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/
```

## 4. Chạy ứng dụng

```bash
python main.py
```

## 5. Các tính năng chính

### ✅ Hoàn chỉnh:
- ✅ Download M3U8 với progress tracking
- ✅ Giao diện web responsive
- ✅ Xử l
