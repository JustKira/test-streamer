### **README: Videos Directory**

This directory contains the video files to be streamed by the MediaMTX server. Follow these guidelines to ensure smooth operation and compatibility:

---

### **Instructions**

1. **File Naming**

   - Ensure that video filenames are URL-friendly. Avoid spaces, special characters, or non-ASCII symbols.
   - Use simple names consisting of letters, numbers, hyphens (`-`), or underscores (`_`).

   **Examples:**

   - ✅ `video1.mp4`
   - ✅ `my-video.mp4`
   - ✅ `tutorial_video.mp4`
   - ❌ `my video.mp4`
   - ❌ `video@123!.mp4`

2. **Video Formats**

   - Supported formats include `MP4`, `MKV`, `MOV`, etc., but ensure that the videos use codecs compatible with FFmpeg and the MediaMTX server:
     - **Video Codec:** `H.264` (libx264)
     - **Audio Codec:** `AAC`

3. **Adding Videos**

   - Place your video files into this directory (`videos/`).
   - Example:
     ```
     videos/
     ├── video1.mp4
     ├── video2.mp4
     ├── tutorial.mp4
     ```

4. **Stream URL Naming**

   - Each video will be streamed using its filename (without the extension) as the stream path.
   - Example:
     - File: `video1.mp4`
     - RTSP URL: `rtsp://<YOUR_HOST>:8554/live/video1`
     - HLS URL: `http://<YOUR_HOST>:8888/live/video1/index.m3u8`

5. **Restart After Adding Videos**
   - If you add or update video files, restart the system using:
     ```bash
     docker-compose down
     docker-compose up
     ```
