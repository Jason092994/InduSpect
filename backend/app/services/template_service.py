"""
模板庫服務 — Sprint 5 Task 5.2

管理預設模板（default templates）與使用者最近使用紀錄。
- 預設模板清單來自 templates_index.json
- 使用紀錄存 SQLite（與 history_service 同模式）
"""

import json
import os
import sqlite3
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class TemplateService:
    """模板庫服務"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "template_usage.db")

        self.db_path = db_path
        self._init_db()

        # 預設模板目錄
        self._data_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data",
            "default_templates",
        )

    def _init_db(self):
        """初始化模板使用紀錄資料庫"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS template_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    template_id TEXT NOT NULL,
                    file_name TEXT DEFAULT '',
                    used_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_template_usage_user
                ON template_usage(user_id, used_at DESC)
            """)
            conn.commit()
        finally:
            conn.close()

    def get_default_templates(self) -> list[dict]:
        """
        取得預設模板清單

        從 templates_index.json 讀取，回傳模板列表。
        每個模板包含: template_id, name, description, file_name, category
        """
        index_path = os.path.join(self._data_dir, "templates_index.json")

        if not os.path.exists(index_path):
            logger.warning(f"templates_index.json not found at {index_path}")
            return []

        try:
            with open(index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("templates", [])
        except Exception as e:
            logger.error(f"Failed to load templates_index.json: {e}")
            return []

    def get_recent_templates(self, user_id: str, limit: int = 10) -> list[dict]:
        """
        取得使用者最近使用的模板

        回傳格式:
        [
            {"template_id": "...", "file_name": "...", "used_at": "..."},
            ...
        ]
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                """
                SELECT template_id, file_name, used_at
                FROM template_usage
                WHERE user_id = ?
                ORDER BY used_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
            rows = cursor.fetchall()
            return [
                {
                    "template_id": row[0],
                    "file_name": row[1],
                    "used_at": row[2],
                }
                for row in rows
            ]
        finally:
            conn.close()

    def record_template_usage(
        self,
        user_id: str,
        template_id: str,
        file_name: str = "",
    ) -> bool:
        """
        記錄模板使用

        回傳 True 表示成功。
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                INSERT INTO template_usage (user_id, template_id, file_name, used_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, template_id, file_name, datetime.now().isoformat()),
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to record template usage: {e}")
            return False
        finally:
            conn.close()

    def get_template_file(self, template_id: str) -> Optional[bytes]:
        """
        取得模板檔案位元組

        根據 template_id 從 templates_index.json 查找對應檔名，
        讀取並回傳檔案內容。
        """
        templates = self.get_default_templates()
        target = None
        for t in templates:
            if t.get("template_id") == template_id:
                target = t
                break

        if target is None:
            logger.warning(f"Template not found: {template_id}")
            return None

        file_name = target.get("file_name", "")
        file_path = os.path.join(self._data_dir, file_name)

        if not os.path.exists(file_path):
            logger.warning(f"Template file not found: {file_path}")
            return None

        try:
            with open(file_path, "rb") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read template file: {e}")
            return None
