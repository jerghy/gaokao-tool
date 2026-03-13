import os
import base64
import json
from typing import Optional
from dataclasses import dataclass

from volcenginesdkarkruntime import Ark

from question_loader import ProcessedQuestion, load_question_by_id


SYSTEM_PROMPT = """# 系统级提示词：学生练题题目质量5级智能判定系统 
 ## 核心任务定位 
 你是一款专为中学生应试练题场景设计的题目质量判定工具，**核心判定逻辑必须严格围绕「模仿思维支撑价值」与「神经刺激式反应积累价值」两大核心**，对输入的「题目+答案」进行全维度质量评估，输出固定5个等级的判定结果。 
 
 ## 输入说明 
 你将接收固定格式的输入内容： 
 - `question`：完整题目文本，包含题干、选项、题号、年份、适配学段等全部原始信息 
 - `answer`：题目的官方正确答案 
 
 ## 核心判定维度与评分规则 
 所有评分与等级判定必须严格基于以下6个维度，优先级从高到低排序： 
 1.  **命题科学性与规范性（一票否决项）**：题干、选项、答案无科学性/知识点错误，表述严谨无歧义，符合对应学段官方考试（高考/中考/学业水平考）的命题规范，无超纲内容。 
 2.  **核心考点锚定质量**：考点紧扣对应学段考纲的高频核心考点，考查目标明确，无模糊、偏僻、无应试价值的冷门考点。 
 3.  **模仿思维支撑价值**：题目具备清晰、可复刻、可迁移的标准化解题思维范式，能支撑学生从单题解法提炼一类题的通用解题框架，实现从「复刻单题」到「掌握一类题思维」的进阶。 
 4.  **神经刺激积累价值**：题目包含高质量、高频考查的可积累触发线索，包括考点匹配关键词、隐藏信息解码提示、典型易错坑点等，能帮助学生形成「线索-自动化反应」的强绑定神经刺激，无无效偏难怪挖坑。 
 5.  **应试适配与区分度**：贴合真实考试的考查逻辑与难度分布，区分度合理，能适配对应学段的练题需求，无过于简单无训练价值、或过于偏难脱离考纲的问题。 
 6.  **瑕疵与缺陷扣分项**：题干表述冗余、非核心线索不足、考查维度单一等不影响核心价值的轻微瑕疵，或影响练题价值的核心缺陷。 
 
 ## 5个质量等级严格准入标准 
 必须严格按照以下标准判定等级，不得随意调整，符合对应等级全部要求方可准入，触及否决项直接降级： 
 | 等级 | 等级全称 | 核心准入标准 | 一票否决项 | 
 | :--- | :--- | :--- | :--- | 
 | S级 | 顶级优质（真题标杆级） | 1. 无任何科学性错误、表述歧义，完全符合官方考试命题规范；2. 100%紧扣考纲高频核心考点，无超纲；3. 模仿思维支撑价值拉满，可直接提炼一类题通用解题框架；4. 神经刺激积累价值拉满，包含多个高频可复用的触发线索与典型坑点；5. 区分度完全贴合真实考试逻辑 | 存在任何瑕疵、缺陷直接降级，不得评为S级 | 
 | A级 | 优质高效（模考核心级） | 1. 无任何科学性错误、答案错误、表述歧义，命题规范；2. 紧扣考纲重点考点，无超纲；3. 模仿思维支撑价值优秀，有明确可复刻的解题范式；4. 神经刺激积累价值优秀，有明确高频触发线索与典型坑点；5. 仅存在不影响核心价值的轻微瑕疵 | 存在核心缺陷直接降级，不得评为A级 | 
 | B级 | 合格可用（基础训练级） | 1. 无科学性错误、答案错误，题干无歧义；2. 考点符合考纲要求，无超纲；3. 能满足基础练题需求，可支撑基础知识点匹配、简单思维模仿与基础反应积累；4. 存在考查维度单一、无典型坑点、迁移性弱等不足，仅适配基础入门训练 | 存在任何错误、超纲直接降级，不得评为B级 | 
 | C级 | 劣质低效（无效刷题级） | 符合以下任意1项及以上：1. 考点模糊、超纲，或考查无应试价值的冷门偏僻知识点；2. 无明确可迁移的解题思维范式，无法支撑模仿思维训练；3. 无有效可积累的神经刺激线索，坑点为无效偏难怪内容；4. 题干表述有歧义，命题不规范；5. 无区分度，过于简单或过难脱离考纲 | 触及D级否决项直接降级 | 
 | D级 | 完全无效（错误误导级） | 符合以下任意1项及以上（一票否决）：1. 存在科学性/知识点错误、答案错误或存在争议；2. 题干/选项存在严重歧义，无法明确解题目标；3. 严重超纲，完全脱离对应学段考纲；4. 存在误导性内容，会给学生形成错误的思维范式或条件反射 | 只要符合任意1项，直接判定为D级 | 
 
 ## 输出要求与固定JSON结构 
 必须严格按照以下JSON结构输出，不得增减、修改任何字段，不得添加任何JSON外的文本、注释、markdown格式： 
 ```json 
 { 
   "question_basic_info": { 
     "question_type": "题目类型，如：单项选择题、填空题、解答题、实验题等", 
     "target_grade": "适配学段，如：高中、初中、小学高段", 
     "core_examination_points": "核心考查考点，用顿号分隔，精准对应考纲知识点" 
   }, 
   "quality_total_grade": "质量总等级，仅填：S级、A级、B级、C级、D级", 
   "grade_judgment_basis": "等级判断的核心依据，严格对应准入标准，不超过150字", 
   "dimension_scores": { 
     "命题科学性与规范性": "1-10分的整数评分", 
     "核心考点锚定质量": "1-10分的整数评分", 
     "模仿思维支撑价值": "1-10分的整数评分", 
     "神经刺激积累价值": "1-10分的整数评分", 
     "应试适配与区分度": "1-10分的整数评分" 
   }, 
   "core_value_highlights": "本题核心练题价值亮点，分点用①②③标注，必须紧扣模仿思维与积累反应两大核心", 
   "core_defects_or_flaws": "本题核心缺陷/瑕疵，无则填「无」，有则分点用①②③标注", 
   "suitable_practice_scene": "本题适配的练题场景，如：高考一轮核心考点巩固、新知识点入门基础训练、错题复盘神经刺激强化等", 
   "practice_usage_suggestion": "针对本题的练题使用建议，紧扣模仿思维与积累反应，不超过100字" 
 } 
 ```
 所有字段内容必须为中文，表述精准严谨，无歧义。等级判定必须严格遵循上述准入标准，不得随意调整。所有内容必须紧扣「模仿思维支撑价值」与「神经刺激积累价值」两大核心，不得脱离学生练题的核心场景。"""


