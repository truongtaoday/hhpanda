###nén file tren ffmpeg trên máy cũ ffmpeg-n5.1.4-18-gdefa085fc8-win64-gpl-5.1.zip
####
ffmpeg -i input.mp4 -vf scale=1280:720 -c:v h264_nvenc -preset fast input_gpu.mp4
nén video 10bit:	!ffmpeg -i v.mp4 -vf scale=1280:720 -pix_fmt yuv420p -c:v hevc_nvenc -preset fast input_gpu.mp4
### dùng cho cả google colab#####
