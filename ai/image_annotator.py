import os
import json
import threading
from dataclasses import dataclass
from typing import Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from ai.base import (
    AI,
    Model,
    ReasoningEffort,
    call_ai_json,
    build_input_content,
)


print_lock = threading.Lock()


__all__ = [
    "CharBox",
    "ImageAnnotation",
    "get_charbox_prompt",
    "get_splitlines_prompt",
    "annotate_single_image",
    "scan_unannotated_configs",
    "batch_annotate_images",
    "save_annotations_to_json",
]


@dataclass
class CharBox:
    x: float
    y: float
    size: float
    fontSize: str = "medium"

    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "size": self.size,
            "fontSize": self.fontSize,
        }


@dataclass
class ImageAnnotation:
    config_id: str
    charBox: Optional[CharBox]
    splitLines: Optional[list[float]]

    def to_dict(self) -> dict:
        return {
            "config_id": self.config_id,
            "charBox": self.charBox.to_dict() if self.charBox else None,
            "splitLines": self.splitLines,
        }


def get_charbox_prompt() -> str:
    return """你是一个图片标注助手。请仔细分析图片，识别图片中字体大小约12-14pt的最小单个汉字。

任务要求：
1. 找到图片中字体大小约12-14pt的最小单个汉字
2. 用正方形框选该汉字
3. 返回正方形框的位置和尺寸

返回JSON格式：
{
    "x": 0.5,
    "y": 0.3,
    "width": 0.04,
    "height": 0.04
}

说明：
- x: 正方形中心点的x坐标，相对于图片宽度，范围0-1
- y: 正方形中心点的y坐标，相对于图片高度，范围0-1
- width: 正方形的宽度，相对于图片宽度，范围0-1
- height: 正方形的高度，相对于图片高度，范围0-1

注意：
- 只返回JSON，不要返回其他内容
- 确保坐标和尺寸准确"""


def get_splitlines_prompt() -> str:
    return """你是一个图片标注助手。请仔细分析图片，识别图片中文字段落之间的水平分割线位置。

任务要求：
1. 观察图片中的文字布局
2. 找出不同文字段落之间的水平分割线
3. 返回所有分割线的y坐标位置

返回JSON格式：
{
    "splitLines": [0.35, 0.72]
}

说明：
- splitLines: 分割线的y坐标数组，每个值相对于图片高度，范围0-1
- 从上到下按顺序排列
- 如果没有明显的分割线，返回空数组

注意：
- 只返回JSON，不要返回其他内容
- 分割线应该是段落之间明显的空白区域的中线位置"""


def _parse_charbox_response(response: dict) -> Optional[CharBox]:
    if not response:
        return None

    x = response.get("x")
    y = response.get("y")
    width = response.get("width")
    height = response.get("height")

    if x is None or y is None:
        return None

    if width is not None and height is not None:
        size = (width + height) / 2
    elif width is not None:
        size = width
    elif height is not None:
        size = height
    else:
        return None

    return CharBox(x=x, y=y, size=size, fontSize="medium")


def _parse_splitlines_response(response: dict) -> Optional[list[float]]:
    if not response:
        return None

    split_lines = response.get("splitLines")
    if split_lines is None:
        return None

    if not isinstance(split_lines, list):
        return None

    return [float(line) for line in split_lines if isinstance(line, (int, float))]


def annotate_single_image(
    image_path: str,
    config_id: str,
    ai: Optional[AI] = None,
    annotate_charbox: bool = True,
    annotate_splitlines: bool = True,
) -> ImageAnnotation:
    annotation_ai = ai or AI(
        model=Model.doubao_seed_2_0_lite_260215,
        reasoning_effort=ReasoningEffort.minimal,
    )

    char_box = None
    split_lines = None

    user_content = build_input_content("请分析这张图片。", [image_path])

    if annotate_charbox:
        charbox_response = call_ai_json(
            ai=annotation_ai,
            system_prompt=get_charbox_prompt(),
            user_content=user_content,
        )
        if isinstance(charbox_response, dict):
            char_box = _parse_charbox_response(charbox_response)

    if annotate_splitlines:
        splitlines_response = call_ai_json(
            ai=annotation_ai,
            system_prompt=get_splitlines_prompt(),
            user_content=user_content,
        )
        if isinstance(splitlines_response, dict):
            split_lines = _parse_splitlines_response(splitlines_response)

    return ImageAnnotation(
        config_id=config_id,
        charBox=char_box,
        splitLines=split_lines,
    )


