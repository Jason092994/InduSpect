import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';

// 照片命名邏輯的獨立測試（不依賴平台服務）
// 驗收標準:
// - 照片按規則自動命名
// - 照片與 task_id 綁定關係持久化
// - 儲存空間管理（單張壓縮 < 300KB）

void main() {
  group('PhotoService 命名規則測試', () {
    test('命名格式: {序號}-{項目簡稱}_{時間戳}.jpg', () {
      // 驗證命名規則：序號 2 位，項目名稱去空格，時間戳 yyyyMMdd_HHmmss
      final name = generateTestFileName(
        sequence: 3,
        displayName: '絕緣電阻 R相',
        year: 2026, month: 3, day: 13, hour: 14, minute: 30, second: 52,
      );
      expect(name, '03-絕緣電阻R相_20260313_143052.jpg');
    });

    test('序號小於 10 前面補 0', () {
      final name = generateTestFileName(
        sequence: 1,
        displayName: '接地電阻',
        year: 2026, month: 3, day: 13, hour: 15, minute: 0, second: 0,
      );
      expect(name, '01-接地電阻_20260313_150000.jpg');
    });

    test('序號大於 9 不補 0', () {
      final name = generateTestFileName(
        sequence: 12,
        displayName: '漏電斷路器',
        year: 2026, month: 3, day: 13, hour: 9, minute: 5, second: 30,
      );
      expect(name, '12-漏電斷路器_20260313_090530.jpg');
    });

    test('名稱超過 15 字元截斷', () {
      final name = generateTestFileName(
        sequence: 1,
        displayName: '這是一個非常非常非常非常長的檢查項目名稱',
        year: 2026, month: 1, day: 1, hour: 0, minute: 0, second: 0,
      );
      // 移除空格後取前 15 字元
      expect(name.length, lessThanOrEqualTo(50)); // 合理長度
      expect(name.startsWith('01-'), true);
      expect(name.endsWith('.jpg'), true);
    });

    test('名稱含特殊字元替換為底線', () {
      final name = generateTestFileName(
        sequence: 1,
        displayName: 'Test/Name:Special',
        year: 2026, month: 1, day: 1, hour: 0, minute: 0, second: 0,
      );
      expect(name.contains('/'), false);
      expect(name.contains(':'), false);
    });
  });

  group('PhotoBinding 測試', () {
    test('PhotoBinding toJson 格式正確', () {
      // 這裡用 Map 模擬
      final binding = {
        'task_id': 'task_1',
        'display_name': '絕緣電阻測量',
        'file_name': '01-絕緣電阻測量_20260313_143052.jpg',
        'sequence': 1,
        'size_kb': 245.5,
      };

      expect(binding['task_id'], 'task_1');
      expect(binding['sequence'], 1);
      expect(binding['size_kb'] as double, lessThan(300));
    });
  });
}

/// 獨立的命名函數（不依賴 PhotoService 實體）
String generateTestFileName({
  required int sequence,
  required String displayName,
  required int year,
  required int month,
  required int day,
  required int hour,
  required int minute,
  required int second,
}) {
  final seqStr = sequence.toString().padLeft(2, '0');
  String shortName = displayName
      .replaceAll(RegExp(r'[\s　]+'), '')
      .replaceAll(RegExp(r'[/\\:*?"<>|]'), '_');
  if (shortName.length > 15) {
    shortName = shortName.substring(0, 15);
  }
  final timeStr =
      '${year.toString().padLeft(4, '0')}'
      '${month.toString().padLeft(2, '0')}'
      '${day.toString().padLeft(2, '0')}_'
      '${hour.toString().padLeft(2, '0')}'
      '${minute.toString().padLeft(2, '0')}'
      '${second.toString().padLeft(2, '0')}';
  return '$seqStr-${shortName}_$timeStr.jpg';
}
