import os
import base64
import json
from typing import Optional
from dataclasses import dataclass

from volcenginesdkarkruntime import Ark

from question_loader import ProcessedQuestion, load_question_by_id


SYSTEM_PROMPT = r"""# 系统级提示词：高中生物「神经刺激式积累反应」生成器 
 ## 任务目标 
 你是一名专业的高中生物学习助手，核心任务是将「题目+答案」转化为**可直接形成条件反射的神经刺激式积累反应**，完全覆盖「考点锚定反应：题干核心关键词→对应核心知识点、考纲考点的自动化匹配，解决 "这题考什么" 的底层问题，是所有后续反应的基础，核心是把「考点名称」和「题干高频触发词」做强绑定。 
 隐含信息解码反应：题干 / 选项的特定表述→背后隐藏的限定规则、默认前提、必备公理的自动化解码，打通 "显性题干" 到 "解题关键条件" 的链路，解决 "看懂题但找不到突破口" 的痛点，核心是把「特定表述」和「隐藏规则」做强绑定。 
 易错陷阱预警反应：选项 / 题干的高频易错表述、命题人常用挖坑点→风险预警信号的自动化触发，提前规避 "会做但做错" 的非知识性失分，是提分的核心，核心是把「挖坑标志性表述」和「易错点 / 避坑要点」做强绑定。 
 正误判断标尺反应：对应考点的固定判定规则、对错标准→选项正误的自动化对标判断，形成标准化判断逻辑，无需每次重新推导知识点，大幅提升解题速度与准确率，核心是把「考点」和「绝对正确 / 错误的判定标尺」做强绑定。 
 同类题迁移锚点反应：单题的考法、命题逻辑→一类题的通用命题规律、解题框架的自动化提炼，实现 "做一道题通一类题"，跳出题海，核心是把「单题考法」和「同类题通用解题框架」做强绑定。 
 」五大核心维度，并生成极简速记包。所有输出必须严格遵循指定的JSON格式，确保内容精准、逻辑清晰、可直接用于学生的神经刺激强化训练。 
 
 ## 输入说明 
 你将接收以下结构化输入： 
 - `question`: 完整的题目文本（含题干、选项、题号、年份、地区等所有信息） 
 - `answer`: 题目的正确答案（如："C"） 
 注意：数学公式请使用 LaTeX 格式：
- 行内公式使用 $...$ 包裹
- 独立公式使用 $$...$$ 包裹
例如：求解方程 $ax^2 + bx + c = 0$ 的解为 $$x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}$$
 ## 输出JSON结构定义 
 你必须严格按照以下JSON结构输出，不得增减字段，所有字段内容必须为中文： 
 ```json 
 { 
   "core_conclusion": "一句话总结本题的核心价值与最关键积累点（不超过50字）", 
   "reaction_dimensions": { 
     "考点锚定反应": { 
       "trigger_clues": "题干/选项中能直接锁定考点的核心关键词（用顿号分隔）", 
       "fixed_reaction": "1秒内自动激活的核心考点列表（分点，用①②③④标注）" 
     }, 
     "隐含信息解码反应": [ 
       { 
         "trigger_clue": "单个触发线索（题干/选项中的特定表述）", 
         "fixed_reaction": "自动解码出的隐藏规则、默认前提或必备公理（精准、具体）" 
       } 
     ], 
     "易错陷阱预警反应": [ 
       { 
         "priority": "优先级（仅填「最高」「高」「中」「低」）", 
         "trigger_clue": "触发预警的标志性表述", 
         "fixed_reaction": "自动激活的风险预警信号+避坑要点（必须明确、可操作）", 
         "example_application": "结合本题选项的具体应用说明（如：本题C选项就是典型陷阱，可瞬间判定为错误）" 
       } 
     ], 
     "正误判断标尺反应": [ 
       { 
         "ruler_name": "标尺名称（简洁概括）", 
         "fixed_standard": "固化的判定标准（绝对正确/错误的明确规则）", 
         "related_option": "本题中对应的选项（如：A、B、C、D）" 
       } 
     ], 
     "同类题迁移锚点反应": { 
       "trigger_clues": "触发同类题迁移的核心考法关键词", 
       "fixed_reaction": "自动提炼的本类题固定高频考法+提前预判坑点（分点，用①②③④标注）" 
     } 
   }, 
   "core_quick_memory_pack": [ 
     "极简线索-反应绑定语句（每条不超过30字，用「看到X→立刻反应Y」的格式）" 
   ] 
 } 
 ``` 
 
 ## 质量核心要求 
 1.  **神经刺激强绑定**：所有「触发线索」与「固化反应」必须是**唯一、直接、无需思考**的强关联，避免模糊表述。 
 2.  **精准覆盖考点**：严格基于高中生物考纲，确保所有考点、判定标准、隐藏规则的科学性与准确性。 
 3.  **优先级明确**：易错陷阱预警必须标注优先级，「最高」优先级为本题最核心、最常见的挖坑点，需重点突出。 
 4.  **极简速记**：核心速记包必须是可直接背诵的条件反射语句，数量控制在3-6条。 
 5.  **JSON格式严格**：确保输出的JSON格式完全正确，无语法错误、无多余字符，所有字段内容完整。"""


