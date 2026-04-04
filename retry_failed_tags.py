"""
重试失败的题目
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai.tag_processor import process_tags_for_question, collect_all_tags
from ai.base import AI, ReasoningEffort

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
PROMPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai", "tsc", "题目标签.txt")

FAILED_IDS = [
    "20260321144257",
    "20260321144340",
    "20260321144548",
    "20260321144813",
]

def main():
    ai = AI(
        model="doubao-seed-2-0-pro-260215",
        reasoning_effort=ReasoningEffort.medium,
        max_output_tokens=4096,
    )

    print("=" * 60)
    print("重试失败的题目")
    print(f"共 {len(FAILED_IDS)} 个题目")
    print("=" * 60)

    existing_tags = collect_all_tags(DATA_DIR)
    print(f"已有标签库: {len(existing_tags)} 个标签")

    success = 0
    failed = 0

    for i, qid in enumerate(FAILED_IDS, 1):
        print(f"\n[{i}/{len(FAILED_IDS)}] 处理: {qid}")
        print("-" * 40)
        result = process_tags_for_question(
            data_dir=DATA_DIR,
            question_id=qid,
            prompt_path=PROMPT_PATH,
            ai=ai,
            replace=False,
            skip_if_has_valid_tags=False,
        )
        if result:
            print(f"✓ 成功: 生成 {len(result.tags)} 个标签")
            for tag in result.tags:
                print(f"  - {tag}")
            success += 1
        else:
            print("✗ 失败")
            failed += 1

    print("\n" + "=" * 60)
    print(f"重试完成: 成功 {success} 个, 失败 {failed} 个")

if __name__ == "__main__":
    main()
