import os
import yaml
import cv2
import shutil
from pathlib import Path
from tqdm import tqdm


def load_class_names(data_yaml_path):
    """
    Đọc class names từ file data.yaml
    
    Args:
        data_yaml_path (str): Đường dẫn đến file data.yaml
        
    Returns:
        list: Danh sách class names
    """
    with open(data_yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data['names']


def parse_yolo_label(label_path):
    """
    Đọc và phân tích file label YOLO
    
    Args:
        label_path (str): Đường dẫn đến file label .txt
        
    Returns:
        list: Danh sách các bounding box [(class_id, x_center, y_center, width, height), ...]
    """
    bboxes = []
    if os.path.exists(label_path):
        with open(label_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if line:
                    parts = line.split()
                    if len(parts) == 5:
                        class_id = int(parts[0])
                        x_center = float(parts[1])
                        y_center = float(parts[2])
                        width = float(parts[3])
                        height = float(parts[4])
                        bboxes.append((class_id, x_center, y_center, width, height))
    return bboxes


def yolo_to_pixel_coords(bbox, img_width, img_height):
    """
    Chuyển đổi tọa độ YOLO sang tọa độ pixel
    
    Args:
        bbox (tuple): (class_id, x_center, y_center, width, height) trong tỷ lệ YOLO
        img_width (int): Chiều rộng ảnh
        img_height (int): Chiều cao ảnh
        
    Returns:
        tuple: (class_id, x1, y1, x2, y2) tọa độ pixel
    """
    class_id, x_center, y_center, width, height = bbox
    
    # Chuyển đổi từ tỷ lệ sang pixel
    x_center_px = x_center * img_width
    y_center_px = y_center * img_height
    width_px = width * img_width
    height_px = height * img_height
    
    # Tính tọa độ góc trên trái và dưới phải
    x1 = int(x_center_px - width_px / 2)
    y1 = int(y_center_px - height_px / 2)
    x2 = int(x_center_px + width_px / 2)
    y2 = int(y_center_px + height_px / 2)
    
    # Đảm bảo tọa độ nằm trong giới hạn ảnh
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(img_width, x2)
    y2 = min(img_height, y2)
    
    return class_id, x1, y1, x2, y2


def add_padding(img, x1, y1, x2, y2, padding_ratio=0.1):
    """
    Thêm padding xung quanh bounding box để tạo context cho model
    
    Args:
        img: Ảnh gốc
        x1, y1, x2, y2: Tọa độ bounding box
        padding_ratio (float): Tỷ lệ padding so với kích thước bbox
        
    Returns:
        numpy.ndarray: Ảnh đã được cắt với padding
    """
    img_height, img_width = img.shape[:2]
    
    # Tính kích thước padding
    bbox_width = x2 - x1
    bbox_height = y2 - y1
    
    pad_x = int(bbox_width * padding_ratio)
    pad_y = int(bbox_height * padding_ratio)
    
    # Áp dụng padding
    x1_pad = max(0, x1 - pad_x)
    y1_pad = max(0, y1 - pad_y)
    x2_pad = min(img_width, x2 + pad_x)
    y2_pad = min(img_height, y2 + pad_y)
    
    return img[y1_pad:y2_pad, x1_pad:x2_pad]


def crop_images_from_dataset(dataset_path, output_path, class_names, padding_ratio=0.1):
    """
    Cắt ảnh từ dataset dựa trên labels
    
    Args:
        dataset_path (str): Đường dẫn đến thư mục dataset
        output_path (str): Đường dẫn đến thư mục output
        class_names (list): Danh sách tên các class
        padding_ratio (float): Tỷ lệ padding
    """
    # Tạo thư mục output nếu chưa tồn tại
    os.makedirs(output_path, exist_ok=True)
    
    # Tạo thư mục cho mỗi class
    for class_name in class_names:
        class_dir = os.path.join(output_path, class_name)
        os.makedirs(class_dir, exist_ok=True)
    
    # Danh sách các split (train, valid, test)
    splits = ['train', 'valid', 'test']
    
    total_cropped = 0
    
    for split in splits:
        print(f"\n🔄 Processing {split} split...")
        
        # Đường dẫn đến thư mục images và labels
        images_dir = os.path.join(dataset_path, split, 'images')
        labels_dir = os.path.join(dataset_path, split, 'labels')
        
        if not os.path.exists(images_dir):
            print(f"⚠️  Images directory not found: {images_dir}")
            continue
            
        if not os.path.exists(labels_dir):
            print(f"⚠️  Labels directory not found: {labels_dir}")
            continue
        
        # Lấy danh sách file ảnh
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        image_files = []
        
        for ext in image_extensions:
            image_files.extend([f for f in os.listdir(images_dir) if f.lower().endswith(ext)])
        
        split_cropped = 0
        
        # Duyệt qua từng file ảnh với thanh tiến trình
        for image_file in tqdm(image_files, desc=f"Cropping {split}", unit="image"):
            # Đường dẫn đến file ảnh
            image_path = os.path.join(images_dir, image_file)
            
            # Tạo tên file label tương ứng (thay đổi extension thành .txt)
            label_file = os.path.splitext(image_file)[0] + '.txt'
            label_path = os.path.join(labels_dir, label_file)
            
            # Đọc ảnh
            try:
                img = cv2.imread(image_path)
                if img is None:
                    print(f"⚠️  Cannot read image: {image_path}")
                    continue
                    
                img_height, img_width = img.shape[:2]
            except Exception as e:
                print(f"⚠️  Error reading {image_path}: {e}")
                continue
            
            # Đọc labels
            bboxes = parse_yolo_label(label_path)
            
            if not bboxes:
                continue  # Bỏ qua nếu không có label
            
            # Cắt ảnh cho mỗi bounding box
            for bbox_idx, bbox in enumerate(bboxes):
                try:
                    # Chuyển đổi tọa độ YOLO sang pixel
                    class_id, x1, y1, x2, y2 = yolo_to_pixel_coords(bbox, img_width, img_height)
                    
                    # Kiểm tra tính hợp lệ của bounding box
                    if x2 <= x1 or y2 <= y1:
                        continue
                    
                    # Cắt ảnh với padding
                    cropped_img = add_padding(img, x1, y1, x2, y2, padding_ratio)
                    
                    if cropped_img.size == 0:
                        continue
                    
                    # Tạo tên file cho ảnh đã cắt
                    base_name = os.path.splitext(image_file)[0]
                    cropped_filename = f"{split}_{base_name}_bbox{bbox_idx}.jpg"
                    
                    # Đường dẫn lưu ảnh
                    class_name = class_names[class_id]
                    output_file_path = os.path.join(output_path, class_name, cropped_filename)
                    
                    # Lưu ảnh đã cắt
                    cv2.imwrite(output_file_path, cropped_img)
                    split_cropped += 1
                    total_cropped += 1
                    
                except Exception as e:
                    print(f"⚠️  Error processing bbox in {image_file}: {e}")
                    continue
        
        print(f"✅ Done cropping {split_cropped} images for {split}")
    
    print(f"\n🎉 Total cropped images: {total_cropped}")
    return total_cropped


def main():
    """
    Hàm chính
    """
    # Đường dẫn đến dataset
    dataset_path = "../data/efficientnet_dataset"
    
    # Đường dẫn đến file data.yaml
    data_yaml_path = os.path.join(dataset_path, "data.yaml")
    
    # Đường dẫn output (thư mục cropped_dataset)
    output_path = "../cropped_dataset"
    
    # Tỷ lệ padding (10% của kích thước bounding box)
    padding_ratio = 0.1
    
    print("🚀 Starting image cropping process...")
    print(f"📁 Dataset path: {os.path.abspath(dataset_path)}")
    print(f"📁 Output path: {os.path.abspath(output_path)}")
    print(f"📏 Padding ratio: {padding_ratio}")
    
    # Kiểm tra xem dataset có tồn tại không
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset path not found: {dataset_path}")
        return
    
    # Kiểm tra file data.yaml
    if not os.path.exists(data_yaml_path):
        print(f"❌ data.yaml not found: {data_yaml_path}")
        return
    
    try:
        # Đọc class names từ data.yaml
        class_names = load_class_names(data_yaml_path)
        print(f"📋 Found {len(class_names)} classes: {class_names}")
        
        # Xóa thư mục output cũ nếu tồn tại (tùy chọn)
        if os.path.exists(output_path):
            response = input(f"🗑️  Output directory exists. Remove it? (y/N): ").lower().strip()
            if response == 'y':
                shutil.rmtree(output_path)
                print(f"🗑️  Removed existing output directory: {output_path}")
        
        # Thực hiện cắt ảnh
        total_cropped = crop_images_from_dataset(
            dataset_path, 
            output_path, 
            class_names, 
            padding_ratio
        )
        
        if total_cropped > 0:
            print(f"\n✅ Successfully completed! Cropped {total_cropped} images.")
            print(f"📁 Cropped images saved to: {os.path.abspath(output_path)}")
            
            # Hiển thị thống kê theo class
            print("\n📊 Summary by class:")
            for class_name in class_names:
                class_dir = os.path.join(output_path, class_name)
                if os.path.exists(class_dir):
                    count = len([f for f in os.listdir(class_dir) if f.lower().endswith('.jpg')])
                    print(f"  - {class_name}: {count} images")
        else:
            print("⚠️  No images were cropped. Please check your dataset.")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()