import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY", ""),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
)


async def analyze_resume(resume_text: str) -> dict:
    """AI分析简历，四维度评分"""
    prompt = f"""你是资深HR和简历专家。请分析以下简历，给出四维度评分（每项1-10分）和总体评价。
    
返回严格JSON格式：
{{
    "overall_score": 数字,
    "dimensions": {{
        "content": {{"score": 数字, "comment": "评价"}},
        "structure": {{"score": 数字, "comment": "评价"}},
        "keywords": {{"score": 数字, "comment": "评价"}},
        "formatting": {{"score": 数字, "comment": "评价"}}
    }},
    "summary": "总体评价，不超过100字"
}}

简历内容：
{resume_text[:4000]}
"""
    try:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1024,
        )
        content = resp.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content)
    except Exception as e:
        return {
            "overall_score": 0,
            "dimensions": {},
            "summary": f"分析失败: {str(e)}",
        }


async def optimize_resume(resume_text: str, target_position: str = "") -> dict:
    """AI优化简历"""
    position_hint = f"\n目标岗位: {target_position}" if target_position else ""
    prompt = f"""你是资深简历优化专家。请优化以下简历，使其更专业、更有竞争力。
{position_hint}

要求：
1. 保留真实经历，优化表达方式
2. 突出量化成果（使用数字）
3. 使用行业关键词
4. 结构清晰、简洁有力

返回严格JSON格式：
{{
    "optimized_resume": "优化后的完整简历（Markdown格式）",
    "changes": ["修改点1", "修改点2", ...],
    "keywords_added": ["关键词1", "关键词2", ...]
}}

原始简历：
{resume_text[:4000]}
"""
    try:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=4096,
        )
        content = resp.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content)
    except Exception as e:
        return {"optimized_resume": "", "changes": [], "keywords_added": [], "error": str(e)}


async def generate_resume(user_info: dict) -> dict:
    """根据用户输入的信息，AI一键生成简历"""
    prompt = f"""你是专业简历撰写专家。根据用户提供的信息，生成一份专业、完整的简历。

用户信息：
- 姓名: {user_info.get('name', '未提供')}
- 求职意向: {user_info.get('target_position', '未提供')}
- 工作经历: {user_info.get('experience', '未提供')}
- 教育背景: {user_info.get('education', '未提供')}
- 技能: {user_info.get('skills', '未提供')}
- 项目经验: {user_info.get('projects', '未提供')}
- 其他: {user_info.get('others', '无')}

要求：
1. 简历结构完整：个人信息、求职意向、工作经历、项目经验、教育背景、技能、自我评价
2. 突出量化成果，使用具体数据
3. 语言专业简洁，适合商务风格
4. 使用行业关键词

返回严格JSON格式：
{{
    "resume": "完整简历内容（Markdown格式）",
    "suggestions": ["优化建议1", "建议2"]
}}
"""
    try:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=4096,
        )
        content = resp.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content)
    except Exception as e:
        return {"resume": "", "suggestions": [], "error": str(e)}
