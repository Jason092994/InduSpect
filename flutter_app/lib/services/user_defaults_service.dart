import 'package:shared_preferences/shared_preferences.dart';

/// 使用者預設值記憶服務
///
/// Sprint 4 Task 4.2: 記住常用資訊，加速定檢流程
/// 使用 SharedPreferences 本地儲存:
/// - 檢查人員姓名
/// - 最近使用的設備清單
/// - 最近使用的位置
class UserDefaultsService {
  static const String _keyInspectorName = 'user_inspector_name';
  static const String _keyRecentEquipments = 'user_recent_equipments';
  static const String _keyRecentLocation = 'user_recent_location';
  static const int _maxRecentEquipments = 10;

  /// 儲存使用者預設值
  Future<void> saveDefaults({
    String? inspectorName,
    String? recentLocation,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    if (inspectorName != null) {
      await prefs.setString(_keyInspectorName, inspectorName);
    }
    if (recentLocation != null) {
      await prefs.setString(_keyRecentLocation, recentLocation);
    }
  }

  /// 載入使用者預設值
  ///
  /// 回傳 Map 包含:
  /// - inspectorName: 檢查人員姓名
  /// - recentLocation: 最近使用位置
  Future<Map<String, String>> loadDefaults() async {
    final prefs = await SharedPreferences.getInstance();
    return {
      'inspectorName': prefs.getString(_keyInspectorName) ?? '',
      'recentLocation': prefs.getString(_keyRecentLocation) ?? '',
    };
  }

  /// 新增最近使用的設備（自動去重，保留最近 N 筆）
  Future<void> addRecentEquipment(String equipmentId) async {
    if (equipmentId.isEmpty) return;

    final prefs = await SharedPreferences.getInstance();
    List<String> recents =
        prefs.getStringList(_keyRecentEquipments) ?? [];

    // 移除重複（如果已存在，先移除再加到最前面）
    recents.remove(equipmentId);
    recents.insert(0, equipmentId);

    // 限制最大數量
    if (recents.length > _maxRecentEquipments) {
      recents = recents.sublist(0, _maxRecentEquipments);
    }

    await prefs.setStringList(_keyRecentEquipments, recents);
  }

  /// 取得最近使用的設備清單
  Future<List<String>> getRecentEquipments() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getStringList(_keyRecentEquipments) ?? [];
  }

  /// 清除所有使用者預設值
  Future<void> clearDefaults() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_keyInspectorName);
    await prefs.remove(_keyRecentEquipments);
    await prefs.remove(_keyRecentLocation);
  }
}
