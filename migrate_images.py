import os
import json
import shutil
from datetime import datetime
from image_manager import ImageManager


def backup_data(data_dir, backup_dir):
    """备份数据目录"""
    if os.path.exists(backup_dir):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_dir = f"{backup_dir}_{timestamp}"
    
    shutil.copytree(data_dir, backup_dir)
    print(f"数据已备份到: {backup_dir}")


def extract_filename_from_src(src):
    """从 src 路径提取文件名"""
    if not src:
        return None
    filename = os.path.basename(src)
    return filename if filename else None


def process_image_item(item, question_id, image_manager, stats):
    """处理单个图片项，返回新的图片项格式"""
    if item.get("type") != "image":
        return item
    
    src = item.get("src")
    if not src:
        return item
    
    filename = extract_filename_from_src(src)
    if not filename:
        return item
    
    existing_image = image_manager.get_image_by_filename(filename)
    
    if existing_image:
        image_id = existing_image["id"]
        stats["existing_images"] += 1
    else:
        image_id = image_manager.add_image(
            filename=filename,
            path=src,
            width=item.get("width") if isinstance(item.get("width"), int) else None,
            height=item.get("height") if isinstance(item.get("height"), int) else None
        )
        stats["new_images"] += 1
    
    display = item.get("display", "center")
    width = item.get("width", 300)
    height = item.get("height", "auto")
    charBox = item.get("charBox")
    splitLines = item.get("splitLines")
    
    config_id = image_manager.create_config(
        image_id=image_id,
        display=display,
        width=width if isinstance(width, int) else 300,
        height=height if isinstance(height, str) else "auto",
        charBox=charBox,
        splitLines=splitLines
    )
    stats["new_configs"] += 1
    
    image_manager.add_usage(config_id, question_id)
    
    return {
        "type": "image",
        "config_id": config_id
    }


def process_items(items, question_id, image_manager, stats):
    """处理 items 列表中的所有图片项"""
    if not items:
        return items
    
    new_items = []
    for item in items:
        new_item = process_image_item(item, question_id, image_manager, stats)
        new_items.append(new_item)
    
    return new_items


def migrate_question(filepath, image_manager, stats):
    """迁移单个题目文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"  警告: 无法读取文件 {filepath}: {e}")
        stats["errors"] += 1
        return False
    
    question_id = data.get("id", os.path.basename(filepath))
    modified = False
    
    if "question" in data and "items" in data.get("question", {}):
        original_items = data["question"]["items"]
        new_items = process_items(original_items, question_id, image_manager, stats)
        if new_items != original_items:
            data["question"]["items"] = new_items
            modified = True
    
    if "answer" in data and "items" in data.get("answer", {}):
        original_items = data["answer"]["items"]
        new_items = process_items(original_items, question_id, image_manager, stats)
        if new_items != original_items:
            data["answer"]["items"] = new_items
            modified = True
    
    if "sub_questions" in data and isinstance(data["sub_questions"], list):
        for sub_q in data["sub_questions"]:
            if "question_text" in sub_q and "items" in sub_q.get("question_text", {}):
                original_items = sub_q["question_text"]["items"]
                new_items = process_items(original_items, question_id, image_manager, stats)
                if new_items != original_items:
                    sub_q["question_text"]["items"] = new_items
                    modified = True
    
    if modified:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print(f"  警告: 无法写入文件 {filepath}: {e}")
            stats["errors"] += 1
            return False
    
    return True


def main():
    """主函数"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    backup_dir = os.path.join(base_dir, 'data_backup')
    images_path = os.path.join(base_dir, 'images.json')
    
    stats = {
        "new_images": 0,
        "existing_images": 0,
        "new_configs": 0,
        "errors": 0
    }
    
    print("=" * 50)
    print("图片数据迁移脚本")
    print("=" * 50)
    
    print("\n[1/3] 正在备份数据...")
    backup_data(data_dir, backup_dir)
    
    print("\n[2/3] 初始化图片管理器...")
    image_manager = ImageManager(images_path)
    
    print("\n[3/3] 正在迁移题目...")
    json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    total_files = len(json_files)
    migrated_count = 0
    
    for i, filename in enumerate(json_files, 1):
        filepath = os.path.join(data_dir, filename)
        if migrate_question(filepath, image_manager, stats):
            migrated_count += 1
        
        if i % 10 == 0 or i == total_files:
            print(f"  进度: {i}/{total_files} ({i*100//total_files}%)")
    
    print("\n" + "=" * 50)
    print("迁移完成！")
    print("=" * 50)
    print(f"处理题目数量: {migrated_count}")
    print(f"新增图片记录: {stats['new_images']}")
    print(f"已存在图片: {stats['existing_images']}")
    print(f"新增配置记录: {stats['new_configs']}")
    if stats['errors'] > 0:
        print(f"错误数量: {stats['errors']}")
    print(f"\n图片数据已保存到: {images_path}")
    print(f"原始数据备份在: {backup_dir}")


if __name__ == '__main__':
    main()
