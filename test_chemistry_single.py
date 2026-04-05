# import os
# import sys

# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# from ai.chemistry_processor import process_chemistry_question
# from ai.base import AI, ReasoningEffort

# data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
# question_id = "20260321144724"

# if __name__ == "__main__":
#     print(f"测试题目: {question_id}")
#     print("=" * 60)
    
#     ai = AI(
#         model="doubao-seed-2-0-pro-260215",
#         reasoning_effort=ReasoningEffort.medium,
#     )
    
#     try:
#         result = process_chemistry_question(
#             data_dir=data_dir,
#             question_id=question_id,
#             ai=ai,
#             skip_if_exists=False,
#         )
        
#         if result:
#             print("\n处理成功！")
#             print(f"Accumulation: {len(result.Accumulation)} 条")
#             print(f"Difficulties: {len(result.Difficulties)} 条")
#             print("\n" + "=" * 60)
#             print("结果预览:")
#             print(f"Accumulation 前2条:")
#             for i, item in enumerate(result.Accumulation[:2], 1):
#                 print(f"  {i}. {item.get('ExerciseType', 'N/A')} - {item.get('ExamTag', 'N/A')[:40]}...")
#             print(f"\nDifficulties 前2条:")
#             for i, item in enumerate(result.Difficulties[:2], 1):
#                 print(f"  {i}. {item.get('DifficultyName', 'N/A')[:40]}... (难度:{item.get('DifficultyLevel', 'N/A')}, 价值:{item.get('BreakthroughValue', 'N/A')})")
#         else:
#             print("处理失败或已存在")
            
#     except Exception as e:
#         print(f"错误: {e}")
#         import traceback
#         traceback.print_exc()


from ai import batch_process_chemistry, AI, ReasoningEffort

ai = AI(
    model="doubao-seed-2-0-pro-260215",
    reasoning_effort=ReasoningEffort.medium,
)

results = batch_process_chemistry(
    data_dir="data",
    ai=ai,
    max_workers=3,
)