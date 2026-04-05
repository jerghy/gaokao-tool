import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai.chemistry_difficulty_processor import batch_process_difficulties
from ai.base import AI, ReasoningEffort

data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

if __name__ == "__main__":
    ai = AI(
        model="doubao-seed-2-0-pro-260215",
        reasoning_effort=ReasoningEffort.medium,
    )

    results = batch_process_difficulties(
        data_dir=data_dir,
        ai=ai,
        max_workers=26,
        skip_if_exists=False,
    )

    print("\n" + "=" * 60)
    print("化学难点教学生成完成！")
    print(f"总计: {results['total']} 个难点")
    print(f"成功: {len(results['success'])} 个")
    print(f"失败: {len(results['failed'])} 个")
    print(f"跳过: {len(results['skipped'])} 个")
