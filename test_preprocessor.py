import os
from question_preprocessor import preprocess_and_save, generate_neural_reaction_by_id

data_dir = r"d:\space\html\print\data"
question_id = "20260314104304"

os.environ["ARK_API_KEY"] = "0f38123d-549a-48c5-a2ab-46dde690c019"

print(f"正在预处理题目: {question_id}")
print("=" * 60)

reaction = preprocess_and_save(data_dir, question_id)

if reaction:
    print(f"核心结论: {reaction.core_conclusion}")
    print()
    
    print("考点锚定反应:")
    anchor = reaction.reaction_dimensions.get("考点锚定反应", {})
    print(f"  触发线索: {anchor.get('trigger_clues', '')}")
    print(f"  固化反应: {anchor.get('fixed_reaction', '')}")
    print()
    
    print("隐含信息解码反应:")
    for i, item in enumerate(reaction.reaction_dimensions.get("隐含信息解码反应", []), 1):
        print(f"  {i}. {item.get('trigger_clue', '')} → {item.get('fixed_reaction', '')}")
    print()
    
    print("易错陷阱预警反应:")
    for item in reaction.reaction_dimensions.get("易错陷阱预警反应", []):
        print(f"  [{item.get('priority', '')}] {item.get('trigger_clue', '')}")
        print(f"    避坑要点: {item.get('fixed_reaction', '')}")
    print()
    
    print("正误判断标尺反应:")
    for item in reaction.reaction_dimensions.get("正误判断标尺反应", []):
        print(f"  {item.get('ruler_name', '')} ({item.get('related_option', '')}): {item.get('fixed_standard', '')}")
    print()
    
    print("同类题迁移锚点反应:")
    migration = reaction.reaction_dimensions.get("同类题迁移锚点反应", {})
    print(f"  触发线索: {migration.get('trigger_clues', '')}")
    print(f"  固化反应: {migration.get('fixed_reaction', '')}")
    print()
    
    print("核心速记包:")
    for i, item in enumerate(reaction.core_quick_memory_pack, 1):
        print(f"  {i}. {item}")
    print()
    
    print(f"结果已保存到: {os.path.join(data_dir, f'{question_id}.json')}")
else:
    print("题目不存在")
