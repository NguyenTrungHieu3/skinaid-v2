"""
Test script for YOLO detection with bounding box refinement.
This script compares original YOLO bounding boxes vs refined bounding boxes.
"""
import sys
from pathlib import Path
import cv2
import numpy as np

# Add parent directory to path
ai_ml_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ai_ml_root))

from models.detection.wound_detector import WoundDetector
from configs.config import settings

def test_refinement(image_path: str):
    """
    Test bounding box refinement on a single image.
    """
    # Initialize detector
    detector = WoundDetector()
    
    # Read image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not read image {image_path}")
        return
    
    print(f"Testing on image: {image_path}")
    print(f"Image size: {image.shape[1]}x{image.shape[0]}")
    print("-" * 50)
    
    # Detect WITHOUT refinement
    detections_original = detector.detect(image, conf_threshold=0.25, refine_bbox=False)
    
    # Detect WITH refinement
    detections_refined = detector.detect(image, conf_threshold=0.25, refine_bbox=True)
    
    print("\n=== ORIGINAL YOLO DETECTIONS ===")
    for i, det in enumerate(detections_original):
        print(f"Detection {i+1}:")
        print(f"  Class: {det['class_name']}, Confidence: {det['confidence']}")
        print(f"  BBox: {det['bbox']}")
        x1, y1, x2, y2 = map(int, det['bbox'])
        print(f"  Size: {x2-x1}x{y2-y1} pixels")
    
    print("\n=== REFINED DETECTIONS ===")
    for i, det in enumerate(detections_refined):
        print(f"Detection {i+1}:")
        print(f"  Class: {det['class_name']}, Confidence: {det['confidence']}")
        print(f"  BBox: {det['bbox']}")
        x1, y1, x2, y2 = map(int, det['bbox'])
        print(f"  Size: {x2-x1}x{y2-y1} pixels")
    
    # Visualize comparison
    img_original = image.copy()
    img_refined = image.copy()
    
    # Draw original boxes (green)
    for det in detections_original:
        x1, y1, x2, y2 = map(int, det['bbox'])
        cv2.rectangle(img_original, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = f"{det['class_name']} {det['confidence']:.2f}"
        cv2.putText(img_original, label, (x1, y1 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # Draw refined boxes (red)
    for det in detections_refined:
        x1, y1, x2, y2 = map(int, det['bbox'])
        cv2.rectangle(img_refined, (x1, y1), (x2, y2), (0, 0, 255), 2)
        label = f"{det['class_name']} {det['confidence']:.2f}"
        cv2.putText(img_refined, label, (x1, y1 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    # Create comparison image (side by side)
    h = max(img_original.shape[0], img_refined.shape[0])
    comparison = np.zeros((h, img_original.shape[1] * 2 + 50, 3), dtype=np.uint8)
    comparison[:img_original.shape[0], :img_original.shape[1]] = img_original
    comparison[:img_refined.shape[0], img_original.shape[1] + 50:] = img_refined
    
    # Add labels
    cv2.putText(comparison, "Original (Green)", (50, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(comparison, "Refined (Red)", (img_original.shape[1] + 100, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    
    # Show results
    cv2.imshow("Comparison: Original vs Refined Bounding Boxes", comparison)
    print("\nPress any key to close the comparison window...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    # Print summary
    print("\n=== SUMMARY ===")
    if len(detections_original) == len(detections_refined):
        for i in range(len(detections_original)):
            orig_box = detections_original[i]['bbox']
            ref_box = detections_refined[i]['bbox']
            
            orig_area = (orig_box[2] - orig_box[0]) * (orig_box[3] - orig_box[1])
            ref_area = (ref_box[2] - ref_box[0]) * (ref_box[3] - ref_box[1])
            
            reduction = (1 - ref_area / orig_area) * 100 if orig_area > 0 else 0
            print(f"Detection {i+1}: Bounding box area reduced by {reduction:.1f}%")
    else:
        print("Warning: Different number of detections between original and refined")

if __name__ == "__main__":
    # Test image path - update this to your test image
    test_image = r"D:\NCKH\C1SE.24_SkinAid_Capstone1\ai_ml\data\raw_dataset\yolo_dataset\yolo_dataset_1_class_wound\test\images\istockphoto-1473174152-612x612_jpg.rf.36d17646cadbbab6b0a250aa7a71f5f1.jpg"
    
    # Check if file exists
    if not Path(test_image).exists():
        print(f"Test image not found: {test_image}")
        print("Please update the test_image path in this script.")
    else:
        test_refinement(test_image)
