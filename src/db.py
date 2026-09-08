import pg8000
from config import DB_CONFIG


def get_connection():
    """返回一个新的数据库连接，autocommit 关闭以便手动管理事务。"""
    conn = pg8000.connect(**DB_CONFIG)
    conn.autocommit = False
    return conn


def execute_query(sql, params=None, fetch=True):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params if params is not None else ())
        if fetch:
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description] if cur.description else []
            return cols, rows
        return None, None
    finally:
        conn.close()


def execute_update(sql, params=None):
    """
    执行 INSERT / UPDATE / DELETE（参数化），提交并返回影响行数。
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params if params is not None else ())
        conn.commit()
        return cur.rowcount
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def call_procedure(proc_name, params=None):
    conn = get_connection()
    try:
        cur = conn.cursor()
        if params:
            placeholders = ','.join(['%s'] * len(params))
            cur.execute(f"SELECT * FROM {proc_name}({placeholders})", params)
        else:
            cur.execute(f"SELECT * FROM {proc_name}()")
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description] if cur.description else []
        return cols, rows
    finally:
        conn.close()
