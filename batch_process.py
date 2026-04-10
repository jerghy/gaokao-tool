import requests
import json
import logging
import re
import os
from pathlib import Path

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

DEEPSEEK_API_KEY = "sk-a0d31013de044042ad66c4baec00df48"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1/chat/completions"

SYSTEM_PROMPT = """
你是严格输出JSON的中学英语教研专家，按以下规则处理文章：
1. 拆分文章为自然段落，每个段落对应1个JSON对象，所有对象放入JSON数组；
2. 每个对象必须包含3个字段：
   - "原文"：英文原文，核心实词首次出现标带圈序号（①②③…），全文连续编号；
   - "翻译"：准确通顺的中文译文；
   - "必背词汇"：标序词汇按「序号 单词/音标/词性.释义」格式，拓展词用Ⓡ开头，换行用\\n；
3. 词汇标序规则：仅标中高考核心实词，排除入门词/虚词/专有名词；
4. 输出仅保留纯JSON数组，无任何额外文字、注释、markdown、缩进换行。

# 核心任务
用户仅输入英语文章原文，你必须按以下要求完成处理：
1.  将原文按自然自然段拆分，每个自然段对应一个JSON对象，所有对象放入一个JSON数组中；
2.  每个JSON对象必须包含3个固定字段：`原文`、`翻译`、`必背词汇`，字段名不可修改、增减；
3.  全文核心词汇序号从`①`开始连续编号，不按段落重置序号，严格遵循词汇筛选与标注规则执行。

# 各字段强制执行细则
## 1. 「原文」字段
- 内容：对应自然段的完整英文原文，仅对符合规则的核心词汇，在**全文第一次出现时**，在单词右上角标注连续的带圈序号（①②③...），同一个单词重复出现时，不再重复标序；
- 标序词汇准入规则（必须同时满足基础门槛+任意1条核心条件）：
  - 基础门槛：必须是实词（动词/名词/形容词/副词），排除无词汇考点的虚词、功能词；
  - 核心入选条件（满足任意1条即可）：
    1.  国内中高考英语考纲要求掌握的核心词汇，非初一及以下入门级基础词；
    2.  中高考完形填空、阅读理解高频考查词，包含熟词生义、固定搭配核心词、易混形近词；
    3.  词根词缀明确，可延伸同根词群，符合构词法记忆逻辑的单词；
    4.  贴合文章主题的核心术语，是理解全文的关键实词；
- 绝对禁止标序清单（满足任意1条，一律不标序）：
  1.  小学/初一入门级超高频简单词（例：child, house, water, day, go, come, big, is, are等）；
  2.  纯功能虚词：介词、冠词、连词、代词、感叹词；
  3.  无通用考点的专属专有名词：人名、地名、专属机构名；
  4.  全文已标序的重复出现词汇。

## 2. 「翻译」字段
- 内容：对应自然段的完整、准确中文翻译，贴合原文语境，语句通顺符合中文表达习惯，无漏译、错译，严格遵循中学英语课文翻译规范。

## 3. 「必背词汇」字段
- 内容：仅收录当前自然段内**全文首次出现**的标序核心词汇，按序号从小到大排列，已在前面段落出现并标序的词汇，不得重复收录；
- 格式规范（严格对标示例）：
  1.  主词条格式：`序号 单词 /DJ英式音标/ 词性. 释义`，释义优先标注本文语境义，再补充中高考核心考纲义；
  2.  每个主词条下方绑定3-5个拓展词条，拓展词条用`Ⓡ`开头、缩进对齐，拓展优先级从高到低为：同根派生词 > 高频反义词/近义词/形近易混词 > 中高考必考固定搭配/短语；
  3.  词汇换行使用`\n`转义，确保JSON格式合法。

# 输出格式终极要求
1.  最终输出必须是**纯标准JSON格式**，不得包含JSON外的任何文字、注释、说明内容；
2.  整体结构为一个JSON数组，数组内的每个元素为对应一个自然段的JSON对象；
3.  所有字段名、字符串内容必须使用双引号包裹，JSON语法必须完全正确，无转义错误、格式错误。

# 执行示例（你必须100%对标此格式生成内容）
## 示例输入（用户仅输入这段原文）：
While running regularly can't make you live forever, the review says it is more effective at lengthening life than walking, cycling or swimming. Two of the authors of the review also made a study published in 2014 that showed a mere five to 10 minutes a day of running reduced the risk of heart disease and early deaths from all causes.

## 示例正确输出：
[
    {
        "原文": "While running regularly① can't make you live forever, the review says it is more effective② at lengthening③ life than walking, cycling④ or swimming. Two of the authors⑤ of the review also made a study published⑥ in 2014 that showed a mere five to 10 minutes a day of running reduced the risk of heart disease and early deaths from all causes⑦.",
        "翻译": "虽然定期跑步无法令你长生不老，但报告称它在延长寿命方面比散步、骑自行车或游泳更有效。该报告的两位作者还做了一项发表于2014年的研究，这项研究表明每天跑步仅五到十分钟，就降低了各种原因导致的心脏病和早逝的风险。",
        "必背词汇": "① regularly /ˈreɡjələrli/ adv. 定期地，有规律地\nⓇ regulate /ˈreɡjuleɪt/ v. 控制；管理\nⓇ regulation /ˌreɡjuˈleɪʃn/ n. 法规；管理\n② effective /ɪˈfektɪv/ adj. 有效的；起作用的\nⓇ effect /ɪˈfekt/ n. 影响；效果\nⓇ affect /əˈfekt/ v. 影响\nⓇ affection /əˈfekʃn/ n. 喜爱\n③ lengthen /ˈleŋθən/ v. (使)延长，(使)变长\nⓇ long /lɒŋ/ adj. 长的 adv. 长久地\nⓇ length /leŋθ/ n. 长度；篇幅\nⓇ strengthen /ˈstreŋθn/ v. 加强\nⓇ strength /streŋθ/ n. 力量；强度\n④ cycle /ˈsaɪkl/ v. 骑自行车 n. 自行车；循环\nⓇ bicycle /ˈbaɪsɪkl/ n. 自行车\nⓇ tricycle /ˈtraɪsɪkl/ n. 三轮脚踏车\n⑤ author /ˈɔːθə(r)/ n. 作者\nⓇ authority /ɔːˈθɒrəti/ n. 官方，当权者；权力\nⓇ authentic /ɔːˈθentɪk/ adj. 真正的\n⑥ publish /ˈpʌblɪʃ/ v. 发表；出版\nⓇ punish /ˈpʌnɪʃ/ v. 处罚\nⓇ public /ˈpʌblɪk/ adj. 公开的\n⑦ cause /kɔːz/ n. 原因 v. 导致\nⓇ reason /ˈriːzn/ n. 原因，理由"
    }
]
"""

