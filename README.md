###nén file tren ffmpeg trên máy cũ ffmpeg 514
ffmpeg -i input.mp4 -vf scale=1280:720 -c:v h264_nvenc -preset fast input_gpu.mp4
### dùng cho cả google colab
