"""
computer_vision.py — Live video display from ArduCam via Hailo8 HAT.

Includes FrameManager and background thread control for integration with
the web app backend (app.py).

Usage:
    python computer_vision.py         (Standalone test)
    # Or import and control via start_task/stop_task
"""

import sys
import threading
import time
import signal
import numpy as np
from contextlib import contextmanager

import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib

from hailo_apps.python.core.gstreamer.gstreamer_app import (
    GStreamerApp,
    app_callback_class,
    dummy_callback,
)
from hailo_apps.python.core.gstreamer.gstreamer_helper_pipelines import (
    DISPLAY_PIPELINE,
    SOURCE_PIPELINE,
    USER_CALLBACK_PIPELINE,
)
from hailo_apps.python.core.common.core import get_pipeline_parser
from hailo_apps.python.core.common.buffer_utils import get_numpy_from_buffer


# -----------------------------------------------------------------------------------------------
# 1. SHARED MEMORY & UTILS
# -----------------------------------------------------------------------------------------------
class FrameManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._current_frame = None
        self._metadata = {}

    def update(self, frame, metadata={}):
        with self._lock:
            self._current_frame = frame
            self._metadata = metadata

    def get_latest(self):
        with self._lock:
            if self._current_frame is None:
                return None, {}
            return self._current_frame.copy(), self._metadata.copy()

# Global frame manager instance
frame_manager = FrameManager()

def get_latest_frame():
    return frame_manager.get_latest()


# -----------------------------------------------------------------------------------------------
# 2. GLOBAL THREAD CONTROL
# -----------------------------------------------------------------------------------------------
current_thread = None
current_app = None

@contextmanager
def thread_safe_signal_mock():
    """Mock signal.signal if we are NOT in the main thread."""
    if threading.current_thread() is threading.main_thread():
        yield
        return

    original_signal_func = signal.signal
    def no_op(*args, **kwargs): pass
    
    # Patch the module function directly
    signal.signal = no_op
    
    try:
        yield
    finally:
        signal.signal = original_signal_func

def start_task(target_func):
    """Start the GStreamer app in a background thread."""
    global current_thread
    stop_task()
    current_thread = threading.Thread(target=target_func)
    current_thread.daemon = True 
    current_thread.start()

def stop_task():
    """Stop the running GStreamer app and join the thread."""
    global current_app, current_thread
    
    if current_app:
        try:
            # Graceful shutdown sequence
            with thread_safe_signal_mock():
                current_app.shutdown()
        except Exception as e:
            print(f"Error stopping app: {e}")
        current_app = None

    if current_thread and current_thread.is_alive():
        current_thread.join(timeout=2.0)
        current_thread = None
    
    # Delay to ensure camera device is released
    time.sleep(0.5)


# -----------------------------------------------------------------------------------------------
# 3. GSTREAMER APP IMPLEMENTATION
# -----------------------------------------------------------------------------------------------
class GStreamerVideoDisplayApp(GStreamerApp):
    """Simple video display app — source → callback → display, no inference."""

    def __init__(self, app_callback, user_data, parser=None):
        if parser is None:
            parser = get_pipeline_parser()

        # Wrap super().__init__ with our signal mock
        with thread_safe_signal_mock():
            super().__init__(parser, user_data)
        
        # Override app_callback to ensure it's used
        self.app_callback = app_callback
        self.create_pipeline()

    def bus_call(self, bus, message, loop):
        """Treat window-close as a clean shutdown instead of an error."""
        if message.type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            if "Output window was closed" in str(err):
                self.shutdown()
                return True
        return super().bus_call(bus, message, loop)

    def get_pipeline_string(self):
        source = SOURCE_PIPELINE(
            video_source=self.video_source,
            video_width=self.video_width,
            video_height=self.video_height,
            frame_rate=self.frame_rate,
            sync=self.sync,
        )
        user_callback = USER_CALLBACK_PIPELINE()
        display = DISPLAY_PIPELINE(
            video_sink=self.video_sink,
            sync=self.sync,
            show_fps=self.show_fps,
        )

        # Rotate -90° (counterclockwise) then scale to fit 480x800 display.
        # Capture stays at full 1280x720.
        rotate_and_scale = (
            "videoflip method=counterclockwise ! "
            "videoscale ! "
            "video/x-raw, width=480, height=800"
        )

        pipeline_string = (
            f"{source} ! "
            f"{user_callback} ! "
            f"{rotate_and_scale} ! "
            f"{display}"
        )
        return pipeline_string


# -----------------------------------------------------------------------------------------------
# 4. RUNNER FUNCTIONS
# -----------------------------------------------------------------------------------------------
def run_app_safely(app):
    """Run app.run() and handle signals/exceptions."""
    # Hijack signal handlers to prevent GStreamerApp from throwing threading errors
    with thread_safe_signal_mock():
        try:
            app.run()
        except SystemExit:
            pass
        except Exception as e:
            print(f"App run error: {e}")

def run_raw_camera_app():
    """Run the basic raw camera app with display and frame capture."""
    global current_app
    
    # Inject --input rpi flag for standalone logic
    if "--input" not in sys.argv:
        sys.argv = [sys.argv[0], "--input", "rpi"] + sys.argv[1:]

    def app_callback(element, buffer, user_data):
        """Called by GStreamer thread for every frame."""
        try:
            pad = element.get_static_pad("sink")
            caps = pad.get_current_caps()
            if not caps: return Gst.PadProbeReturn.OK
            
            structure = caps.get_structure(0)
            width = structure.get_int("width")[1]
            height = structure.get_int("height")[1]
            # format = structure.get_value("format") # usually "RGB"
            
            # Convert GStreamer buffer to numpy array
            frame = get_numpy_from_buffer(buffer, "RGB", width, height)
            
            if frame is not None:
                # Update FrameManager for web streaming
                frame_manager.update(frame, {})
                
        except Exception as e:
            # print(f"Frame capture error: {e}")
            pass
        return Gst.PadProbeReturn.OK

    user_data = app_callback_class()
    app = GStreamerVideoDisplayApp(app_callback, user_data)
    current_app = app
    
    run_app_safely(app)

# Placeholders aliases for now
run_detection_app = run_raw_camera_app
run_pose_app = run_raw_camera_app


def main():
    run_raw_camera_app()


if __name__ == "__main__":
    main()