def clean_ai_output(raw_output: str) -> str:
    cleaned = raw_output.strip()
    cleaned = re.sub(r'//.*?$', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
    json_match = re.search(r'\[.*\]', cleaned, flags=re.DOTALL)
    if json_match:
        cleaned = json_match.group(0)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    logging.debug(f"清洗后的JSON：{cleaned[:200]}...")
    return cleaned

def call_deepseek_json_mode(english_article: str) -> list:
    request_data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": english_article.strip()}
        ],
        "temperature": 0.0,
        "max_tokens": 8000,
        "stream": False,
        "response_format": {"type": "json_object"}
    }

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json; charset=utf-8"
    }

    try:
        response = requests.post(
            url=DEEPSEEK_BASE_URL,
            headers=headers,
            json=request_data,
            timeout=90
        )
        response.raise_for_status()
        api_resp = response.json()

        ai_raw_output = api_resp["choices"][0]["message"]["content"].strip()
        logging.info(f"AI原始输出：{ai_raw_output[:500]}...")

        cleaned_json = clean_ai_output(ai_raw_output)
        parsed_result = json.loads(cleaned_json)

        if not isinstance(parsed_result, list):
            raise ValueError(f"JSON不是数组格式，解析结果：{type(parsed_result)}")

        logging.info(f"JSON解析成功，共处理 {len(parsed_result)} 个段落")
        return parsed_result

    except requests.exceptions.RequestException as e:
        logging.error(f"API请求失败：{str(e)} | 响应码：{response.status_code if 'response' in locals() else '无'}")
        raise Exception(f"API请求错误：{str(e)}")
    except json.JSONDecodeError as e:
        logging.error(f"JSON解析失败！AI原始输出：{ai_raw_output[:500]}...")
        raise Exception(f"JSON格式错误：{str(e)}，请检查AI输出是否为合法JSON")
    except KeyError as e:
        logging.error(f"API返回字段缺失：{str(e)} | 原始返回：{api_resp}")
        raise Exception(f"返回结构异常，缺少字段：{str(e)}")
    except ValueError as e:
        logging.error(f"JSON格式校验失败：{str(e)}")
        raise Exception(f"JSON不是数组：{str(e)}")

def get_pending_files(article_dir: str, result_dir: str) -> list:
    article_path = Path(article_dir)
    result_path = Path(result_dir)
    
    result_path.mkdir(parents=True, exist_ok=True)
    
    existing_results = {f.stem for f in result_path.glob("*.json")}
    
    pending_files = []
    for txt_file in sorted(article_path.glob("*.txt")):
        if txt_file.stem not in existing_results:
            pending_files.append(txt_file)
    
    return pending_files

def batch_process():
    article_dir = r"d:\space\html\print\article"
    result_dir = r"d:\space\html\print\result"
    
    pending_files = get_pending_files(article_dir, result_dir)
    
    if not pending_files:
        logging.info("所有文件已处理完成，无需重复处理！")
        return
    
    logging.info(f"发现 {len(pending_files)} 个待处理文件：{[f.name for f in pending_files]}")
    
    for txt_file in pending_files:
        logging.info(f"\n{'='*50}\n开始处理：{txt_file.name}\n{'='*50}")
        
        try:
            with open(txt_file, "r", encoding="utf-8") as f:
                article_content = f.read()
            
            result = call_deepseek_json_mode(article_content)
            
            result_file = Path(result_dir) / f"{txt_file.stem}.json"
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logging.info(f"✓ 成功保存：{result_file}")
            
        except Exception as e:
            logging.error(f"✗ 处理失败 {txt_file.name}：{str(e)}")
            continue
    
    logging.info(f"\n{'='*50}\n批量处理完成！\n{'='*50}")

if __name__ == "__main__":
    batch_process()
