"""
測試動態模板建立功能

直接呼叫 FormFillService 的方法進行單元測試，
不需要啟動 FastAPI 伺服器。

由於環境中沒有 Gemini API key，AI 轉換會走 fallback 路徑。
"""

import asyncio
import json
import sys
import os

# 加入 backend 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# 設定 dummy key 讓 config 不會出錯
os.environ.setdefault('GEMINI_API_KEY', 'test-key-not-real')

# Mock google.generativeai to avoid cffi issues in this environment
import types
google_mod = types.ModuleType('google')
google_mod.generativeai = types.ModuleType('google.generativeai')
sys.modules['google'] = google_mod
sys.modules['google.generativeai'] = google_mod.generativeai

# Now provide a mock genai
mock_genai = google_mod.generativeai
mock_genai.configure = lambda **kwargs: None

class MockResponse:
    text = '{}'

class MockModel:
    def __init__(self, *a, **kw): pass
    def generate_content(self, *a, **kw): return MockResponse()

mock_genai.GenerativeModel = MockModel

# Prevent __init__.py from importing everything - mock the services package
mock_services = types.ModuleType('app.services')
sys.modules['app.services'] = mock_services
sys.modules['app.services.embedding'] = types.ModuleType('app.services.embedding')
sys.modules['app.services.rag'] = types.ModuleType('app.services.rag')

# Now import form_fill directly
import importlib.util
spec = importlib.util.spec_from_file_location(
    "app.services.form_fill",
    os.path.join(os.path.dirname(__file__), '..', 'backend', 'app', 'services', 'form_fill.py')
)
form_fill_mod = importlib.util.module_from_spec(spec)
sys.modules['app.services.form_fill'] = form_fill_mod
spec.loader.exec_module(form_fill_mod)
FormFillService = form_fill_mod.FormFillService


