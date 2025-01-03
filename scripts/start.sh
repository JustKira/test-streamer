#!/bin/bash
# RTSP server details
RTSP_URL="rtsp://mediamtx:8554"
# Directory containing videos
VIDEOS_DIR="/videos"

# Loop through all files in the videos directory
for file in "$VIDEOS_DIR"/*; do
  if [[ -f "$file" ]]; then
    FILENAME=$(basename "$file")
    RTSP_PATH="${FILENAME%.*}"  # Use the filename as the unique path
    echo "Streaming $file to $RTSP_URL/$RTSP_PATH"
    ffmpeg -re -stream_loop -1 -i "$file" -c copy -f rtsp "$RTSP_URL/$RTSP_PATH" &
  fi
done

# Wait indefinitely to keep the container running
wait
