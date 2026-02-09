import cv2
import numpy as np
from picamera2 import Picamera2
from picamera2.devices import Hailo

# --- CONFIGURATION ---
MODEL_FILE = "/usr/share/hailo-models/yolov8s_h8.hef"
CONFIDENCE_THRESHOLD = 0.45 

COCO_LABELS = {
    0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane',
    5: 'bus', 6: 'train', 7: 'truck', 8: 'boat', 9: 'traffic light',
    10: 'fire hydrant', 11: 'stop sign', 12: 'parking meter', 13: 'bench',
    14: 'bird', 15: 'cat', 16: 'dog', 17: 'horse', 18: 'sheep', 19: 'cow',
    20: 'elephant', 21: 'bear', 22: 'zebra', 23: 'giraffe', 24: 'backpack',
    25: 'umbrella', 26: 'handbag', 27: 'tie', 28: 'suitcase', 29: 'frisbee',
    30: 'skis', 31: 'snowboard', 32: 'sports ball', 33: 'kite', 34: 'baseball bat',
    35: 'baseball glove', 36: 'skateboard', 37: 'surfboard', 38: 'tennis racket',
    39: 'bottle', 40: 'wine glass', 41: 'cup', 42: 'fork', 43: 'knife',
    44: 'spoon', 45: 'bowl', 46: 'banana', 47: 'apple', 48: 'sandwich',
    49: 'orange', 50: 'broccoli', 51: 'carrot', 52: 'hot dog', 53: 'pizza',
    54: 'donut', 55: 'cake', 56: 'chair', 57: 'couch', 58: 'potted plant',
    59: 'bed', 60: 'dining table', 61: 'toilet', 62: 'tv', 63: 'laptop',
    64: 'mouse', 65: 'remote', 66: 'keyboard', 67: 'cell phone', 68: 'microwave',
    69: 'oven', 70: 'toaster', 71: 'sink', 72: 'refrigerator', 73: 'book',
    74: 'clock', 75: 'vase', 76: 'scissors', 77: 'teddy bear', 78: 'hair drier',
    79: 'toothbrush'
}

def draw_detections(frame, results):
    """
    Draws boxes using the 'Squish' logic.
    Includes FIX for split tensors (Boxes vs Classes).
    """
    if not results: 
        return

    # --- DEBUG SECTION ---
    # Print what the Hailo chip actually returned
    # print(f"DEBUG: Received {len(results)} output tensors.")
    # for i, tensor in enumerate(results):
    #     print(f"  Tensor {i} shape: {tensor.shape}")
    # ---------------------

    final_detections = []

    # CASE A: Standard Combined Output (1 Array)
    if len(results) == 1:
        batch = results[0]
        if len(batch.shape) == 3: batch = batch[0] # Unwrap batch dimension
        final_detections = batch

    # CASE B: Split Output (2 Arrays: Boxes/Scores in one, Classes in the other)
    # This is likely what is happening to you.
    elif len(results) == 2:
        tensor_a = results[0]
        tensor_b = results[1]
        
        # Unwrap batch dimension if present (1, N, X) -> (N, X)
        if len(tensor_a.shape) == 3: tensor_a = tensor_a[0]
        if len(tensor_b.shape) == 3: tensor_b = tensor_b[0]

        # Identify which is which based on width (number of columns)
        # Boxes usually have 5 cols (ymin, xmin, ymax, xmax, score)
        # Classes usually have 1 col (class_id)
        boxes = None
        classes = None

        if tensor_a.shape[1] == 5 and tensor_b.shape[1] == 1:
            boxes = tensor_a
            classes = tensor_b
        elif tensor_a.shape[1] == 1 and tensor_b.shape[1] == 5:
            boxes = tensor_b
            classes = tensor_a
        
        # If we successfully identified the pair, merge them
        if boxes is not None and classes is not None:
            # Create a new list where each item is [ymin, xmin, ymax, xmax, score, class_id]
            # using numpy to stack them horizontally
            final_detections = np.hstack((boxes, classes))
        else:
            # Fallback if shapes are weird
            print("Warning: Could not merge split tensors automatically.")
            final_detections = tensor_a # Default to first one

    # --- DRAWING LOOP ---
    height, width, _ = frame.shape

    for det in final_detections:
        # We handle both lengths now
        if len(det) == 6:
            ymin, xmin, ymax, xmax, score, class_id = det
        elif len(det) == 5:
            # If we STILL only have 5, it means the merge failed or it wasn't split.
            # We must default to 0 (Person), but at least we tried!
            ymin, xmin, ymax, xmax, score = det
            class_id = 0
        else:
            continue

        if score < CONFIDENCE_THRESHOLD:
            continue

        # SIMPLE MAPPING
        x0 = int(xmin * width)
        y0 = int(ymin * height)
        x1 = int(xmax * width)
        y1 = int(ymax * height)

        # Draw
        label = COCO_LABELS.get(int(class_id), "Object")
        
        # Color coding (optional: change color based on class)
        color = (0, 255, 0) # Green
        if int(class_id) == 0: color = (0, 255, 255) # Yellow for Person
        
        cv2.rectangle(frame, (x0, y0), (x1, y1), color, 2)
        cv2.putText(frame, f"{label} {int(score*100)}%", (x0, y0-10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

def main():
    try:
        print(f"Loading Model: {MODEL_FILE}")
        with Hailo(MODEL_FILE) as hailo:
            picam2 = Picamera2()
            
            config = picam2.create_preview_configuration(
                main={"size": (2304, 1296), "format": "XRGB8888"}
            )
            picam2.configure(config)
            picam2.start()
            picam2.set_controls({"AfMode": 2, "AfRange": 0}) 

            print("Running... Press 'q' to quit.")

            while True:
                # 1. Capture Wide Image
                frame_wide = picam2.capture_array('main')
                frame_bgr = cv2.cvtColor(frame_wide, cv2.COLOR_BGRA2BGR)

                # 2. THE SQUISH
                frame_ai = cv2.resize(frame_bgr, (640, 640))

                # 3. Run AI
                results = hailo.run(frame_ai)

                # 4. Draw
                draw_detections(frame_bgr, results)
                
                cv2.imshow("Hailo Object Detection", frame_bgr)

                if cv2.waitKey(1) == ord('q'):
                    break

    except Exception as e:
        print(f"Error: {e}")
    finally:
        picam2.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()