async def test_excel_template():
    """測試 Excel 定檢表 → InspectionTemplate"""
    print("=" * 60)
    print("測試 1: 電氣設備定期檢查表 (Excel)")
    print("=" * 60)

    excel_path = os.path.join(os.path.dirname(__file__), '電氣設備定期檢查表.xlsx')
    with open(excel_path, 'rb') as f:
        content = f.read()

    service = FormFillService()

    # Step 1: 測試深度分析
    print("\n--- Step 1: 深度分析 Excel 結構 ---")
    field_map = await service._deep_analyze_excel(content)
    print(f"偵測到 {len(field_map)} 個欄位:")
    for f in field_map[:10]:
        print(f"  • {f['field_name']} ({f['field_type']}) @ {f['label_location']}")
    if len(field_map) > 10:
        print(f"  ... 及其餘 {len(field_map) - 10} 個欄位")

    # Step 2: 測試原始文字擷取
    print("\n--- Step 2: 擷取原始文字 ---")
    raw_text = await service._extract_excel_text(content)
    print(f"擷取到 {len(raw_text)} 字元:")
    for line in raw_text.split('\n')[:8]:
        print(f"  {line}")
    print("  ...")

    # Step 3: 測試完整建立流程（會走 fallback）
    print("\n--- Step 3: 建立 InspectionTemplate ---")
    result = await service.create_template_from_file(
        file_content=content,
        file_name='電氣設備定期檢查表.xlsx',
        template_name='電氣設備定期檢查表',
        category='電氣設備',
        company='國立臺北科技大學',
        department='環安中心',
    )

    print(f"成功: {result['success']}")
    print(f"模板 ID: {result['template_id']}")
    print(f"欄位數: {result['field_count']}")
    print(f"區段數: {result['section_count']}")

    template = result['template']
    print(f"\n模板名稱: {template['template_name']}")
    print(f"版本: {template['template_version']}")
    print(f"類別: {template['category']}")

    for section in template['sections']:
        print(f"\n  Section: {section['section_title']} (ID: {section['section_id']})")
        print(f"  說明: {section.get('description', 'N/A')}")
        print(f"  欄位數: {len(section['fields'])}")
        for field in section['fields'][:5]:
            print(f"    - {field['label']} ({field['field_type']})")
        if len(section['fields']) > 5:
            print(f"    ... 及其餘 {len(section['fields']) - 5} 個欄位")

    # 驗證 source_file 綁定
    assert 'source_file' in template, "缺少 source_file 綁定"
    print(f"\n原始文件綁定: {template['source_file']['file_name']} ({template['source_file']['file_type']})")
    print(f"Field map 數量: {len(template['source_file']['field_map'])}")

    # 輸出完整 JSON
    output_path = os.path.join(os.path.dirname(__file__), 'output_excel_template.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(template, f, ensure_ascii=False, indent=2)
    print(f"\n完整模板 JSON 已儲存: {output_path}")

    return result


async def test_word_template():
    """測試 Word 定檢表 → InspectionTemplate"""
    print("\n" + "=" * 60)
    print("測試 2: 消防安全設備定期檢查表 (Word)")
    print("=" * 60)

    docx_path = os.path.join(os.path.dirname(__file__), '消防安全設備定期檢查表.docx')
    with open(docx_path, 'rb') as f:
        content = f.read()

    service = FormFillService()

    # Step 1: 深度分析
    print("\n--- Step 1: 深度分析 Word 結構 ---")
    field_map = await service._deep_analyze_word(content)
    print(f"偵測到 {len(field_map)} 個欄位:")
    for f in field_map[:10]:
        loc_type = f['label_location'].get('type', 'unknown')
        print(f"  • {f['field_name']} ({f['field_type']}) [{loc_type}]")
    if len(field_map) > 10:
        print(f"  ... 及其餘 {len(field_map) - 10} 個欄位")

    # Step 2: 原始文字
    print("\n--- Step 2: 擷取原始文字 ---")
    raw_text = await service._extract_word_text(content)
    print(f"擷取到 {len(raw_text)} 字元:")
    for line in raw_text.split('\n')[:8]:
        print(f"  {line}")
    print("  ...")

    # Step 3: 建立模板
    print("\n--- Step 3: 建立 InspectionTemplate ---")
    result = await service.create_template_from_file(
        file_content=content,
        file_name='消防安全設備定期檢查表.docx',
        template_name='消防安全設備定期檢查表',
        category='消防設備',
        company='國立臺北科技大學',
        department='環安中心',
    )

    print(f"成功: {result['success']}")
    print(f"模板 ID: {result['template_id']}")
    print(f"欄位數: {result['field_count']}")
    print(f"區段數: {result['section_count']}")

    template = result['template']
    for section in template['sections']:
        print(f"\n  Section: {section['section_title']} (ID: {section['section_id']})")
        print(f"  欄位數: {len(section['fields'])}")
        for field in section['fields'][:5]:
            print(f"    - {field['label']} ({field['field_type']})")
        if len(section['fields']) > 5:
            print(f"    ... 及其餘 {len(section['fields']) - 5} 個欄位")

    assert 'source_file' in template, "缺少 source_file 綁定"
    print(f"\n原始文件綁定: {template['source_file']['file_name']} ({template['source_file']['file_type']})")

    output_path = os.path.join(os.path.dirname(__file__), 'output_word_template.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(template, f, ensure_ascii=False, indent=2)
    print(f"\n完整模板 JSON 已儲存: {output_path}")

    return result


async def test_template_json_validity(template_json: dict):
    """驗證產生的模板 JSON 是否符合 InspectionTemplate 格式"""
    print("\n" + "=" * 60)
    print("驗證模板 JSON 格式")
    print("=" * 60)

    errors = []

    # 必要欄位
    required_keys = ['template_id', 'template_name', 'template_version', 'category',
                     'created_at', 'updated_at', 'metadata', 'sections']
    for key in required_keys:
        if key not in template_json:
            errors.append(f"缺少必要欄位: {key}")

    # metadata
    meta = template_json.get('metadata', {})
    meta_keys = ['company', 'department', 'inspection_cycle_days', 'estimated_duration_minutes']
    for key in meta_keys:
        if key not in meta:
            errors.append(f"metadata 缺少: {key}")

    # sections
    sections = template_json.get('sections', [])
    if not sections:
        errors.append("sections 為空")

    for i, section in enumerate(sections):
        section_keys = ['section_id', 'section_title', 'section_order', 'fields']
        for key in section_keys:
            if key not in section:
                errors.append(f"section[{i}] 缺少: {key}")

        for j, field in enumerate(section.get('fields', [])):
            field_keys = ['field_id', 'field_type', 'label']
            for key in field_keys:
                if key not in field:
                    errors.append(f"section[{i}].fields[{j}] 缺少: {key}")

    if errors:
        print("❌ 發現問題:")
        for e in errors:
            print(f"  • {e}")
    else:
        print("✅ 模板 JSON 格式驗證通過!")

    return len(errors) == 0


async def main():
    print("🔧 動態模板建立功能測試")
    print("（注意：無 Gemini API key，AI 轉換會走 fallback 路徑）\n")

    # 測試 Excel
    excel_result = await test_excel_template()

    # 測試 Word
    word_result = await test_word_template()

    # 驗證格式
    print("\n\n📋 驗證 Excel 模板格式:")
    excel_valid = await test_template_json_validity(excel_result['template'])

    print("\n📋 驗證 Word 模板格式:")
    word_valid = await test_template_json_validity(word_result['template'])

    print("\n" + "=" * 60)
    print("總結")
    print("=" * 60)
    print(f"Excel 模板: {'✅ 通過' if excel_valid else '❌ 失敗'}")
    print(f"Word 模板:  {'✅ 通過' if word_valid else '❌ 失敗'}")

    if excel_valid and word_valid:
        print("\n🎉 所有測試通過！動態模板建立功能正常運作。")
    else:
        print("\n⚠️ 部分測試未通過，需要修復。")


if __name__ == '__main__':
    asyncio.run(main())
