import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai import (
    AI,
    ReasoningEffort,
    batch_process_chinese_modern_text,
    get_chinese_questions_without_training,
)

def main():
    data_dir = r"d:\space\html\print\data"
    
    print("=" * 60)
    print("语文现代文训练生成器")
    print("=" * 60)
    
    questions = get_chinese_questions_without_training(data_dir, skip_if_exists=True)
    print(f"\n找到 {len(questions)} 个待处理的语文题目")
    
    if not questions:
        print("没有需要处理的题目")
        return
    
    print(f"\n待处理题目ID: {questions[:5]}{'...' if len(questions) > 5 else ''}")
    
    ai = AI(
        model="doubao-seed-2-0-pro-260215",
        reasoning_effort=ReasoningEffort.medium,
    )
    
    print("\n开始批量处理...")
    print("-" * 60)
    
    result = batch_process_chinese_modern_text(
        data_dir=data_dir,
        ai=ai,
        max_workers=3,
        skip_if_exists=True,
    )
    
    print("\n" + "=" * 60)
    print("处理完成!")
    print(f"总计: {result['total']}")
    print(f"成功: {len(result['success'])}")
    print(f"失败: {len(result['failed'])}")
    print(f"跳过: {len(result['skipped'])}")
    
    if result['failed']:
        print("\n失败详情:")
        for item in result['failed'][:5]:
            print(f"  - {item['id']}: {item['reason']}")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