@dataclass
class QualityEvaluation:
    question_basic_info: dict
    quality_total_grade: str
    grade_judgment_basis: str
    dimension_scores: dict
    core_value_highlights: str
    core_defects_or_flaws: str
    suitable_practice_scene: str
    practice_usage_suggestion: str
    raw_response: str
    
    def to_dict(self) -> dict:
        return {
            "question_basic_info": self.question_basic_info,
            "quality_total_grade": self.quality_total_grade,
            "grade_judgment_basis": self.grade_judgment_basis,
            "dimension_scores": self.dimension_scores,
            "core_value_highlights": self.core_value_highlights,
            "core_defects_or_flaws": self.core_defects_or_flaws,
            "suitable_practice_scene": self.suitable_practice_scene,
            "practice_usage_suggestion": self.practice_usage_suggestion
        }


def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_image_media_type(image_path: str) -> str:
    ext = os.path.splitext(image_path)[1].lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    return media_types.get(ext, "image/png")


def evaluate_question_quality(
    question: ProcessedQuestion,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
) -> QualityEvaluation:
    if api_key is None:
        api_key = "0f38123d-549a-48c5-a2ab-46dde690c019"
    
    if not api_key:
        raise ValueError("API KEY未配置，请设置ARK_API_KEY环境变量或传入api_key参数")
    
    client = Ark(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=api_key,
    )
    
    user_content = []
    
    for image_path in question.image_paths:
        if os.path.exists(image_path):
            base64_image = encode_image_to_base64(image_path)
            media_type = get_image_media_type(image_path)
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{media_type};base64,{base64_image}"}
            })
    
    prompt_text = f"""请对以下题目进行质量评价：

【题目】
{question.question_text}

【答案】
{question.answer_text if question.answer_text else "暂无答案"}

请严格按照系统提示词中的JSON格式输出评价结果。"""
    
    user_content.append({
        "type": "text",
        "text": prompt_text
    })
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_content
            }
        ]
    )
    
    raw_response = response.choices[0].message.content
    
    try:
        json_str = raw_response.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()
        
        result = json.loads(json_str)
    except json.JSONDecodeError:
        raise ValueError(f"AI返回内容不是有效的JSON格式:\n{raw_response}")
    
    return QualityEvaluation(
        question_basic_info=result.get("question_basic_info", {}),
        quality_total_grade=result.get("quality_total_grade", ""),
        grade_judgment_basis=result.get("grade_judgment_basis", ""),
        dimension_scores=result.get("dimension_scores", {}),
        core_value_highlights=result.get("core_value_highlights", ""),
        core_defects_or_flaws=result.get("core_defects_or_flaws", ""),
        suitable_practice_scene=result.get("suitable_practice_scene", ""),
        practice_usage_suggestion=result.get("practice_usage_suggestion", ""),
        raw_response=raw_response
    )


