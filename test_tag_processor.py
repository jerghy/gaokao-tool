"""
题目标签生成测试脚本

使用方法:
    python test_tag_processor.py [question_id]

示例:
    python test_tag_processor.py 20260314095948
    python test_tag_processor.py  # 处理所有题目
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai.tag_processor import (
    process_tags_for_question,
    batch_process_tags,
    collect_all_tags,
)
from ai.base import AI, ReasoningEffort

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
PROMPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai", "tsc", "题目标签.txt")


def main():
    question_id = sys.argv[1] if len(sys.argv) > 1 else None

    ai = AI(
        model="doubao-seed-2-0-pro-260215",
        reasoning_effort=ReasoningEffort.medium,
        max_output_tokens=4096,
    )

    print("=" * 60)
    print("题目标签生成器")
    print(f"模型: {ai.model}")
    print(f"推理深度: {ai.reasoning_effort}")
    print("=" * 60)

    existing_tags = collect_all_tags(DATA_DIR)
    print(f"\n已有标签库: {len(existing_tags)} 个标签")
    if existing_tags:
        print("示例标签:", existing_tags[:5], "..." if len(existing_tags) > 5 else "")

    if question_id:
        print(f"\n处理单个题目: {question_id}")
        print("-" * 60)
        result = process_tags_for_question(
            data_dir=DATA_DIR,
            question_id=question_id,
            prompt_path=PROMPT_PATH,
            ai=ai,
            replace=False,
            skip_if_has_valid_tags=False,
        )
        if result:
            print(f"\n生成的标签 ({len(result.tags)} 个):")
            for tag in result.tags:
                print(f"  - {tag}")
        else:
            print("生成失败")
    else:
        print("\n批量处理所有题目")
        print("-" * 60)
        results = batch_process_tags(
            data_dir=DATA_DIR,
            prompt_path=PROMPT_PATH,
            ai=ai,
            replace=True,
            skip_if_has_valid_tags=True,
            max_workers=3,
        )
        print(f"\n处理结果: 成功 {len(results['success'])} 个, 失败 {len(results['failed'])} 个, 跳过 {len(results['skipped'])} 个")


if __name__ == "__main__":
    main()
