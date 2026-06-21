"""
MySQL 数据库连接与操作模块
基于 phpstudy_pro 内置 MySQL 8.0.12
"""
import os
import json
import aiomysql
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("MYSQLHOST", os.getenv("MYSQL_HOST", "127.0.0.1")),
    "port": int(os.getenv("MYSQLPORT", os.getenv("MYSQL_PORT", "3306"))),
    "user": os.getenv("MYSQLUSER", os.getenv("MYSQL_USER", "root")),
    "password": os.getenv("MYSQLPASSWORD", os.getenv("MYSQL_PASSWORD", "root")),
    "db": os.getenv("MYSQLDATABASE", os.getenv("MYSQL_DB", "resume_builder")),
    "charset": "utf8mb4",
    "autocommit": True,
}

_pool = None


async def get_pool():
    global _pool
    if _pool is None:
        _pool = await aiomysql.create_pool(
            minsize=2,
            maxsize=10,
            **DB_CONFIG,
        )
    return _pool


async def close_pool():
    global _pool
    if _pool:
        _pool.close()
        await _pool.wait_closed()
        _pool = None


async def execute(sql: str, args=None):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql, args)
            return cur


# ==================== 简历 CRUD ====================

async def create_resume(resume_id: str, file_name: str, file_path: str, original_text: str):
    cur = await execute(
        "INSERT INTO resumes (id, filename, original_text) VALUES (%s, %s, %s, %s)",
        (resume_id, file_name, file_path, original_text),
    )
    return resume_id


async def get_resume(resume_id: str):
    cur = await execute("SELECT * FROM resumes WHERE id = %s", (resume_id,))
    row = await cur.fetchone()
    if row:
        row["suggestions"] = json.loads(row["suggestions"]) if row.get("suggestions") else None
    return row


async def update_resume_analysis(resume_id: str, analysis: dict):
    await execute(
        "UPDATE resumes SET score=%s, suggestions=%s WHERE id=%s",
        (analysis.get("overall_score", 0), json.dumps(analysis.get("dimensions", []), ensure_ascii=False), resume_id),
    )


async def update_resume_optimized(resume_id: str, optimized: dict):
    await execute(
        "UPDATE resumes SET optimized_text=%s WHERE id=%s",
        (optimized.get("optimized_text", ""), resume_id),
    )


async def create_generated_resume(resume_id: str, user_info: dict, generated_text: str, suggestions: list):
    await execute(
        "INSERT INTO resumes (id, original_text, optimized_text, suggestions) VALUES (%s, %s, %s, %s)",
        (resume_id, json.dumps(user_info, ensure_ascii=False), generated_text, json.dumps(suggestions, ensure_ascii=False)),
    )


async def list_resumes():
    cur = await execute("SELECT id, filename, created_at, score, optimized_text FROM resumes ORDER BY created_at DESC")
    rows = await cur.fetchall()
    items = []
    for r in rows:
        items.append({
            "id": r["id"],
            "file_name": r.get("filename", "AI生成简历"),
            "created_at": str(r.get("created_at", "")),
            "has_analysis": r.get("score", 0) > 0,
            "has_optimized": bool(r.get("optimized_text")),
        })
    return items
