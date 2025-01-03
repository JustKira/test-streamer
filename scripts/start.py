#!/usr/bin/env python3

"""
Stream Manager Service for Media Streaming

This module provides a robust solution for managing multiple media streams through FFmpeg.
It supports various input types (files, RTSP, RTMP) and handles their conversion/relay
to a MediaMTX RTSP server.

Typical usage:
    python start.py

The service reads stream configurations from a YAML file and manages FFmpeg processes
for each stream, providing proper process management and error handling.

Requirements:
    - FFmpeg installed in the system
    - Python 3.7+
    - PyYAML package
"""

import yaml
import subprocess
import os
import signal
import sys
import time
from typing import Dict, List, Optional, Union
import logging
from dataclasses import dataclass
from pathlib import Path
from enum import Enum, auto

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StreamType(Enum):
    """Enumeration of supported stream types."""
    FILE = auto()
    RTSP = auto()
    RTMP = auto()
    HLS = auto()
    UDP = auto()

@dataclass
class StreamConfig:
    """Data class representing a stream configuration.

    Attributes:
        name: Unique identifier for the stream
        type: Type of stream (file, rtsp, rtmp, etc.)
        input: Input URL or file path
        output_path: Path where the stream will be published on the RTSP server
        options: Optional FFmpeg parameters for this stream
    """
    name: str
    type: StreamType
    input: str
    output_path: str
    options: Optional[Dict] = None

class FFmpegProcess:
    """Manages an individual FFmpeg process.

    This class handles the lifecycle of a single FFmpeg process, including
    startup, monitoring, and shutdown.

    Attributes:
        config: StreamConfig object containing stream configuration
        process: Subprocess object for the FFmpeg process
        last_restart: Timestamp of last restart attempt
    """

    def __init__(self, config: StreamConfig, rtsp_server: str):
        """Initialize FFmpeg process manager.

        Args:
            config: StreamConfig object with stream details
            rtsp_server: Base URL of the RTSP server
        """
        self.config = config
        self.rtsp_server = rtsp_server
        self.process: Optional[subprocess.Popen] = None
        self.last_restart = 0
        self.max_restarts = 5
        self.restart_count = 0
        self.restart_interval = 60  # seconds

    def _build_command(self) -> List[str]:
        """Construct FFmpeg command based on stream configuration.

        Returns:
            List of command arguments for FFmpeg

        Raises:
            ValueError: If stream type is not supported
        """
        base_command = ['ffmpeg', '-re']

        # Stream type specific parameters
        if self.config.type == StreamType.FILE:
            base_command.extend([
                '-stream_loop', '-1',
                '-i', self.config.input,
                '-c:v', 'libx264',
                '-preset', 'veryfast',
                '-c:a', 'aac',
                '-b:v', '2M',  # 2 Mbps video bitrate
                '-bufsize', '4M',
                '-maxrate', '2.5M',
                '-g', '50',  # Keyframe interval
                '-keyint_min', '25'
            ])
        elif self.config.type == StreamType.RTSP:
            base_command.extend([
                '-rtsp_transport', 'tcp',
                '-i', self.config.input,
                '-c', 'copy',
                '-f', 'rtsp',
                '-rtsp_transport', 'tcp'
            ])
        elif self.config.type == StreamType.RTMP:
            base_command.extend([
                '-i', self.config.input,
                '-c', 'copy'
            ])
        else:
            raise ValueError(f"Unsupported stream type: {self.config.type}")

        # Add custom options if specified
        if self.config.options:
            for key, value in self.config.options.items():
                base_command.extend([f"-{key}", str(value)])

        # Add output options
        base_command.extend([
            '-f', 'rtsp',
            f'{self.rtsp_server}/{self.config.output_path}'
        ])

        return base_command

    def start(self) -> bool:
        """Start the FFmpeg process.

        Returns:
            bool: True if process started successfully, False otherwise
        """
        try:
            command = self._build_command()
            logger.info(f"Starting stream: {self.config.name}")
            logger.debug(f"Command: {' '.join(command)}")

            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to start stream {self.config.name}: {e}")
            return False

    def stop(self):
        """Gracefully stop the FFmpeg process."""
        if self.process:
            logger.info(f"Stopping stream: {self.config.name}")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

    def is_alive(self) -> bool:
        """Check if the FFmpeg process is still running.

        Returns:
            bool: True if process is running, False otherwise
        """
        return self.process is not None and self.process.poll() is None

class StreamManager:
    """Main class for managing multiple media streams.

    This class handles the lifecycle of multiple FFmpeg processes, including
    configuration loading, process management, and error recovery.

    Attributes:
        rtsp_server: Base URL of the RTSP server
        streams: Dictionary of active stream processes
        config: Loaded stream configurations
    """

    def __init__(self, config_path: Union[str, Path], rtsp_server: str):
        """Initialize the stream manager.

        Args:
            config_path: Path to the YAML configuration file
            rtsp_server: Base URL of the RTSP server
        """
        self.rtsp_server = rtsp_server
        self.streams: Dict[str, FFmpegProcess] = {}
        self.config = self._load_config(config_path)
        self._setup_signal_handlers()

    def _load_config(self, config_path: Union[str, Path]) -> Dict:
        """Load and validate stream configurations from YAML file.

        Args:
            config_path: Path to configuration file

        Returns:
            Dict containing validated configuration

        Raises:
            SystemExit: If configuration file cannot be loaded or is invalid
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            # Validate configuration
            if not isinstance(config, dict) or 'streams' not in config:
                raise ValueError("Invalid configuration format")

            return config
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            sys.exit(1)

    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received signal {signum}, shutting down...")
        self.cleanup()
        sys.exit(0)

    def start_all_streams(self):
        """Start all configured streams."""
        for stream_config in self.config['streams']:
            try:
                stream = StreamConfig(
                    name=stream_config['name'],
                    type=StreamType[stream_config['type'].upper()],
                    input=stream_config['input'],
                    output_path=stream_config['output_path'],
                    options=stream_config.get('options')
                )
                process = FFmpegProcess(stream, self.rtsp_server)
                if process.start():
                    self.streams[stream.name] = process
            except Exception as e:
                logger.error(f"Failed to start stream {stream_config['name']}: {e}")

    def monitor_streams(self):
        """Monitor and restart failed streams if necessary."""
        while True:
            for name, process in self.streams.items():
                if not process.is_alive():
                    logger.warning(f"Stream {name} has died, attempting restart...")
                    if process.restart_count < process.max_restarts:
                        process.restart_count += 1
                        process.start()
                    else:
                        logger.error(f"Stream {name} has failed too many times, giving up")
            time.sleep(5)

    def cleanup(self):
        """Clean up all streams and processes."""
        logger.info("Cleaning up streams...")
        for process in self.streams.values():
            process.stop()

def main():
    """Main entry point for the stream manager service."""
    # Configuration
    RTSP_SERVER = os.getenv('RTSP_SERVER', "rtsp://mediamtx:8554")
    CONFIG_PATH = os.getenv('CONFIG_PATH', "/config/streams.yml")

    try:
        # Create stream manager
        manager = StreamManager(CONFIG_PATH, RTSP_SERVER)

        # Start all streams
        manager.start_all_streams()

        # Monitor streams
        manager.monitor_streams()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