@dataclass
class NeuralReaction:
    core_conclusion: str
    reaction_dimensions: dict
    core_quick_memory_pack: list
    raw_response: str
    
    def to_dict(self) -> dict:
        return {
            "core_conclusion": self.core_conclusion,
            "reaction_dimensions": self.reaction_dimensions,
            "core_quick_memory_pack": self.core_quick_memory_pack
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


def generate_neural_reaction(
    question: ProcessedQuestion,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
) -> NeuralReaction:
    if api_key is None:
        api_key = os.getenv("ARK_API_KEY")
    
    if not api_key:
        raise ValueError("API KEY未配置，请设置ARK_API_KEY环境变量或传入api_key参数")
    
    client = Ark(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=api_key,
        timeout=1800,
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
    
    prompt_text = f"""请对以下题目生成神经刺激式积累反应：

【题目】
{question.question_text}

【答案】
{question.answer_text if question.answer_text else "暂无答案"}

请严格按照系统提示词中的JSON格式输出。"""
    
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
        ],
        thinking={
            "type": "enabled",
        },
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
    
    return NeuralReaction(
        core_conclusion=result.get("core_conclusion", ""),
        reaction_dimensions=result.get("reaction_dimensions", {}),
        core_quick_memory_pack=result.get("core_quick_memory_pack", []),
        raw_response=raw_response
    )


def generate_neural_reaction_by_id(
    data_dir: str,
    question_id: str,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
) -> Optional[NeuralReaction]:
    question = load_question_by_id(data_dir, question_id)
    if question is None:
        return None
    return generate_neural_reaction(question, api_key, model)


def save_neural_reaction_to_json(
    data_dir: str,
    question_id: str,
    reaction: NeuralReaction
) -> bool:
    file_path = os.path.join(data_dir, f"{question_id}.json")
    
    if not os.path.exists(file_path):
        return False
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    data["neural_reaction"] = reaction.to_dict()
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return True


def preprocess_and_save(
    data_dir: str,
    question_id: str,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
) -> Optional[NeuralReaction]:
    reaction = generate_neural_reaction_by_id(data_dir, question_id, api_key, model)
    
    if reaction is None:
        return None
    
    save_neural_reaction_to_json(data_dir, question_id, reaction)
    
    return reaction


if __name__ == "__main__":
    data_dir = r"d:\space\html\print\data"
    question_id = "20260314104304"
    
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
        print("核心速记包:")
        for i, item in enumerate(reaction.core_quick_memory_pack, 1):
            print(f"  {i}. {item}")
        print()
        print(f"结果已保存到: {os.path.join(data_dir, f'{question_id}.json')}")
    else:
        print("题目不存在")
