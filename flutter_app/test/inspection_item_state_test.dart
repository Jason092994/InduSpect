import 'package:flutter_test/flutter_test.dart';
import 'package:induspect_ai/screens/form_inspection_screen.dart';

/// 測試 InspectionItemState 的 computed properties 和 controller 管理
void main() {
  group('InspectionItemState', () {
    test('displayValue 回傳 AI condition_assessment（正常時）', () {
      final item = InspectionItemState(
        fieldId: 'f1',
        label: '絕緣電阻',
        fieldType: 'number',
        aiResult: {
          'condition_assessment': '正常',
          'is_anomaly': false,
        },
      );

      expect(item.displayValue, '正常');
    });

    test('displayValue 回傳異常描述', () {
      final item = InspectionItemState(
        fieldId: 'f2',
        label: '溫度',
        fieldType: 'number',
        aiResult: {
          'condition_assessment': '過熱',
          'is_anomaly': true,
          'anomaly_description': '溫度超過 85°C',
        },
      );

      expect(item.displayValue, contains('異常'));
      expect(item.displayValue, contains('溫度超過 85°C'));
    });

    test('displayValue 無 AI 結果時回傳 manualValue', () {
      final item = InspectionItemState(
        fieldId: 'f3',
        label: '外觀',
        fieldType: 'text',
        manualValue: '外觀完好',
      );

      expect(item.displayValue, '外觀完好');
    });

    test('displayValue 無任何值時回傳 null', () {
      final item = InspectionItemState(
        fieldId: 'f4',
        label: '備註',
        fieldType: 'text',
      );

      expect(item.displayValue, isNull);
    });

    test('verdict: AI 異常 → 不合格', () {
      final item = InspectionItemState(
        fieldId: 'f5',
        label: '接地',
        fieldType: 'radio',
        aiResult: {'is_anomaly': true},
      );

      expect(item.verdict, '不合格');
    });

    test('verdict: AI 正常 → 合格', () {
      final item = InspectionItemState(
        fieldId: 'f6',
        label: '接地',
        fieldType: 'radio',
        aiResult: {'is_anomaly': false},
      );

      expect(item.verdict, '合格');
    });

    test('verdict: 手動填寫 → 已填寫', () {
      final item = InspectionItemState(
        fieldId: 'f7',
        label: '備註',
        fieldType: 'text',
        manualValue: '正常',
      );

      expect(item.verdict, '已填寫');
    });

    test('verdict: 未填寫 → 未檢測', () {
      final item = InspectionItemState(
        fieldId: 'f8',
        label: '備註',
        fieldType: 'text',
      );

      expect(item.verdict, '未檢測');
    });

    test('manualController 初始值與建構參數一致', () {
      final item = InspectionItemState(
        fieldId: 'ctrl1',
        label: 'Test',
        fieldType: 'text',
        manualValue: '初始值',
      );

      expect(item.manualController.text, '初始值');
      // 清理
      item.manualController.dispose();
    });

    test('manualController 無初始值時為空字串', () {
      final item = InspectionItemState(
        fieldId: 'ctrl2',
        label: 'Test',
        fieldType: 'text',
      );

      expect(item.manualController.text, '');
      item.manualController.dispose();
    });

    test('isCompleted 預設為 false', () {
      final item = InspectionItemState(
        fieldId: 'new',
        label: 'New',
        fieldType: 'text',
      );

      expect(item.isCompleted, false);
      expect(item.isAnalyzing, false);
      item.manualController.dispose();
    });
  });
}
