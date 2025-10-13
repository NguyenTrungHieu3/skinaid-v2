import os
import shutil
import random
from pathlib import Path


def get_image_files(directory):
    """
    Lấy danh sách tất cả file ảnh trong thư mục
    
    Args:
        directory (str): Đường dẫn thư mục
        
    Returns:
        list: Danh sách file ảnh
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    image_files = []
    
    if os.path.exists(directory):
        for file in os.listdir(directory):
            if Path(file).suffix.lower() in image_extensions:
                image_files.append(file)
    
    return image_files


def create_directory_structure(output_dir, class_names):
    """
    Tạo cấu trúc thư mục cho dataset đã chia
    
    Args:
        output_dir (str): Thư mục output
        class_names (list): Danh sách tên class
    """
    splits = ['train', 'val', 'test']
    
    # Tạo thư mục gốc nếu chưa tồn tại
    os.makedirs(output_dir, exist_ok=True)
    
    # Tạo thư mục cho mỗi split và class
    for split in splits:
        for class_name in class_names:
            split_class_dir = os.path.join(output_dir, split, class_name)
            os.makedirs(split_class_dir, exist_ok=True)
    
    print(f"📁 Created directory structure at: {os.path.abspath(output_dir)}")


def split_class_images(class_images, train_ratio=0.7, val_ratio=0.2, test_ratio=0.1):
    """
    Chia danh sách ảnh của một class thành train/val/test
    
    Args:
        class_images (list): Danh sách file ảnh
        train_ratio (float): Tỷ lệ train
        val_ratio (float): Tỷ lệ validation
        test_ratio (float): Tỷ lệ test
        
    Returns:
        tuple: (train_images, val_images, test_images)
    """
    # Shuffle danh sách ảnh
    random.shuffle(class_images)
    
    total_images = len(class_images)
    
    # Tính số lượng ảnh cho mỗi split
    train_count = int(total_images * train_ratio)
    val_count = int(total_images * val_ratio)
    # Test count = số còn lại để đảm bảo tất cả ảnh được phân chia
    test_count = total_images - train_count - val_count
    
    # Chia ảnh
    train_images = class_images[:train_count]
    val_images = class_images[train_count:train_count + val_count]
    test_images = class_images[train_count + val_count:]
    
    return train_images, val_images, test_images


def copy_images(source_dir, target_dir, image_list):
    """
    Copy danh sách ảnh từ thư mục nguồn đến thư mục đích
    
    Args:
        source_dir (str): Thư mục nguồn
        target_dir (str): Thư mục đích
        image_list (list): Danh sách file ảnh cần copy
        
    Returns:
        int: Số lượng ảnh đã copy thành công
    """
    success_count = 0
    
    for image_file in image_list:
        source_path = os.path.join(source_dir, image_file)
        target_path = os.path.join(target_dir, image_file)
        
        try:
            shutil.copy2(source_path, target_path)
            success_count += 1
        except Exception as e:
            print(f"⚠️  Error copying {image_file}: {e}")
    
    return success_count


def split_dataset(input_dir, output_dir, train_ratio=0.7, val_ratio=0.2, test_ratio=0.1, 
                  copy_files=True, random_seed=42):
    """
    Chia dataset thành train/val/test
    
    Args:
        input_dir (str): Thư mục chứa cropped_dataset
        output_dir (str): Thư mục output cho dataset đã chia
        train_ratio (float): Tỷ lệ train (mặc định 0.7)
        val_ratio (float): Tỷ lệ validation (mặc định 0.2)
        test_ratio (float): Tỷ lệ test (mặc định 0.1)
        copy_files (bool): True để copy file, False để move file
        random_seed (int): Seed cho random để có thể reproduce
        
    Returns:
        dict: Thống kê số lượng ảnh cho mỗi class và split
    """
    # Set random seed để có thể reproduce kết quả
    random.seed(random_seed)
    
    # Kiểm tra tỷ lệ split
    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-6:
        raise ValueError("Tổng các tỷ lệ split phải bằng 1.0")
    
    # Kiểm tra thư mục input
    if not os.path.exists(input_dir):
        raise ValueError(f"Input directory not found: {input_dir}")
    
    # Lấy danh sách các class (thư mục con)
    class_names = []
    for item in os.listdir(input_dir):
        item_path = os.path.join(input_dir, item)
        if os.path.isdir(item_path):
            class_names.append(item)
    
    if not class_names:
        raise ValueError(f"No class directories found in: {input_dir}")
    
    class_names.sort()  # Sắp xếp để có thứ tự nhất quán
    
    print(f"📋 Found {len(class_names)} classes: {class_names}")
    
    # Tạo cấu trúc thư mục
    create_directory_structure(output_dir, class_names)
    
    # Thống kê
    stats = {}
    total_stats = {'train': 0, 'val': 0, 'test': 0}
    
    print(f"\n🔄 Processing dataset split...")
    print(f"📊 Split ratios - Train: {train_ratio:.1%}, Val: {val_ratio:.1%}, Test: {test_ratio:.1%}")
    print(f"🎲 Random seed: {random_seed}")
    print(f"📁 {'Copying' if copy_files else 'Moving'} files...")
    
    # Xử lý từng class
    for class_name in class_names:
        print(f"\n🔄 Processing class: {class_name}")
        
        # Đường dẫn thư mục class
        class_input_dir = os.path.join(input_dir, class_name)
        
        # Lấy danh sách ảnh trong class
        class_images = get_image_files(class_input_dir)
        
        if not class_images:
            print(f"⚠️  No images found in {class_name}")
            stats[class_name] = {'train': 0, 'val': 0, 'test': 0, 'total': 0}
            continue
        
        print(f"  📷 Found {len(class_images)} images")
        
        # Chia ảnh thành train/val/test
        train_images, val_images, test_images = split_class_images(
            class_images, train_ratio, val_ratio, test_ratio
        )
        
        # Copy/Move ảnh vào các thư mục tương ứng
        splits_data = [
            ('train', train_images),
            ('val', val_images), 
            ('test', test_images)
        ]
        
        class_stats = {'total': len(class_images)}
        
        for split_name, split_images in splits_data:
            if split_images:
                target_dir = os.path.join(output_dir, split_name, class_name)
                
                if copy_files:
                    copied_count = copy_images(class_input_dir, target_dir, split_images)
                    class_stats[split_name] = copied_count
                    total_stats[split_name] += copied_count
                else:
                    # Move files (di chuyển file)
                    moved_count = 0
                    for image_file in split_images:
                        source_path = os.path.join(class_input_dir, image_file)
                        target_path = os.path.join(target_dir, image_file)
                        try:
                            shutil.move(source_path, target_path)
                            moved_count += 1
                        except Exception as e:
                            print(f"⚠️  Error moving {image_file}: {e}")
                    
                    class_stats[split_name] = moved_count
                    total_stats[split_name] += moved_count
            else:
                class_stats[split_name] = 0
        
        # In thống kê cho class này
        print(f"  ✅ {class_name}: Train={class_stats['train']}, "
              f"Val={class_stats['val']}, Test={class_stats['test']}")
        
        stats[class_name] = class_stats
    
    return stats, total_stats


def print_final_stats(stats, total_stats):
    """
    In thống kê cuối cùng
    
    Args:
        stats (dict): Thống kê theo class
        total_stats (dict): Thống kê tổng
    """
    print(f"\n" + "="*60)
    print(f"📊 FINAL STATISTICS")
    print(f"="*60)
    
    # Thống kê theo class
    print(f"{'Class Name':<25} {'Train':<8} {'Val':<8} {'Test':<8} {'Total':<8}")
    print(f"-" * 60)
    
    for class_name, class_stats in stats.items():
        print(f"{class_name:<25} "
              f"{class_stats.get('train', 0):<8} "
              f"{class_stats.get('val', 0):<8} "
              f"{class_stats.get('test', 0):<8} "
              f"{class_stats.get('total', 0):<8}")
    
    print(f"-" * 60)
    print(f"{'TOTAL':<25} "
          f"{total_stats['train']:<8} "
          f"{total_stats['val']:<8} "
          f"{total_stats['test']:<8} "
          f"{sum(total_stats.values()):<8}")
    
    # Tỷ lệ thực tế
    total_images = sum(total_stats.values())
    if total_images > 0:
        print(f"\n📈 Actual split ratios:")
        print(f"  Train: {total_stats['train']/total_images:.1%} ({total_stats['train']} images)")
        print(f"  Val:   {total_stats['val']/total_images:.1%} ({total_stats['val']} images)")
        print(f"  Test:  {total_stats['test']/total_images:.1%} ({total_stats['test']} images)")


def main():
    """
    Hàm chính
    """
    # Cấu hình
    input_dir = "../cropped_dataset"  # Thư mục chứa dataset gốc
    output_dir = "../efficientnet_dataset"  # Thư mục output
    
    # Tỷ lệ split
    train_ratio = 0.7
    val_ratio = 0.2
    test_ratio = 0.1
    
    # Cấu hình khác
    copy_files = True  # True để copy, False để move
    random_seed = 42   # Seed cho random
    
    print("🚀 Starting dataset splitting process...")
    print(f"📁 Input directory: {os.path.abspath(input_dir)}")
    print(f"📁 Output directory: {os.path.abspath(output_dir)}")
    
    # Kiểm tra thư mục input
    if not os.path.exists(input_dir):
        print(f"❌ Input directory not found: {input_dir}")
        return
    
    # Xác nhận ghi đè nếu thư mục output đã tồn tại
    if os.path.exists(output_dir):
        response = input(f"🗑️  Output directory exists. Remove and recreate? (y/N): ").lower().strip()
        if response == 'y':
            shutil.rmtree(output_dir)
            print(f"🗑️  Removed existing output directory")
        else:
            print(f"ℹ️  Will merge with existing directory")
    
    try:
        # Thực hiện chia dataset
        stats, total_stats = split_dataset(
            input_dir=input_dir,
            output_dir=output_dir,
            train_ratio=train_ratio,
            val_ratio=val_ratio,
            test_ratio=test_ratio,
            copy_files=copy_files,
            random_seed=random_seed
        )
        
        # In thống kê cuối cùng
        print_final_stats(stats, total_stats)
        
        print(f"\n✅ Dataset splitting completed successfully!")
        print(f"📁 Split dataset saved to: {os.path.abspath(output_dir)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()