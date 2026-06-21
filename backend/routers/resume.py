import os
import uuid
import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from services import ai_service, file_parser
from db import (
    create_resume, get_resume, update_resume_analysis,
    update_resume_optimized, create_generated_resume, list_resumes,
)

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


class UserInfoRequest(BaseModel):
    name: str = ""
    target_position: str = ""
    experience: str = ""
    education: str = ""
    skills: str = ""
    projects: str = ""
    others: str = ""


class OptimizeRequest(BaseModel):
    resume_id: str = ""
    resume_text: str = ""
    target_position: str = ""


# ==================== 文件上传 + 分析 ====================

@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    """上传简历文件，解析文本并返回"""
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("pdf", "docx", "doc", "txt", "md"):
        raise HTTPException(400, detail=f"不支持的文件格式: .{ext}")

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.{ext}")
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    text = await file_parser.parse_file(file_path)

    resume_id = str(uuid.uuid4())
    await create_resume(resume_id, file.filename, file_path, text)

    return {
        "resume_id": resume_id,
        "file_name": file.filename,
        "text": text,
        "text_length": len(text),
    }


# ==================== AI 简历分析 ====================

@router.post("/analyze")
async def analyze_resume(req: OptimizeRequest):
    """AI四维度分析简历"""
    if req.resume_id:
        row = await get_resume(req.resume_id)
        if row:
            text = row.get("original_text", "")
        else:
            raise HTTPException(404, detail="简历不存在")
    elif req.resume_text:
        text = req.resume_text
    else:
        raise HTTPException(400, detail="请提供简历文本或简历ID")

    if len(text) < 50:
        raise HTTPException(400, detail="简历内容过短，请提供完整简历")

    result = await ai_service.analyze_resume(text)

    if req.resume_id:
        await update_resume_analysis(req.resume_id, result)

    return result


# ==================== AI 简历优化 ====================

@router.post("/optimize")
async def optimize_resume(req: OptimizeRequest):
    """AI优化简历"""
    if req.resume_id:
        row = await get_resume(req.resume_id)
        if row:
            text = row.get("original_text", "")
        else:
            raise HTTPException(404, detail="简历不存在")
    elif req.resume_text:
        text = req.resume_text
    else:
        raise HTTPException(400, detail="请提供简历文本或简历ID")

    if len(text) < 50:
        raise HTTPException(400, detail="简历内容过短")

    result = await ai_service.optimize_resume(text, req.target_position)

    if req.resume_id:
        await update_resume_optimized(req.resume_id, result)

    return result


# ==================== AI 一键生成简历 ====================

@router.post("/generate")
async def generate_resume(req: UserInfoRequest):
    """根据用户信息AI一键生成简历"""
    user_info = req.model_dump()

    has_content = any(v for k, v in user_info.items() if v and k != "others")
    if not has_content:
        raise HTTPException(400, detail="请至少填写一项内容")

    result = await ai_service.generate_resume(user_info)

    resume_id = str(uuid.uuid4())
    await create_generated_resume(
        resume_id, user_info,
        result.get("resume", ""),
        result.get("suggestions", []),
    )

    result["resume_id"] = resume_id
    return result


# ==================== 简历列表 ====================

@router.get("/list")
async def list_resumes_api():
    """获取所有简历列表"""
    items = await list_resumes()
    return {"total": len(items), "items": items}


# ==================== 获取单份简历详情 ====================

@router.get("/{resume_id}")
async def get_resume_api(resume_id: str):
    """获取单份简历详情"""
    row = await get_resume(resume_id)
    if not row:
        raise HTTPException(404, detail="简历不存在")
    return row
