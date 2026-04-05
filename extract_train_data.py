import os
import json
from pathlib import Path

data_dir = Path(r"d:\space\html\print\data")
output_file = Path(r"d:\space\html\print\extracted_train_data.json")

knowledge_error_train = []
pattern_reflex_train = []

for json_file in data_dir.glob("*.json"):
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if "math_processing_result" not in data:
            continue
        
        file_id = data.get("id", json_file.stem)
        
        for item in data["math_processing_result"]:
            unit_content = item.get("unit_content", "")
            classify_result = item.get("classify_result", "")
            
            for pre_item in item.get("pre_process", []):
                train_type = pre_item.get("train_type", "")
                
                record = {
                    "source_file": file_id,
                    "unit_content": unit_content,
                    "classify_result": classify_result,
                    "train_data": pre_item
                }
                
                if train_type == "知识易错训练":
                    knowledge_error_train.append(record)
                elif train_type == "套路反射训练":
                    pattern_reflex_train.append(record)
    
    except Exception as e:
        print(f"Error processing {json_file}: {e}")

result = {
    "知识易错训练": knowledge_error_train,
    "套路反射训练": pattern_reflex_train,
    "统计": {
        "知识易错训练数量": len(knowledge_error_train),
        "套路反射训练数量": len(pattern_reflex_train),
        "总数量": len(knowledge_error_train) + len(pattern_reflex_train)
    }
}

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"提取完成！")
print(f"知识易错训练: {len(knowledge_error_train)} 条")
print(f"套路反射训练: {len(pattern_reflex_train)} 条")
print(f"结果已保存到: {output_file}")
