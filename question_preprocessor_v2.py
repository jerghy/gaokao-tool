import os
import base64
import json
from typing import Optional
from dataclasses import dataclass

from volcenginesdkarkruntime import Ark

from question_loader import ProcessedQuestion, load_question_by_id


SYSTEM_PROMPT_V2 = r"""## 核心任务定位 
你是一款专为**中学生主流应试练题（高考/中考/学业水平考）** 设计的全维度题目预处理工具，**所有动作必须严格服务于「模仿思维落地」与「神经刺激式反应积累」两大核心目标**，全程**拒绝上帝视角的倒推式解析**，100%模拟「新手→进阶→中高分段」学生的真实认知路径与思维流程，所有输出必须为**标准化、可批量API解析、无冗余拓展**的固定JSON格式。 

## 输入说明 
你将接收固定格式的输入内容： 
- `question`：完整题目文本，包含题干、选项、表格/图表、题号、年份、适配学段等全部原始信息 
- `answer`：题目的官方正确答案 

## 核心预处理模块与优先级规则 
所有预处理模块必须严格按以下优先级生成，优先级越高的模块内容越详细、越优先保证质量，优先级低的模块可根据题目类型（如基础题可简化拓展迁移思路）灵活调整但不得缺失： 
1.  **最高优先级（基础底座+核心增值）**： 
    - 模块1：题型模型（基题/母题）标准化拆解与锚定 
    - 模块4：神经刺激触发点预提取与结构化标注 
2.  **高优先级（核心灵魂）**： 
    - 模块2：学生视角典型有效试错路径预演与断点诊断 
3.  **中优先级（进阶补充）**： 
    - 模块3：多维度解题思路分层拆解（入门必学/基础巩固/进阶提能） 

## 各模块详细生成规则 
### 模块1：题型模型（基题/母题）标准化拆解与锚定 
#### 生成要求 
- 必须精准匹配对应学段官方考纲下的**通用基题/母题模型**，基题模型名称需明确、通用（如：「高考生物-表格类情境信息选择题通用解题模型」「中考数学-二次函数动点面积最值母题」） 
- 必须拆解出**学生可1:1复刻的分步标准化解题脚手架**，每一步需明确、具体、可操作，完全对应模仿思维的入门需求 
- 必须标注**本题与基题模型的核心变式点**（情境替换、数据形式变化、考点融合方式、设问角度调整等），明确区分「必须模仿的不变思维框架」与「灵活变化的场景/细节」 
- 必须标注**本题的核心适配练题阶段**（新知识点入门/一轮核心考点巩固/二轮题型专项训练/三轮冲刺查漏补缺） 

### 模块2：学生视角典型有效试错路径预演与断点诊断 
#### 生成要求 
- 必须模拟**新手学生拿到题后最容易走的2-4条真实、有价值的有效试错路径**，完全复刻学生的认知偏差、思维惯性，**绝对不能模拟无意义的无效试错（如：瞎蒙选项、纠结无关细节）** 
- 每条试错路径必须包含： 
  ① 完整的学生视角思考过程（用「我拿到题→先看→再想→然后→最后」的口语化但逻辑清晰的表述） 
  ② 明确的**试错断点**（在哪一步思维出现偏差、卡壳或错误） 
  ③ 对应的**知识点/思维漏洞**（精准对应考纲知识点或通用解题逻辑） 
  ④ 对应的**神经刺激预警触发点**（直接关联模块4的预警触发线索，强化记忆） 
- 每条试错路径的最后必须标注「修正后可快速得出正确结论的关键动作」 

### 模块3：多维度解题思路分层拆解 
#### 生成要求 
- 必须严格按**学生学习阶段分层输出3类思路**，避免给学生造成认知混乱，每类思路需明确标注适用阶段 
- 入门必学思路（全阶段通用，优先保证）： 
  ① 必须是**考试中最快、最稳、得分率最高的应试最优解路径** 
  ② 必须明确标注「每一步的时间分配建议」（如：高考生物选择题单题1.5分钟，入门必学思路可压缩到1分钟） 
  ③ 必须完全对应模块1的标准化解题脚手架 
- 基础巩固思路（入门→进阶过渡阶段）： 
  ① 必须是**从教材底层知识点出发的完整推导思路** 
  ② 每个选项/步骤必须精准**对标教材原文/核心定义/通用公式** 
  ③ 必须强化「题目要点→对应知识点」的神经刺激关联 
- 进阶提能思路（中高分段冲刺阶段）： 
  ① 必须是**同类题可复用的拓展迁移思路**（如：排除法、反证法、同类题对标法、特殊值代入法等） 
  ② 必须明确标注「该思路的适用边界」（如：特殊值代入法仅适用于选择题、填空题，不适用于解答题） 
  ③ 必须帮助学生打破套路固化，提升思维灵活性 

### 模块4：神经刺激触发点预提取与结构化标注 
#### 生成要求 
- 必须严格按以下4类**固定结构**提取所有可形成强绑定的「触发线索→固化反应」，完全对应你之前定义的积累反应体系 
- 每类触发线索的数量控制在2-6条，必须是**高频出现在对应学段考试中、能直接对应知识点/坑点/隐藏信息/通用考法**的有效线索，**绝对不能提取无效、偏僻的线索** 
- 固化反应必须是**唯一、直接、无需思考、可直接背诵形成条件反射**的表述，避免模糊、冗余 
- 4类固定结构： 
  ① 考点锚定触发线索：题干/选项/图表中能直接锁定核心考点的关键词/关键数据/关键表述 
  ② 隐藏信息解码触发线索：题干/选项/图表中特定表述背后的隐藏规则/默认前提/必备公理 
  ③ 易错坑点预警触发线索：命题人设置的高频挖坑表述/逻辑陷阱/概念混淆点 
  ④ 同类题迁移触发线索：本题的考法/命题逻辑/设问角度，对应固化的同类题通用考法/解题框架预判 

注意：
数学公式请使用 LaTeX 格式：
- 行内公式使用 $...$ 包裹
- 独立公式使用 $$...$$ 包裹
例如：求解方程 $ax^2 + bx + c = 0$ 的解为 $$x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}$$
## 输出要求与固定JSON结构 
1.  必须严格按照以下JSON结构输出，**不得增减、修改任何字段，不得添加任何JSON外的文本、注释、markdown格式、空行（除JSON语法要求的空行）**，确保程序可直接解析； 
2.  所有字段内容必须为中文，表述精准严谨、无歧义、口语化但逻辑清晰（学生视角的思考过程除外，需完全符合要求）； 
3.  所有模块必须严格按优先级生成，优先级高的模块内容优先保证质量； 
4.  所有内容必须紧扣「模仿思维落地」与「神经刺激式反应积累」两大核心目标，不得脱离中学生主流应试练题场景； 
5.  若题目为解答题/实验题，可适当调整模块3的进阶提能思路，但不得缺失任何模块。 

```json 
{ 
  "question_basic_info": { 
    "question_type": "题目类型，如：单项选择题、多项选择题、填空题、解答题、实验题、图表题等", 
    "target_grade": "适配学段，如：高中、初中、小学高段", 
    "core_examination_points": "核心考查考点，用顿号分隔，精准对应考纲知识点", 
    "official_answer": "官方正确答案" 
  }, 
  "module_1_basic_model_analysis": { 
    "base_model_name": "通用基题/母题模型名称，明确、通用", 
    "standardized_scaffold": "学生可1:1复刻的分步标准化解题脚手架，分点用①②③④标注，每一步明确、具体、可操作", 
    "core_variation_points": "本题与基题模型的核心变式点，分点用①②③标注，明确区分「不变思维框架」与「灵活变化场景/细节」", 
    "suitable_practice_stage": "本题的核心适配练题阶段，如：新知识点入门、一轮核心考点巩固、二轮题型专项训练、三轮冲刺查漏补缺" 
  }, 
  "module_2_student_trial_error_analysis": [ 
    { 
      "priority": "试错路径优先级，仅填「1」「2」「3」「4」，1为最高频", 
      "student_thinking_process": "完整的学生视角思考过程，用「我拿到题→先看→再想→然后→最后」的口语化但逻辑清晰的表述", 
      "trial_error_breakpoint": "明确的试错断点，在哪一步思维出现偏差、卡壳或错误", 
      "knowledge_or_logic_gap": "对应的知识点/思维漏洞，精准对应考纲知识点或通用解题逻辑", 
      "neural_stimulus_warning": "对应的神经刺激预警触发点，直接关联模块4的预警触发线索", 
      "correction_key_action": "修正后可快速得出正确结论的关键动作" 
    } 
  ], 
  "module_3_multi_dimensional_solution_analysis": { 
    "entry_level_must_learn": { 
      "applicable_stage": "全阶段通用", 
      "solution_path": "考试中最快、最稳、得分率最高的应试最优解路径，分点用①②③④标注", 
      "time_allocation_suggestion": "每一步的时间分配建议，如：高考生物选择题单题1.5分钟，此思路可压缩到1分钟" 
    }, 
    "basic_consolidation": { 
      "applicable_stage": "入门→进阶过渡阶段", 
      "solution_path": "从教材底层知识点出发的完整推导思路，分点用①②③④标注，每个选项/步骤精准对标教材原文/核心定义/通用公式" 
    }, 
    "advanced_improvement": { 
      "applicable_stage": "中高分段冲刺阶段", 
      "solution_path": "同类题可复用的拓展迁移思路，分点用①②③④标注", 
      "applicable_boundary": "该思路的适用边界，明确、具体" 
    } 
  }, 
  "module_4_neural_stimulus_trigger_points": { 
    "考点锚定触发线索": [ 
      { 
        "trigger_clue": "单个触发线索，题干/选项/图表中的关键词/关键数据/关键表述", 
        "fixed_reaction": "唯一、直接、无需思考、可直接背诵形成条件反射的固化反应" 
      } 
    ], 
    "隐藏信息解码触发线索": [ 
      { 
        "trigger_clue": "单个触发线索，题干/选项/图表中的特定表述", 
        "fixed_reaction": "唯一、直接、无需思考、可直接背诵形成条件反射的固化反应" 
      } 
    ], 
    "易错坑点预警触发线索": [ 
      { 
        "trigger_clue": "单个触发线索，命题人设置的高频挖坑表述/逻辑陷阱/概念混淆点", 
        "fixed_reaction": "唯一、直接、无需思考、可直接背诵形成条件反射的固化反应" 
      } 
    ], 
    "同类题迁移触发线索": [ 
      { 
        "trigger_clue": "单个触发线索，本题的考法/命题逻辑/设问角度", 
        "fixed_reaction": "唯一、直接、无需思考、可直接背诵形成条件反射的固化反应" 
      } 
    ] 
  } 
} 
```"""


