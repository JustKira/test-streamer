### **README: Streaming Media with MediaMTX and FFmpeg**

This document provides clear instructions for developers to set up a MediaMTX RTSP and HLS streaming server, stream videos, and connect to the streams.

---

### **Setup Instructions**

#### **Prerequisites**

- Docker and Docker Compose installed on your machine.
- Video files to stream.

---

### **Directory Structure**

Organize your project directory as follows:

```
project-root/
│
├── docker-compose.yml
├── mediamtx.yml
├── videos/          # Directory for your video files
│   ├── video1.mp4
│   ├── video2.mp4
│   └── video3.mp4
├── scripts/         # Directory for preconfigured scripts (no need for user interaction)
│   └── start.sh
```

---

### **Steps to Use**

#### 1. **Add Your Videos**

Place your video files into the `videos/` directory. For example:

```
videos/
├── video1.mp4
├── video2.mp4
```

#### 2. **Start the System**

Run the following command to start MediaMTX and the FFmpeg streamer:

```bash
docker-compose up
```

- This will:
  - Start the MediaMTX server for RTSP and HLS streaming.
  - Use FFmpeg to stream videos from the `videos/` directory to the MediaMTX server.

#### 3. **Stop the System**

To stop the containers, use:

```bash
docker-compose down
```

---

### **Connecting to the Streams**

#### **RTSP (Low-Latency)**

Use an RTSP-compatible player like VLC to connect to the RTSP stream. The URL format is:

```plaintext
rtsp://<YOUR_HOST>:8554/live/<VIDEO_NAME>
```

- Replace `<YOUR_HOST>` with `localhost` or the IP address of your server.
- Replace `<VIDEO_NAME>` with the name of your video file (without the extension).

**Example:**
If your video file is `video1.mp4` and the server is on `localhost`:

```plaintext
rtsp://localhost:8554/live/video1
```

---

#### **HLS (Browser-Compatible)**

You can access the HLS stream using a browser or HLS-compatible player. The URL format is:

```plaintext
http://<YOUR_HOST>:8888/live/<VIDEO_NAME>/index.m3u8
```

**Example:**
If your video file is `video1.mp4` and the server is on `localhost`:

```plaintext
http://localhost:8888/live/video1/index.m3u8
```

---

### **File Details**

#### `docker-compose.yml`

Defines the services:

- `mediamtx` for RTSP and HLS server.
- `ffmpeg-streamer` for video streaming.

#### `mediamtx.yml`

Custom configuration for MediaMTX (RTSP/HLS server).

#### `start.sh`

Bash script to stream all videos in the `videos/` directory to unique RTSP paths.

---

### **Developer Tips**

#### Logs

- To view logs for the MediaMTX server:
  ```bash
  docker logs mediamtx
  ```
- To view logs for the FFmpeg streamer:
  ```bash
  docker logs ffmpeg-streamer
  ```

#### Debugging

- Ensure the `videos/` directory is properly mounted in the containers.
- Check video compatibility with FFmpeg (`libx264` for video, `aac` for audio).

---

### **Scaling and Testing**

- Add more videos to the `videos/` folder and restart the system with `docker-compose up`.
- Use VLC, a browser, or any HLS/RTSP client to test the streams.
