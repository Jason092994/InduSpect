"""
定檢歷史資料服務

Sprint 3 Task 3.3: 儲存/查詢歷史檢查資料
Sprint 3 Task 3.4: 前次數值自動帶入 + 趨勢分析

第一版使用 SQLite 本地儲存，未來可遷移至 Supabase/PostgreSQL
"""

import json
import uuid
import logging
import sqlite3
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class HistoryService:
    """定檢歷史資料服務"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            # 預設路徑
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "inspection_history.db")

        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化資料庫"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS inspection_history (
                    history_id TEXT PRIMARY KEY,
                    equipment_id TEXT NOT NULL,
                    equipment_name TEXT DEFAULT '',
                    template_id TEXT DEFAULT '',
                    inspection_date TEXT NOT NULL,
                    inspector TEXT DEFAULT '',
                    results_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_equipment_id
                ON inspection_history (equipment_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_inspection_date
                ON inspection_history (inspection_date)
            """)
            conn.commit()
        finally:
            conn.close()

    # ============ 儲存 ============

    async def save_inspection(
        self,
        equipment_id: str,
        equipment_name: str = "",
        template_id: str = "",
        inspection_date: str = "",
        inspector: str = "",
        results: list[dict] = None,
    ) -> str:
        """
        儲存一次定檢記錄

        results 格式:
        [
            {"field_name": "絕緣電阻 R相", "value": 52.3, "unit": "MΩ", "judgment": "pass"},
            ...
        ]

        回傳: history_id
        """
        history_id = str(uuid.uuid4())
        if not inspection_date:
            inspection_date = datetime.now().strftime("%Y-%m-%d")

        results = results or []

        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """INSERT INTO inspection_history
                   (history_id, equipment_id, equipment_name, template_id,
                    inspection_date, inspector, results_json, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    history_id,
                    equipment_id,
                    equipment_name,
                    template_id,
                    inspection_date,
                    inspector,
                    json.dumps(results, ensure_ascii=False),
                    datetime.now().isoformat(),
                )
            )
            conn.commit()
            logger.info(f"Saved inspection history: {history_id} for {equipment_id}")
        finally:
            conn.close()

        return history_id

    # ============ 查詢 ============

    async def get_history(
        self,
        equipment_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict]:
        """查詢某設備的歷史記錄（最新在前）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """SELECT * FROM inspection_history
                   WHERE equipment_id = ?
                   ORDER BY inspection_date DESC, created_at DESC
                   LIMIT ? OFFSET ?""",
                (equipment_id, limit, offset)
            ).fetchall()

            return [self._row_to_dict(row) for row in rows]
        finally:
            conn.close()

    async def get_latest(self, equipment_id: str) -> Optional[dict]:
        """查詢某設備最近一次記錄"""
        records = await self.get_history(equipment_id, limit=1)
        return records[0] if records else None

    async def get_by_id(self, history_id: str) -> Optional[dict]:
        """根據 history_id 查詢"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT * FROM inspection_history WHERE history_id = ?",
                (history_id,)
            ).fetchone()

            return self._row_to_dict(row) if row else None
        finally:
            conn.close()

    # ============ Task 3.4: 前次數值帶入 ============

    async def get_previous_values(
        self,
        equipment_id: str,
        field_names: list[str],
    ) -> dict:
        """
        取得前次對應欄位的值

        回傳: {field_name: {"value": ..., "date": ..., "unit": ...}}
        """
        latest = await self.get_latest(equipment_id)
        if not latest:
            return {}

        prev_values = {}
        results = latest.get("results", [])

        for fn in field_names:
            # 嘗試精確匹配
            for r in results:
                r_name = r.get("field_name", "")
                if r_name == fn or fn in r_name or r_name in fn:
                    prev_values[fn] = {
                        "value": r.get("value"),
                        "unit": r.get("unit", ""),
                        "date": latest.get("inspection_date", ""),
                    }
                    break

        return prev_values

    async def analyze_trend(
        self,
        equipment_id: str,
        field_name: str,
        num_records: int = 5,
    ) -> Optional[dict]:
        """
        分析某項數值的趨勢

        回傳:
        {
            "field_name": "絕緣電阻 R相",
            "values": [80, 65, 52],        # 從舊到新
            "dates": ["2025-09", "2025-12", "2026-03"],
            "trend": "declining",           # rising, declining, stable, insufficient
            "consecutive_decline": 3,       # 連續下降次數
            "warning": "⚠ 絕緣電阻連續 3 次下降 (80→65→52 MΩ)，建議安排維修"
        }
        """
        records = await self.get_history(equipment_id, limit=num_records)

        if len(records) < 2:
            return {
                "field_name": field_name,
                "values": [],
                "dates": [],
                "trend": "insufficient",
                "consecutive_decline": 0,
                "warning": None,
            }

        # 取出各次記錄中的對應值（從舊到新）
        values = []
        dates = []

        for record in reversed(records):  # records 是最新在前，反轉為舊到新
            for r in record.get("results", []):
                r_name = r.get("field_name", "")
                if r_name == field_name or field_name in r_name or r_name in field_name:
                    try:
                        val = float(r.get("value", 0))
                        values.append(val)
                        dates.append(record.get("inspection_date", ""))
                    except (ValueError, TypeError):
                        pass
                    break

        if len(values) < 2:
            return {
                "field_name": field_name,
                "values": values,
                "dates": dates,
                "trend": "insufficient",
                "consecutive_decline": 0,
                "warning": None,
            }

        # 分析趨勢
        consecutive_decline = 0
        consecutive_rise = 0

        for i in range(1, len(values)):
            if values[i] < values[i-1]:
                consecutive_decline += 1
                consecutive_rise = 0
            elif values[i] > values[i-1]:
                consecutive_rise += 1
                consecutive_decline = 0
            else:
                consecutive_decline = 0
                consecutive_rise = 0

        if consecutive_decline >= 2:
            trend = "declining"
        elif consecutive_rise >= 2:
            trend = "rising"
        else:
            trend = "stable"

        # 產生警告
        warning = None
        if consecutive_decline >= 2:
            val_str = "→".join(str(v) for v in values[-consecutive_decline-1:])
            warning = f"⚠ {field_name}連續 {consecutive_decline+1} 次下降 ({val_str})，建議安排維修"

        return {
            "field_name": field_name,
            "values": values,
            "dates": dates,
            "trend": trend,
            "consecutive_decline": consecutive_decline,
            "warning": warning,
        }

    # ============ 刪除 ============

    async def delete_history(self, history_id: str) -> bool:
        """刪除指定記錄"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                "DELETE FROM inspection_history WHERE history_id = ?",
                (history_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    # ============ 工具 ============

    def _row_to_dict(self, row) -> dict:
        """將 SQLite Row 轉為 dict"""
        d = dict(row)
        d["results"] = json.loads(d.pop("results_json", "[]"))
        return d
