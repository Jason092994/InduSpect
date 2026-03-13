"""
InduSpect AI — 共用常數定義

集中管理所有魔術字串，避免散落各處
"""

from enum import Enum


# ============ 欄位類型 ============

class FieldType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    CHECKBOX = "checkbox"
    DUAL_COLUMN_CHECKBOX = "dual_column_checkbox"


# ============ 判定結果 ============

class Judgment(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    UNKNOWN = "unknown"


# ============ 檔案類型 ============

class FileType(str, Enum):
    XLSX = "xlsx"
    DOCX = "docx"


# ============ 值來源 ============

class ValueSource(str, Enum):
    AI_PHOTO = "ai_photo"
    MANUAL = "manual"
    HISTORY = "history"
    DEFAULT = "default"
    STANDARD = "standard"


# ============ 勾選符號 ============

DEFAULT_CHECK_SYMBOL = "✓"
ALTERNATIVE_CHECK_SYMBOLS = ["✓", "☑", "■", "√", "V", "v", "○", "●"]


# ============ 表單欄位關鍵字 ============

FIELD_KEYWORDS = [
    ':', '：', '日期', '姓名', '編號', '設備', '檢查', '備註',
    '人員', '地點', '位置', '廠區', '型號', '規格', '狀態', '狀況',
    '結果', '判定', '溫度', '壓力', '電流', '電壓', '轉速', '流量',
    '讀數', '數值', '合格', '不合格', '正常', '異常', '測量',
    '頻率', '振動', '噪音', '油位', '水位', '濕度',
]

BASIC_INFO_KEYWORDS = [
    '名稱', '編號', '日期', '時間', '人員', '姓名', '位置', '地點',
    '廠區', '廠商', '型號', '規格', '電話', '證照', '週期', '地址',
    '樓層', '區域', '天氣', '陪同', '部門', '單位', '公司', '製造商',
    '序號', '負責人', '聯絡', '工號', '年份', '月份',
]

JUDGMENT_KEYWORDS = ['合格', '不合格', '判定', '結果', '正常', '異常', '良好', '不良']
REMARKS_KEYWORDS = ['備註', '說明', '描述', '建議', '異常說明', '改善', '異常描述', '處理', '對策']
CONCLUSION_KEYWORDS = ['綜合', '結論', '整體', '複查', '簽核', '簽名', '審核']


# ============ 定檢資料可用欄位定義 ============

INSPECTION_FIELDS = {
    "equipment_name": {"label": "設備名稱", "type": FieldType.TEXT},
    "equipment_type": {"label": "設備類型", "type": FieldType.TEXT},
    "equipment_id": {"label": "設備編號", "type": FieldType.TEXT},
    "inspection_date": {"label": "檢查日期", "type": FieldType.DATE},
    "inspector_name": {"label": "檢查人員", "type": FieldType.TEXT},
    "location": {"label": "位置/廠區", "type": FieldType.TEXT},
    "condition_assessment": {"label": "狀況評估", "type": FieldType.TEXT},
    "anomaly_description": {"label": "異常描述", "type": FieldType.TEXT},
    "is_anomaly": {"label": "是否異常", "type": FieldType.CHECKBOX},
    "notes": {"label": "備註", "type": FieldType.TEXT},
    "extracted_values": {"label": "儀表讀數/量測值", "type": "dict"},
}


# ============ 照片相關常數 ============

PHOTO_MAX_WIDTH = 600
PHOTO_MAX_HEIGHT = 450
PHOTO_MAX_SIZE_KB = 500
PHOTO_QUALITY = 85
