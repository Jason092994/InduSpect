"""
表單處理共用工具函數

被多個服務共用的欄位偵測、類型推測、值轉換等工具
"""

import re
import logging

from app.constants import FIELD_KEYWORDS

logger = logging.getLogger(__name__)


def is_field_label(text: str) -> bool:
    """判斷文字是否為欄位標籤"""
    text = text.strip()
    if not text or len(text) > 50:
        return False
    return any(kw in text for kw in FIELD_KEYWORDS)


def is_placeholder(text: str) -> bool:
    """判斷文字是否為佔位符"""
    text = text.strip()
    if not text:
        return True
    # 常見佔位符模式
    placeholder_patterns = [
        r'^[_＿]{2,}$',     # 底線
        r'^\{\{.*\}\}$',    # {{placeholder}}
        r'^<.*>$',          # <placeholder>
        r'^\[.*\]$',        # [placeholder]
        r'^/{2,}$',         # ///
        r'^\s+$',           # 純空白
    ]
    return any(re.match(p, text) for p in placeholder_patterns)


def guess_field_type(field_name: str) -> str:
    """猜測欄位類型"""
    name_lower = field_name.lower()

    if any(kw in name_lower for kw in ['日期', 'date', '時間', 'time']):
        return 'date'
    elif any(kw in name_lower for kw in [
        '數量', '數值', 'number', '金額', '溫度', '壓力',
        '電流', '電壓', '轉速', '流量', '讀數', '頻率',
        '振動', '噪音', '油位', '水位', '濕度',
    ]):
        return 'number'
    elif any(kw in name_lower for kw in [
        '是否', '確認', 'check', '合格', '判定', '正常', '異常',
    ]):
        return 'checkbox'
    else:
        return 'text'


def convert_value(value, field_type: str):
    """根據欄位類型轉換值"""
    if value is None:
        return None

    if field_type == 'number':
        try:
            if '.' in str(value):
                return float(value)
            return int(value)
        except (ValueError, TypeError):
            return str(value)
    elif field_type == 'checkbox':
        v = str(value).strip().lower()
        if v in ['true', '1', '是', '合格', '正常', 'yes', 'ok', '通過']:
            return '合格'
        elif v in ['false', '0', '否', '不合格', '異常', 'no', 'ng', '不通過']:
            return '不合格'
        return str(value)
    elif field_type == 'date':
        return str(value)
    else:
        return str(value)


def is_section_header(text: str) -> bool:
    """判斷文字是否為區段標題（而非可填入的欄位）"""
    text = text.strip()
    # 中文編號開頭的區段標題：一、二、三、... 或 （一）（二）...
    if re.match(r'^[一二三四五六七八九十]+[、．.]', text):
        return True
    if re.match(r'^[（(][一二三四五六七八九十]+[）)]', text):
        return True
    # 表格標題列的表頭欄位
    header_patterns = ['項次', '檢查項目', '檢查標準', '檢查要點', '量測項目',
                       '量測位置', '判定', '備註/異常說明', '備註']
    if text in header_patterns:
        return True
    return False


def is_non_field_item(text: str) -> bool:
    """判斷文字是否不應作為模板欄位（標題、表頭、注意事項等）"""
    text = text.strip()
    # 過長或過短的不太可能是欄位
    if len(text) > 30 or len(text) < 2:
        return True
    # 區段標題
    if is_section_header(text):
        return True
    # 常見非欄位文字
    non_field_patterns = [
        r'^注意事項',
        r'^簽核$',
        r'^\d+\.\s',  # 編號開頭的注意事項
        r'^□',         # 勾選項目描述
    ]
    return any(re.match(p, text) for p in non_field_patterns)


def replace_paragraph_text_preserve_format(paragraph, new_text: str):
    """替換段落文字但保留第一個 run 的格式"""
    if not paragraph.runs:
        paragraph.text = new_text
        return

    # 保留第一個 run 的格式
    first_run = paragraph.runs[0]

    # 清除所有 runs
    for run in paragraph.runs:
        run.text = ""

    # 在第一個 run 中設定新文字
    first_run.text = new_text
