import os
import shutil
from pathlib import Path

def copy_files_from_target_folders(source_dir, target_dir, folder_name="1_10年真题"):
    """
    遍历源文件夹及其所有子文件夹，找到所有名为folder_name的文件夹，
    将其中的所有文件复制到目标文件夹中。
    
    Args:
        source_dir: 要遍历的源文件夹路径
        target_dir: 目标文件夹路径
        folder_name: 要查找的文件夹名称，默认为"1_10年真题"
    """
    source_path = Path(source_dir)
    target_path = Path(target_dir)
    
    if not source_path.exists():
        print(f"错误：源文件夹不存在: {source_dir}")
        return
    
    if not target_path.exists():
        target_path.mkdir(parents=True, exist_ok=True)
        print(f"创建目标文件夹: {target_dir}")
    
    copied_count = 0
    skipped_count = 0
    
    for root, dirs, files in os.walk(source_path):
        current_path = Path(root)
        
        if current_path.name == folder_name:
            print(f"找到目标文件夹: {root}")
            
            for file in files:
                source_file = current_path / file
                target_file = target_path / file
                
                if target_file.exists():
                    print(f"  跳过（文件已存在）: {file}")
                    skipped_count += 1
                else:
                    shutil.copy2(source_file, target_file)
                    print(f"  复制: {file}")
                    copied_count += 1
    
    print(f"\n完成！")
    print(f"复制文件数: {copied_count}")
    print(f"跳过文件数: {skipped_count}")

if __name__ == "__main__":
    source_directory = input("请输入源文件夹路径: ").strip()
    target_directory = input("请输入目标文件夹路径: ").strip()
    folder_name = input("请输入要查找的文件夹名称（默认为'1_10年真题'）: ").strip() or "1_10年真题"
    
    copy_files_from_target_folders(source_directory, target_directory, folder_name)