def scan_unannotated_configs(images_json_path: str) -> list[dict]:
    """
    扫描 images.json 中没有 charBox 字段的配置
    返回: [{"config_id": "xxx", "image_path": "xxx"}, ...]
    """
    if not os.path.exists(images_json_path):
        return []

    with open(images_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    images = data.get("images", {})
    configs = data.get("configs", {})
    base_dir = os.path.dirname(images_json_path)

    unannotated = []
    for config_id, config in configs.items():
        if config.get("charBox") is not None:
            continue

        image_id = config.get("image_id")
        if not image_id:
            continue

        image = images.get(image_id)
        if not image:
            continue

        image_path = image.get("path")
        if not image_path:
            continue

        full_image_path = os.path.join(base_dir, image_path)
        unannotated.append({
            "config_id": config_id,
            "image_path": full_image_path,
        })

    return unannotated


def save_annotations_to_json(
    images_json_path: str,
    annotations: list[ImageAnnotation],
) -> bool:
    """
    将标注结果保存回 images.json
    """
    if not os.path.exists(images_json_path):
        return False

    if not annotations:
        return False

    with open(images_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    configs = data.get("configs", {})
    updated = False

    for annotation in annotations:
        config_id = annotation.config_id
        if config_id not in configs:
            continue

        config = configs[config_id]
        if annotation.charBox:
            config["charBox"] = annotation.charBox.to_dict()
            updated = True
        if annotation.splitLines is not None:
            config["splitLines"] = annotation.splitLines
            updated = True

    if updated:
        with open(images_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return updated


def _process_single_annotation(
    config_id: str,
    image_path: str,
    ai: Optional[AI],
    annotate_charbox: bool,
    annotate_splitlines: bool,
    index: int,
    total: int,
) -> dict:
    result = {
        "config_id": config_id,
        "success": False,
        "annotation": None,
        "message": "",
    }

    try:
        annotation = annotate_single_image(
            image_path=image_path,
            config_id=config_id,
            ai=ai,
            annotate_charbox=annotate_charbox,
            annotate_splitlines=annotate_splitlines,
        )
        result["success"] = True
        result["annotation"] = annotation
        result["message"] = "标注成功"

    except Exception as e:
        result["message"] = str(e)[:100]

    with print_lock:
        status = "✓" if result["success"] else "✗"
        print(f"[{index}/{total}] {status} {config_id}: {result['message'][:50]}")

    return result


def batch_annotate_images(
    images_json_path: str,
    max_workers: int = 3,
    skip_existing: bool = True,
    annotate_charbox: bool = True,
    annotate_splitlines: bool = True,
    on_progress: Optional[Callable[[int, int, str], None]] = None,
) -> dict:
    """
    批量标注图片
    返回: {"total": 10, "success": 8, "failed": 1, "skipped": 1, "results": [...]}
    """
    results = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "results": [],
    }

    if not os.path.exists(images_json_path):
        print(f"文件不存在: {images_json_path}")
        return results

    targets = scan_unannotated_configs(images_json_path)
    if skip_existing:
        pass
    else:
        with open(images_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        configs = data.get("configs", {})
        images = data.get("images", {})
        base_dir = os.path.dirname(images_json_path)

        all_targets = []
        for config_id, config in configs.items():
            image_id = config.get("image_id")
            if not image_id:
                continue
            image = images.get(image_id)
            if not image:
                continue
            image_path = image.get("path")
            if not image_path:
                continue
            full_image_path = os.path.join(base_dir, image_path)
            all_targets.append({
                "config_id": config_id,
                "image_path": full_image_path,
            })
        targets = all_targets

    total = len(targets)
    results["total"] = total

    print(f"共 {total} 个配置需要标注")
    print(f"并发数: {max_workers}")
    print(f"标注 charBox: {annotate_charbox}")
    print(f"标注 splitLines: {annotate_splitlines}")
    print("=" * 60)

    if total == 0:
        return results

    ai = AI(
        model=Model.doubao_seed_2_0_lite_260215,
        reasoning_effort=ReasoningEffort.minimal,
    )

    successful_annotations = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                _process_single_annotation,
                target["config_id"],
                target["image_path"],
                ai,
                annotate_charbox,
                annotate_splitlines,
                i,
                total,
            ): target["config_id"]
            for i, target in enumerate(targets, 1)
        }

        for future in as_completed(futures):
            result = future.result()
            results["results"].append(result)

            if result["success"]:
                results["success"] += 1
                if result["annotation"]:
                    successful_annotations.append(result["annotation"])
            else:
                results["failed"] += 1

            if on_progress:
                on_progress(
                    results["success"] + results["failed"],
                    total,
                    result["config_id"],
                )

    if successful_annotations:
        save_annotations_to_json(images_json_path, successful_annotations)

    print("\n" + "=" * 60)
    print(f"处理完成: 成功 {results['success']} 个, 失败 {results['failed']} 个")

    if results["failed"] > 0:
        print("\n失败列表:")
        for r in results["results"]:
            if not r["success"]:
                print(f"  - {r['config_id']}: {r['message']}")

    return results
