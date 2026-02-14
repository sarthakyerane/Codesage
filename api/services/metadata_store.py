"""
MySQL metadata store - stores file and function info using aiomysql.
"""
import os
from contextlib import asynccontextmanager
from loguru import logger
import aiomysql

_pool = None


async def get_pool():
    global _pool
    if not _pool:
        _pool = await aiomysql.create_pool(
            host=os.getenv("MYSQL_HOST", "mysql"),
            port=int(os.getenv("MYSQL_PORT", 3306)),
            user=os.getenv("MYSQL_USER", "codesage_user"),
            password=os.getenv("MYSQL_PASSWORD", "codesage_pass"),
            db=os.getenv("MYSQL_DATABASE", "codesage"),
            autocommit=True, minsize=1, maxsize=10, charset="utf8mb4",
        )
        logger.info("MySQL pool created")
    return _pool


async def close_pool():
    global _pool
    if _pool:
        _pool.close()
        await _pool.wait_closed()
        _pool = None


@asynccontextmanager
async def get_cursor():
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            yield cur


async def upsert_file(file_path, file_name, function_count):
    async with get_cursor() as cur:
        await cur.execute(
            """INSERT INTO files (file_path, file_name, function_count) VALUES (%s, %s, %s)
               ON DUPLICATE KEY UPDATE file_name=VALUES(file_name),
               function_count=VALUES(function_count), upload_time=CURRENT_TIMESTAMP""",
            (file_path, file_name, function_count),
        )
        await cur.execute("SELECT id FROM files WHERE file_path=%s", (file_path,))
        return (await cur.fetchone())["id"]


async def get_file(file_id):
    async with get_cursor() as cur:
        await cur.execute("SELECT * FROM files WHERE id=%s", (file_id,))
        return await cur.fetchone()


async def delete_file(file_id):
    async with get_cursor() as cur:
        await cur.execute("DELETE FROM files WHERE id=%s", (file_id,))


async def insert_function(file_id, function_name, return_type, parameters,
                           line_start, line_end, complexity, tags, chroma_id, body_preview):
    tag_str = ",".join(tags)
    preview = body_preview[:500] if body_preview else ""
    async with get_cursor() as cur:
        await cur.execute(
            """INSERT INTO functions (file_id, function_name, return_type, parameters,
               line_start, line_end, complexity, tags, chroma_id, body_preview)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (file_id, function_name, return_type, parameters,
             line_start, line_end, complexity, tag_str, chroma_id, preview),
        )
        return cur.lastrowid


async def insert_call_edges(caller_id, callees):
    if not callees: return
    async with get_cursor() as cur:
        await cur.executemany(
            "INSERT INTO call_edges (caller_id, callee_name) VALUES (%s, %s)",
            [(caller_id, c) for c in callees],
        )


async def get_functions_by_file(file_id):
    async with get_cursor() as cur:
        await cur.execute("SELECT * FROM functions WHERE file_id=%s ORDER BY line_start", (file_id,))
        return await cur.fetchall()


async def get_function_by_name(name):
    async with get_cursor() as cur:
        await cur.execute(
            "SELECT f.*, fi.file_path FROM functions f JOIN files fi ON f.file_id=fi.id WHERE f.function_name=%s LIMIT 1",
            (name,),
        )
        return await cur.fetchone()


async def delete_functions_by_file(file_id):
    async with get_cursor() as cur:
        await cur.execute("DELETE FROM functions WHERE file_id=%s", (file_id,))


async def ping():
    try:
        async with get_cursor() as cur:
            await cur.execute("SELECT 1")
        return True
    except Exception:
        return False
