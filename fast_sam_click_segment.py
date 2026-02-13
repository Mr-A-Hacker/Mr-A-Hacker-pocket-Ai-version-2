#!/usr/bin/env python3
"""
Live click-to-segment using Fast SAM on the Hailo hat.

- Runs Fast SAM continuously on the camera stream (live segmentation).
- Click on an object: only that object’s mask is overlaid (not the whole image).
- Uses Hailo inference and hailo-apps instance_segmentation post-processing (fast arch).

Usage:
  source hailo-apps/setup_env.sh
  python fast_sam_click_segment.py [--hef path/to/fast_sam_s.hef] [--fps 5]

Requirements: hailo-apps, opencv-python, numpy. On RPi: picamera2.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

# Project root and hailo-apps
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR
HAILO_APPS_ROOT = REPO_ROOT / "hailo-apps"
if not HAILO_APPS_ROOT.is_dir():
    HAILO_APPS_ROOT = REPO_ROOT / "hailo_apps"  # fallback if run from inside hailo-apps
if str(HAILO_APPS_ROOT) not in sys.path:
    sys.path.insert(0, str(HAILO_APPS_ROOT))

# After path fix, import hailo-apps components
try:
    from hailo_apps.python.core.common.hailo_inference import HailoInfer
    from hailo_apps.python.core.common.toolbox import default_preprocess, load_json_file
    from hailo_apps.python.core.common.hailo_logger import get_logger
except ImportError as e:
    print("Failed to import hailo-apps. Run from project root with: source hailo-apps/setup_env.sh", file=sys.stderr)
    raise SystemExit(1) from e

# Instance segmentation postprocess (Fast SAM uses "fast" arch = yolov8_seg_postprocess)
INSTANCE_SEG_DIR = HAILO_APPS_ROOT / "hailo_apps" / "python" / "standalone_apps" / "instance_segmentation"
if not INSTANCE_SEG_DIR.is_dir():
    INSTANCE_SEG_DIR = REPO_ROOT / "hailo-apps" / "hailo_apps" / "python" / "standalone_apps" / "instance_segmentation"
if str(INSTANCE_SEG_DIR) not in sys.path:
    sys.path.insert(0, str(INSTANCE_SEG_DIR))
try:
    from post_process.postprocessing import inference_result_handler, decode_and_postprocess
except ImportError:
    inference_result_handler = None
    decode_and_postprocess = None

logger = get_logger(__name__)

# Default paths (HEF in project root; config from instance_seg or local fallback)
DEFAULT_HEF = REPO_ROOT / "fast_sam_s.hef"
DEFAULT_CONFIG = INSTANCE_SEG_DIR / "config.json" if (INSTANCE_SEG_DIR / "config.json").is_file() else REPO_ROOT / "fast_sam_config.json"

# Fast SAM has a single "object" class
FAST_SAM_LABELS = ["object"]

# Model input size (from config "fast" -> input_shape)
MODEL_W, MODEL_H = 640, 640

# Live inference rate (Hz)
SEGMENT_FPS = 5


def parse_args():
    p = argparse.ArgumentParser(description="Click on the video to run Fast SAM segmentation (Hailo).")
    p.add_argument("--hef", type=Path, default=DEFAULT_HEF, help="Path to fast_sam_s.hef")
    p.add_argument("--config", type=Path, default=None, help="Path to instance_seg config.json (default: hailo-apps standalone config)")
    p.add_argument("--width", type=int, default=640, help="Camera width")
    p.add_argument("--height", type=int, default=480, help="Camera height")
    p.add_argument("--no-pi", action="store_true", help="Force USB camera (OpenCV) even on Raspberry Pi")
    p.add_argument("--fps", type=float, default=SEGMENT_FPS, help="Segmentation inference rate (Hz)")
    return p.parse_args()


def get_camera(args):
    """Return (capture, release_func). Prefer Picamera2 on RPi."""
    use_pi = not args.no_pi
    if use_pi:
        try:
            from picamera2 import Picamera2
            picam2 = Picamera2()
            # Prefer BGR888 so OpenCV gets correct colors (avoids bluish tint)
            try:
                cfg = picam2.create_preview_configuration(
                    main={"size": (args.width, args.height), "format": "BGR888"}
                )
                picam2.configure(cfg)
                need_bgr_convert = False
            except Exception:
                cfg = picam2.create_preview_configuration(
                    main={"size": (args.width, args.height), "format": "RGB888"}
                )
                picam2.configure(cfg)
                need_bgr_convert = True
            picam2.start()

            class PiCapture:
                def read(self):
                    try:
                        arr = picam2.capture_array()
                        if arr is None:
                            return False, None
                        if len(arr.shape) == 2:
                            arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
                        elif need_bgr_convert and arr.shape[2] == 3:
                            arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
                        return True, arr
                    except Exception:
                        return False, None
                def release(self):
                    try:
                        picam2.stop()
                        picam2.close()
                    except Exception:
                        pass

            cap = PiCapture()
            return cap, cap.release
        except Exception as e:
            logger.warning("Picamera2 not available: %s. Falling back to OpenCV.", e)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open camera (OpenCV).")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    def release():
        cap.release()
    return cap, release


def run_inference_and_decode(hailo_infer, config_data, frame_bgr, nms_postprocess_enabled):
    """Run Fast SAM on one BGR frame. Returns (frame_rgb, decoded_detections_dict or None)."""
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    preprocessed = default_preprocess(frame_rgb, MODEL_W, MODEL_H)
    input_batch = [preprocessed]
    result_holder = [None]

    def callback(completion_info, bindings_list):
        if completion_info.exception:
            logger.error("Inference error: %s", completion_info.exception)
            return
        bindings = bindings_list[0]
        if len(bindings._output_names) == 1:
            result = bindings.output().get_buffer()
        else:
            result = {
                name: np.expand_dims(bindings.output(name).get_buffer(), axis=0)
                for name in bindings._output_names
            }
        result_holder[0] = result

    hailo_infer.run(input_batch, callback)
    if hailo_infer.last_infer_job is not None:
        hailo_infer.last_infer_job.wait(10000)
    raw_result = result_holder[0]
    if raw_result is None:
        return frame_rgb, None
    if nms_postprocess_enabled or decode_and_postprocess is None:
        return frame_rgb, None
    try:
        decoded = decode_and_postprocess(raw_result, config_data, "fast")
        return frame_rgb, decoded
    except Exception as e:
        logger.warning("decode_and_postprocess failed: %s", e)
        return frame_rgb, None


def get_detection_at_click(detections, original_h, original_w, click_x, click_y, config_data, arch="fast"):
    """Find which detection contains (click_x, click_y). Returns (idx, original_boxes, masks, pad_h, pad_w, ...) or None."""
    if detections is None:
        return None
    boxes_arr = detections.get("detection_boxes")
    if boxes_arr is None or (hasattr(boxes_arr, "__len__") and len(boxes_arr) == 0):
        return None
    vis = config_data.get("visualization_params", {})
    score_thres = vis.get("score_thres", 0.25)
    mask_thresh = vis.get("mask_thresh", 0.4)
    input_h = config_data[arch]["input_shape"][0]
    input_w = config_data[arch]["input_shape"][1]
    scale_ratio = min(input_w / original_w, input_h / original_h)
    resized_w = int(round(original_w * scale_ratio))
    resized_h = int(round(original_h * scale_ratio))
    pad_w = (input_w - resized_w) // 2
    pad_h = (input_h - resized_h) // 2

    boxes = detections["detection_boxes"].copy()
    masks = detections["mask"] > mask_thresh
    scores = np.asarray(detections["detection_scores"])
    keep = scores > score_thres
    boxes = boxes[keep]
    masks = masks[keep]
    if len(boxes) == 0:
        return None
    # Decode to original image coords
    boxes[:, [0, 2]] = (boxes[:, [0, 2]] * input_w - pad_w) / scale_ratio
    boxes[:, [1, 3]] = (boxes[:, [1, 3]] * input_h - pad_h) / scale_ratio
    boxes[:, [0, 2]] = np.clip(boxes[:, [0, 2]], 0, original_w - 1)
    boxes[:, [1, 3]] = np.clip(boxes[:, [1, 3]], 0, original_h - 1)
    for idx in range(len(boxes)):
        x1, y1, x2, y2 = boxes[idx]
        if x1 <= click_x <= x2 and y1 <= click_y <= y2:
            return (idx, boxes, masks, pad_h, pad_w, input_h, input_w, scale_ratio)
    return None


def draw_single_mask_overlay(frame_bgr, mask_640, pad_h, pad_w, input_h, input_w, original_h, original_w, color, alpha=0.5):
    """Draw one mask (in 640x640 letterbox space) onto the BGR frame in original coords."""
    mask_crop = mask_640[pad_h : input_h - pad_h, pad_w : input_w - pad_w]
    if mask_crop.size == 0:
        return frame_bgr
    mask_orig = cv2.resize(mask_crop.astype(np.uint8), (original_w, original_h), interpolation=cv2.INTER_NEAREST)
    if len(mask_orig.shape) == 2:
        mask_2d = mask_orig
    else:
        mask_2d = mask_orig.squeeze()
    color_bgr = np.array([int(color[2]), int(color[1]), int(color[0])], dtype=np.uint8)
    out = frame_bgr.copy()
    blend = (1.0 - alpha) * frame_bgr.astype(np.float32) + alpha * color_bgr
    out[mask_2d > 0] = blend[mask_2d > 0].astype(np.uint8)
    return out


def main():
    args = parse_args()

    hef_path = args.hef
    if not hef_path.is_file():
        logger.error("HEF not found: %s", hef_path)
        sys.exit(1)

    config_path = args.config or DEFAULT_CONFIG
    if not config_path.is_file():
        logger.error("Config not found: %s. Use --config path/to/config.json or ensure fast_sam_config.json exists.", config_path)
        sys.exit(1)
    config_data = load_json_file(str(config_path))

    # Ensure "fast" and visualization_params exist
    if "fast" not in config_data:
        logger.error("Config must contain 'fast' key (Fast SAM arch). Use instance_segmentation/config.json.")
        sys.exit(1)
    if "visualization_params" not in config_data:
        config_data["visualization_params"] = {"score_thres": 0.25, "mask_thresh": 0.4, "mask_alpha": 0.5, "max_boxes_to_draw": 50}

    logger.info("Loading Hailo model: %s", hef_path)
    hailo_infer = HailoInfer(str(hef_path), batch_size=1, output_type="FLOAT32")
    nms_postprocess_enabled = hailo_infer.is_nms_postprocess_enabled()
    logger.info("NMS postprocess (in-HEF): %s", nms_postprocess_enabled)

    try:
        cap, release_camera = get_camera(args)
    except Exception as e:
        logger.exception("Camera init failed")
        sys.exit(1)

    latest_inference = [None]  # (frame_bgr, detections) from latest inference run
    last_click_xy = [None]  # (x, y) when set: run inference and show that object's mask; when None: no inference
    vis_params = config_data.get("visualization_params", {})
    mask_alpha = vis_params.get("mask_alpha", 0.5)
    frame_interval = max(1, int(30 / max(0.5, min(15.0, args.fps))))
    frame_count = 0

    def on_mouse(event, x, y, _flags, _param):
        if event == cv2.EVENT_LBUTTONDOWN:
            last_click_xy[0] = (int(x), int(y))

    window_name = "Fast SAM - Click to segment, C to unclick"
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, on_mouse)

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            frame_count += 1
            # Only run segmentation while user has clicked an object (live updates until they unclick)
            if last_click_xy[0] is not None and frame_count % frame_interval == 0:
                try:
                    frame_rgb, decoded = run_inference_and_decode(
                        hailo_infer, config_data, frame, nms_postprocess_enabled
                    )
                    if decoded is not None:
                        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                        latest_inference[0] = (frame_bgr, decoded)
                except Exception as e:
                    logger.exception("Inference failed: %s", e)

            # When user unclicks (C), stop showing old segmentation
            if last_click_xy[0] is None:
                latest_inference[0] = None

            click = last_click_xy[0]
            if click is None:
                show = frame
                cv2.putText(show, "Click an object to segment | Q: quit", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            else:
                data = latest_inference[0]
                if data is None:
                    show = frame
                    cv2.putText(show, "Segmenting...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                else:
                    frame_bgr, detections = data
                    show = frame_bgr.copy()
                    h, w = show.shape[:2]
                    hit = get_detection_at_click(detections, h, w, click[0], click[1], config_data, "fast")
                    if hit is not None:
                        idx, original_boxes, masks, pad_h, pad_w, input_h, input_w, _ = hit
                        color = np.array([0, 255, 0], dtype=np.float64)
                        show = draw_single_mask_overlay(
                            show, masks[idx], pad_h, pad_w, input_h, input_w, h, w, color, mask_alpha
                        )
                    cv2.putText(show, "Live segment | C: unclick (stop) | Q: quit", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            cv2.imshow(window_name, show)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:
                break
            if key == ord("c"):
                last_click_xy[0] = None
    finally:
        release_camera()
        cv2.destroyAllWindows()
        hailo_infer.close()
    logger.info("Done.")


if __name__ == "__main__":
    main()
