"""
拍照任務產生服務

從 field_map 自動產生拍照任務清單，
將表單欄位分類為需拍照的檢查項目和不需拍照的基本資訊。
"""

import logging
from typing import Optional
from datetime import datetime

from app.constants import (
    BASIC_INFO_KEYWORDS, CONCLUSION_KEYWORDS,
    JUDGMENT_KEYWORDS, REMARKS_KEYWORDS,
)

logger = logging.getLogger(__name__)


class PhotoTaskService:
    """拍照任務產生服務"""

    async def generate_photo_tasks(
        self,
        field_map: list[dict],
    ) -> dict:
        """
        從 field_map 自動產生「拍照任務清單」

        將表單欄位分為兩類：
        1. basic_info_fields: 不需要拍照，可直接手動填入的基本資訊欄位
        2. photo_tasks: 需要拍照佐證的檢查項目，每個項目可對應多個欄位

        核心邏輯：
        - 同一列(row)的 數值欄位 + 判定欄位 + 備註欄位 → 合併為一個拍照任務
        - 純文字的基本資訊欄位（日期、人員、設備名稱等）→ 歸到 basic_info
        - 結論/簽核類欄位 → 不產生拍照任務

        Returns:
            {
                "photo_tasks": [...],
                "basic_info_fields": [...],
                "conclusion_fields": [...],
                "stats": { "total_tasks": N, "total_basic": N, "total_conclusion": N }
            }
        """
        basic_info_fields = []
        conclusion_fields = []
        # 暫存: row_key -> { "fields": [...], "primary_name": str }
        row_groups: dict[str, dict] = {}
        ungrouped_inspection = []

        for field in field_map:
            name = field.get("field_name", "").strip()
            ftype = field.get("field_type", "text")
            label_loc = field.get("label_location", {})

            # 跳過空名欄位
            if not name:
                continue

            # 分類 1: 結論/簽核類（優先判斷，因為「簽名」含有「姓名」等基本資訊關鍵字）
            if self._is_conclusion_field(name):
                conclusion_fields.append({
                    "field_id": field["field_id"],
                    "field_name": name,
                    "field_type": ftype,
                    "value_location": field.get("value_location"),
                })
                continue

            # 分類 2: 基本資訊欄位（不需要拍照）
            if self._is_basic_info_field(name):
                basic_info_fields.append({
                    "field_id": field["field_id"],
                    "field_name": name,
                    "field_type": ftype,
                    "value_location": field.get("value_location"),
                    "default_value": self._get_default_value(name, ftype),
                })
                continue

            # 分類 3: 檢查項目 → 嘗試按 row 分組
            row_key = self._get_row_key(label_loc)
            if row_key:
                if row_key not in row_groups:
                    row_groups[row_key] = {
                        "fields": [],
                        "primary_name": None,
                        "row_index": label_loc.get("row", 0),
                    }

                row_groups[row_key]["fields"].append(field)

                # 確定主要名稱（非判定、非備註的欄位名稱）
                if (not self._is_judgment_field(name) and
                        not self._is_remarks_field(name) and
                        row_groups[row_key]["primary_name"] is None):
                    row_groups[row_key]["primary_name"] = name
            else:
                ungrouped_inspection.append(field)

        # 建立拍照任務
        photo_tasks = []
        sequence = 1

        # 從 row_groups 產生任務（按 row 排序）
        sorted_groups = sorted(
            row_groups.items(),
            key=lambda x: x[1].get("row_index", 0)
        )

        for row_key, group in sorted_groups:
            fields = group["fields"]
            primary_name = group["primary_name"] or fields[0].get("field_name", "檢查項目")

            # 分類欄位角色
            value_field_ids = []
            judgment_field_ids = []
            remarks_field_ids = []
            expected_type = "text"
            expected_unit = ""

            for f in fields:
                fname = f.get("field_name", "")
                fid = f["field_id"]
                ft = f.get("field_type", "text")

                if self._is_judgment_field(fname):
                    judgment_field_ids.append(fid)
                elif self._is_remarks_field(fname):
                    remarks_field_ids.append(fid)
                else:
                    value_field_ids.append(fid)
                    if ft == "number":
                        expected_type = "number"
                        expected_unit = self._guess_unit(fname)

            photo_tasks.append({
                "task_id": f"photo_{sequence:03d}",
                "field_ids": value_field_ids + judgment_field_ids + remarks_field_ids,
                "value_field_ids": value_field_ids,
                "judgment_field_ids": judgment_field_ids,
                "remarks_field_ids": remarks_field_ids,
                "display_name": primary_name,
                "photo_hint": self._generate_photo_hint(primary_name, expected_type, expected_unit),
                "expected_type": expected_type,
                "expected_unit": expected_unit,
                "sequence": sequence,
                "row_key": row_key,
            })
            sequence += 1

        # 未分組的檢查欄位 → 各自成為一個拍照任務
        for f in ungrouped_inspection:
            fname = f.get("field_name", "檢查項目")
            ft = f.get("field_type", "text")
            unit = self._guess_unit(fname) if ft == "number" else ""

            photo_tasks.append({
                "task_id": f"photo_{sequence:03d}",
                "field_ids": [f["field_id"]],
                "value_field_ids": [f["field_id"]],
                "judgment_field_ids": [],
                "remarks_field_ids": [],
                "display_name": fname,
                "photo_hint": self._generate_photo_hint(fname, ft, unit),
                "expected_type": ft,
                "expected_unit": unit,
                "sequence": sequence,
                "row_key": None,
            })
            sequence += 1

        return {
            "photo_tasks": photo_tasks,
            "basic_info_fields": basic_info_fields,
            "conclusion_fields": conclusion_fields,
            "stats": {
                "total_tasks": len(photo_tasks),
                "total_basic": len(basic_info_fields),
                "total_conclusion": len(conclusion_fields),
                "total_fields_covered": (
                    sum(len(t["field_ids"]) for t in photo_tasks) +
                    len(basic_info_fields) +
                    len(conclusion_fields)
                ),
            },
        }

    # ---- 拍照任務輔助方法 ----

    def _is_basic_info_field(self, name: str) -> bool:
        """判斷是否為基本資訊欄位（不需要拍照）"""
        return any(kw in name for kw in BASIC_INFO_KEYWORDS)

    def _is_conclusion_field(self, name: str) -> bool:
        """判斷是否為結論/簽核類欄位"""
        return any(kw in name for kw in CONCLUSION_KEYWORDS)

    def _is_judgment_field(self, name: str) -> bool:
        """判斷是否為判定類欄位（排除備註類優先）"""
        # 備註類優先（「異常說明」含有「異常」但應歸類為備註）
        if self._is_remarks_field(name):
            return False
        return any(kw in name for kw in JUDGMENT_KEYWORDS)

    def _is_remarks_field(self, name: str) -> bool:
        """判斷是否為備註類欄位"""
        return any(kw in name for kw in REMARKS_KEYWORDS)

    def _get_row_key(self, label_location: dict) -> Optional[str]:
        """從 label_location 取得 row key，用於同列欄位合併"""
        if not label_location:
            return None
        sheet = label_location.get("sheet", "")
        row = label_location.get("row")
        if row is not None:
            return f"{sheet}_row{row}"
        # Word 表格
        table_idx = label_location.get("table_index")
        row_idx = label_location.get("row_index")
        if table_idx is not None and row_idx is not None:
            return f"table{table_idx}_row{row_idx}"
        return None

    def _get_default_value(self, name: str, field_type: str) -> Optional[str]:
        """為基本資訊欄位產生預設值建議"""
        if '日期' in name or field_type == 'date':
            return datetime.now().strftime("%Y-%m-%d")
        return None

    def _guess_unit(self, name: str) -> str:
        """從欄位名稱猜測量測單位"""
        # 注意: 順序很重要！「絕緣電阻」要先匹配「絕緣」(MΩ)，不能先匹配「電阻」(Ω)
        # 使用 list of tuples 保證順序
        unit_map_ordered = [
            ('絕緣', 'MΩ'),    # 絕緣電阻 → MΩ (必須在「電阻」前面)
            ('接地電阻', 'Ω'),  # 接地電阻 → Ω
            ('電阻', 'Ω'),
            ('電壓', 'V'), ('電流', 'A'),
            ('溫度', '°C'), ('壓力', 'kPa'), ('頻率', 'Hz'), ('轉速', 'rpm'),
            ('振動', 'mm/s'), ('噪音', 'dB'), ('油位', 'mm'), ('水位', 'mm'),
            ('濕度', '%RH'), ('功率', 'kW'), ('流量', 'L/min'),
        ]
        # 不再使用 dict（dict 在 Python 3.7+ 有序，但語義上不保證優先級）
        unit_map = dict(unit_map_ordered)  # 保持向後相容，但改用有序搜尋
        for kw, unit in unit_map_ordered:
            if kw in name:
                return unit
        return ""

    def _generate_photo_hint(self, name: str, expected_type: str, unit: str) -> str:
        """產生拍照提示語"""
        if expected_type == "number" and unit:
            return f"請拍攝 {name} 的量測儀表讀數（單位: {unit}）"
        elif expected_type == "number":
            return f"請拍攝 {name} 的量測數值"
        elif 'checkbox' in expected_type:
            return f"請拍攝 {name} 的現場狀況"
        else:
            return f"請拍攝 {name} 的現場照片"