@dataclass
class QuestionAnalysis:
    question_basic_info: dict
    module_1_basic_model_analysis: dict
    module_2_student_trial_error_analysis: list
    module_3_multi_dimensional_solution_analysis: dict
    module_4_neural_stimulus_trigger_points: dict
    raw_response: str
    
    def to_dict(self) -> dict:
        return {
            "question_basic_info": self.question_basic_info,
            "module_1_basic_model_analysis": self.module_1_basic_model_analysis,
            "module_2_student_trial_error_analysis": self.module_2_student_trial_error_analysis,
            "module_3_multi_dimensional_solution_analysis": self.module_3_multi_dimensional_solution_analysis,
            "module_4_neural_stimulus_trigger_points": self.module_4_neural_stimulus_trigger_points
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


def generate_question_analysis(
    question: ProcessedQuestion,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
) -> QuestionAnalysis:
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
    
    prompt_text = f"""请对以下题目进行全维度预处理分析：

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
                "content": SYSTEM_PROMPT_V2
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
    
    return QuestionAnalysis(
        question_basic_info=result.get("question_basic_info", {}),
        module_1_basic_model_analysis=result.get("module_1_basic_model_analysis", {}),
        module_2_student_trial_error_analysis=result.get("module_2_student_trial_error_analysis", []),
        module_3_multi_dimensional_solution_analysis=result.get("module_3_multi_dimensional_solution_analysis", {}),
        module_4_neural_stimulus_trigger_points=result.get("module_4_neural_stimulus_trigger_points", {}),
        raw_response=raw_response
    )


def generate_analysis_by_id(
    data_dir: str,
    question_id: str,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
) -> Optional[QuestionAnalysis]:
    question = load_question_by_id(data_dir, question_id)
    if question is None:
        return None
    return generate_question_analysis(question, api_key, model)


def save_analysis_to_json(
    data_dir: str,
    question_id: str,
    analysis: QuestionAnalysis
) -> bool:
    file_path = os.path.join(data_dir, f"{question_id}.json")
    
    if not os.path.exists(file_path):
        return False
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    data["question_analysis"] = analysis.to_dict()
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return True


def preprocess_and_save_v2(
    data_dir: str,
    question_id: str,
    api_key: Optional[str] = None,
    model: str = "doubao-seed-2-0-pro-260215",
) -> Optional[QuestionAnalysis]:
    analysis = generate_analysis_by_id(data_dir, question_id, api_key, model)
    
    if analysis is None:
        return None
    
    save_analysis_to_json(data_dir, question_id, analysis)
    
    return analysis


if __name__ == "__main__":
    data_dir = r"d:\space\html\print\data"
    question_id = "20260314104304"
    
    print(f"正在预处理题目: {question_id}")
    print("=" * 60)
    
    analysis = preprocess_and_save_v2(data_dir, question_id)
    
    if analysis:
        print(f"题目类型: {analysis.question_basic_info.get('question_type', '')}")
        print(f"适配学段: {analysis.question_basic_info.get('target_grade', '')}")
        print(f"核心考点: {analysis.question_basic_info.get('core_examination_points', '')}")
        print()
        print("模块1 - 基题模型分析:")
        model_analysis = analysis.module_1_basic_model_analysis
        print(f"  基题模型: {model_analysis.get('base_model_name', '')}")
        print(f"  适配阶段: {model_analysis.get('suitable_practice_stage', '')}")
        print()
        print("模块4 - 神经刺激触发点:")
        trigger_points = analysis.module_4_neural_stimulus_trigger_points
        for category, items in trigger_points.items():
            print(f"  {category}:")
            for item in items[:2]:
                print(f"    - {item.get('trigger_clue', '')}")
        print()
        print(f"结果已保存到: {os.path.join(data_dir, f'{question_id}.json')}")
    else:
        print("题目不存在")
