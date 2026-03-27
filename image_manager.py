import os
import json
from PIL import Image
from typing import Set, List, Tuple, Optional


def get_all_referenced_images(data_dir: str) -> Set[str]:
    referenced_images = set()
    
    for filename in os.listdir(data_dir):
        if not filename.endswith('.json'):
            continue
        
        filepath = os.path.join(data_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            def extract_images_from_items(items: list) -> None:
                if not items:
                    return
                for item in items:
                    if isinstance(item, dict) and item.get('type') == 'image':
                        src = item.get('src', '')
                        if src.startswith('img/'):
                            referenced_images.add(src)
            
            extract_images_from_items(data.get('question', {}).get('items', []))
            extract_images_from_items(data.get('answer', {}).get('items', []))
            
            for sub_q in data.get('sub_questions', []):
                extract_images_from_items(sub_q.get('question_text', {}).get('items', []))
                
        except (json.JSONDecodeError, IOError) as e:
            print(f"警告: 无法读取文件 {filename}: {e}")
            continue
    
    return referenced_images


def cleanup_unused_images(
    base_dir: str,
    data_dir_name: str = 'data',
    img_dir_name: str = 'img',
    dry_run: bool = False,
    min_size_kb: Optional[int] = None
) -> Tuple[int, int, List[str]]:
    img_dir = os.path.join(base_dir, img_dir_name)
    data_dir = os.path.join(base_dir, data_dir_name)
    
    if not os.path.exists(img_dir):
        print(f"错误: 图片目录不存在: {img_dir}")
        return 0, 0, []
    
    if not os.path.exists(data_dir):
        print(f"错误: 数据目录不存在: {data_dir}")
        return 0, 0, []
    
    referenced_images = get_all_referenced_images(data_dir)
    print(f"找到 {len(referenced_images)} 个被引用的图片")
    
    deleted_count = 0
    skipped_count = 0
    deleted_files = []
    
    for filename in os.listdir(img_dir):
        if not (filename.lower().endswith('.png') or 
                filename.lower().endswith('.jpg') or 
                filename.lower().endswith('.jpeg') or 
                filename.lower().endswith('.gif')):
            continue
        
        img_path = os.path.join(img_dir, filename)
        img_reference = f"img/{filename}"
        
        if img_reference in referenced_images:
            continue
        
        file_size_kb = os.path.getsize(img_path) / 1024
        
        if min_size_kb is not None and file_size_kb < min_size_kb:
            skipped_count += 1
            continue
        
        if dry_run:
            print(f"[模拟删除] {filename} ({file_size_kb:.1f} KB)")
            deleted_files.append(filename)
            deleted_count += 1
        else:
            try:
                os.remove(img_path)
                print(f"[已删除] {filename} ({file_size_kb:.1f} KB)")
                deleted_files.append(filename)
                deleted_count += 1
            except OSError as e:
                print(f"删除失败 {filename}: {e}")
    
    print(f"\n清理完成: 删除 {deleted_count} 个文件, 跳过 {skipped_count} 个小文件")
    return deleted_count, skipped_count, deleted_files


def compress_images(
    base_dir: str,
    img_dir_name: str = 'img',
    min_size_kb: int = 100,
    quality: int = 85,
    dry_run: bool = False,
    convert_png_to_jpeg: bool = False
) -> Tuple[int, int, List[str]]:
    img_dir = os.path.join(base_dir, img_dir_name)
    
    if not os.path.exists(img_dir):
        print(f"错误: 图片目录不存在: {img_dir}")
        return 0, 0, []
    
    compressed_count = 0
    skipped_count = 0
    compressed_files = []
    
    for filename in os.listdir(img_dir):
        filepath = os.path.join(img_dir, filename)
        
        if not os.path.isfile(filepath):
            continue
        
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        if ext not in ['png', 'jpg', 'jpeg', 'gif']:
            continue
        
        original_size_kb = os.path.getsize(filepath) / 1024
        
        if original_size_kb < min_size_kb:
            skipped_count += 1
            continue
        
        try:
            with Image.open(filepath) as img:
                original_mode = img.mode
                original_format = img.format
                
                if dry_run:
                    print(f"[模拟压缩] {filename}")
                    print(f"  原始大小: {original_size_kb:.1f} KB")
                    print(f"  格式: {original_format}, 模式: {original_mode}")
                    compressed_files.append(filename)
                    compressed_count += 1
                    continue
                
                backup_path = filepath + '.bak'
                os.rename(filepath, backup_path)
                
                try:
                    if ext == 'png':
                        img_optimized = img.copy()
                        
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img_optimized = img.convert('RGBA')
                        
                        img_optimized.save(
                            filepath, 
                            'PNG', 
                            optimize=True,
                            compress_level=9
                        )
                    
                    elif ext in ['jpg', 'jpeg']:
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert('RGB')
                        
                        img.save(
                            filepath, 
                            'JPEG', 
                            quality=quality, 
                            optimize=True,
                            progressive=True
                        )
                    
                    elif ext == 'gif':
                        img.save(
                            filepath, 
                            'GIF', 
                            optimize=True
                        )
                    
                    new_size_kb = os.path.getsize(filepath) / 1024
                    saved_kb = original_size_kb - new_size_kb
                    saved_percent = (saved_kb / original_size_kb) * 100
                    
                    if new_size_kb < original_size_kb:
                        os.remove(backup_path)
                        print(f"[已压缩] {filename}")
                        print(f"  {original_size_kb:.1f} KB -> {new_size_kb:.1f} KB (节省 {saved_percent:.1f}%)")
                        compressed_files.append(filename)
                        compressed_count += 1
                    else:
                        os.remove(filepath)
                        os.rename(backup_path, filepath)
                        print(f"[跳过] {filename} (压缩后更大，保留原文件)")
                        skipped_count += 1
                        
                except Exception as e:
                    if os.path.exists(backup_path):
                        if os.path.exists(filepath):
                            os.remove(filepath)
                        os.rename(backup_path, filepath)
                    print(f"压缩失败 {filename}: {e}")
                    skipped_count += 1
                    
        except Exception as e:
            print(f"无法处理 {filename}: {e}")
            skipped_count += 1
    
    print(f"\n压缩完成: 压缩 {compressed_count} 个文件, 跳过 {skipped_count} 个文件")
    return compressed_count, skipped_count, compressed_files


def analyze_images(base_dir: str, img_dir_name: str = 'img') -> None:
    img_dir = os.path.join(base_dir, img_dir_name)
    
    if not os.path.exists(img_dir):
        print(f"错误: 图片目录不存在: {img_dir}")
        return
    
    total_size = 0
    total_count = 0
    size_ranges = {
        '< 50KB': 0,
        '50-100KB': 0,
        '100-500KB': 0,
        '500KB-1MB': 0,
        '> 1MB': 0
    }
    large_files = []
    
    for filename in os.listdir(img_dir):
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if ext not in ['png', 'jpg', 'jpeg', 'gif']:
            continue
        
        filepath = os.path.join(img_dir, filename)
        size_kb = os.path.getsize(filepath) / 1024
        total_size += size_kb
        total_count += 1
        
        if size_kb < 50:
            size_ranges['< 50KB'] += 1
        elif size_kb < 100:
            size_ranges['50-100KB'] += 1
        elif size_kb < 500:
            size_ranges['100-500KB'] += 1
        elif size_kb < 1024:
            size_ranges['500KB-1MB'] += 1
        else:
            size_ranges['> 1MB'] += 1
        
        if size_kb >= 500:
            large_files.append((filename, size_kb))
    
    print("\n" + "="*50)
    print("图片统计分析")
    print("="*50)
    print(f"总图片数: {total_count}")
    print(f"总大小: {total_size/1024:.2f} MB ({total_size:.1f} KB)")
    print(f"平均大小: {total_size/total_count:.1f} KB" if total_count > 0 else "")
    print("\n大小分布:")
    for range_name, count in size_ranges.items():
        print(f"  {range_name}: {count} 个")
    
    if large_files:
        large_files.sort(key=lambda x: x[1], reverse=True)
        print(f"\n大文件列表 (>=500KB, 共{len(large_files)}个):")
        for filename, size_kb in large_files[:10]:
            print(f"  {filename}: {size_kb:.1f} KB ({size_kb/1024:.2f} MB)")


if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    print("="*60)
    print("错题系统图片管理工具")
    print("="*60)
    
    while True:
        print("\n请选择操作:")
        print("1. 分析图片统计信息")
        print("2. 清理未引用的图片")
        print("3. 压缩大图片")
        print("4. 执行全部操作 (分析 -> 清理 -> 压缩)")
        print("0. 退出")
        
        choice = input("\n请输入选项 (0-4): ").strip()
        
        if choice == '0':
            print("再见!")
            break
        
        elif choice == '1':
            analyze_images(BASE_DIR)
        
        elif choice == '2':
            min_size = input("输入最小文件大小限制(KB, 直接回车删除所有未引用图片): ").strip()
            min_size_kb = int(min_size) if min_size else None
            
            dry_run = input("是否模拟运行? (y/n, 默认n): ").strip().lower() == 'y'
            
            cleanup_unused_images(
                BASE_DIR,
                dry_run=dry_run,
                min_size_kb=min_size_kb
            )
        
        elif choice == '3':
            min_size = input("输入最小压缩阈值(KB, 默认100): ").strip()
            min_size_kb = int(min_size) if min_size else 100
            
            quality = input("输入JPEG质量 (1-100, 默认85): ").strip()
            quality_val = int(quality) if quality else 85
            
            dry_run = input("是否模拟运行? (y/n, 默认n): ").strip().lower() == 'y'
            
            compress_images(
                BASE_DIR,
                min_size_kb=min_size_kb,
                quality=quality_val,
                dry_run=dry_run
            )
        
        elif choice == '4':
            print("\n--- 步骤1: 分析图片 ---")
            analyze_images(BASE_DIR)
            
            print("\n--- 步骤2: 清理未引用图片 ---")
            dry_run_clean = input("清理: 是否模拟运行? (y/n, 默认n): ").strip().lower() == 'y'
            cleanup_unused_images(BASE_DIR, dry_run=dry_run_clean)
            
            print("\n--- 步骤3: 压缩大图片 ---")
            min_size = input("压缩: 输入最小压缩阈值(KB, 默认100): ").strip()
            min_size_kb = int(min_size) if min_size else 100
            
            quality = input("压缩: 输入JPEG质量 (1-100, 默认85): ").strip()
            quality_val = int(quality) if quality else 85
            
            dry_run_compress = input("压缩: 是否模拟运行? (y/n, 默认n): ").strip().lower() == 'y'
            
            compress_images(
                BASE_DIR,
                min_size_kb=min_size_kb,
                quality=quality_val,
                dry_run=dry_run_compress
            )
            
            print("\n--- 最终统计 ---")
            analyze_images(BASE_DIR)
        
        else:
            print("无效选项，请重新输入")