def evaluate_question_by_id(
    data_dir: str,
    question_id: str,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
) -> Optional[QualityEvaluation]:
    question = load_question_by_id(data_dir, question_id)
    if question is None:
        return None
    return evaluate_question_quality(question, api_key, model)


def save_evaluation_to_json(
    data_dir: str,
    question_id: str,
    evaluation: QualityEvaluation
) -> bool:
    file_path = os.path.join(data_dir, f"{question_id}.json")
    
    if not os.path.exists(file_path):
        return False
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    data["quality_evaluation"] = evaluation.to_dict()
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return True


def evaluate_and_save(
    data_dir: str,
    question_id: str,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
) -> Optional[QualityEvaluation]:
    evaluation = evaluate_question_by_id(data_dir, question_id, api_key, model)
    
    if evaluation is None:
        return None
    
    save_evaluation_to_json(data_dir, question_id, evaluation)
    
    return evaluation


if __name__ == "__main__":
    data_dir = r"d:\space\html\print\data"
    question_id = "20260314104304"
    
    print(f"正在评价题目: {question_id}")
    print("=" * 60)
    
    evaluation = evaluate_and_save(data_dir, question_id)
    
    if evaluation:
        print(f"质量等级: {evaluation.quality_total_grade}")
        print(f"判断依据: {evaluation.grade_judgment_basis}")
        print()
        print("维度评分:")
        for dim, score in evaluation.dimension_scores.items():
            print(f"  - {dim}: {score}分")
        print()
        print(f"核心价值亮点: {evaluation.core_value_highlights}")
        print()
        print(f"核心缺陷/瑕疵: {evaluation.core_defects_or_flaws}")
        print()
        print(f"适配练题场景: {evaluation.suitable_practice_scene}")
        print()
        print(f"练题使用建议: {evaluation.practice_usage_suggestion}")
        print()
        print(f"评价结果已保存到: {os.path.join(data_dir, f'{question_id}.json')}")
    else:
        print("题目不存在")
