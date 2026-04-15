import 'package:flutter/foundation.dart';
import 'package:geolocator/geolocator.dart';
import 'package:geocoding/geocoding.dart';

/// GPS 定位資料
class LocationData {
  final double latitude;
  final double longitude;
  final String? locationName;

  LocationData({
    required this.latitude,
    required this.longitude,
    this.locationName,
  });
}

/// 定位服務 — 一次性擷取當前位置
class LocationService {
  static final LocationService _instance = LocationService._internal();
  factory LocationService() => _instance;
  LocationService._internal();

  /// 取得當前 GPS 位置，失敗或被拒絕時回傳 null
  Future<LocationData?> getCurrentPosition() async {
    try {
      // 檢查定位服務是否開啟
      final serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        debugPrint('定位服務未開啟');
        return null;
      }

      // 檢查並請求權限
      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          debugPrint('定位權限被拒絕');
          return null;
        }
      }

      if (permission == LocationPermission.deniedForever) {
        debugPrint('定位權限被永久拒絕');
        return null;
      }

      // 取得位置（10 秒超時）
      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.medium,
        timeLimit: const Duration(seconds: 10),
      );

      // Issue #19: Web 平台不支援 geocoding，跳過反向地理編碼
      String? locationName;
      if (!kIsWeb) {
        try {
          final placemarks = await placemarkFromCoordinates(
            position.latitude,
            position.longitude,
          );
          if (placemarks.isNotEmpty) {
            final p = placemarks.first;
            // 組合地址：區域 + 街道
            final parts = [p.subAdministrativeArea, p.locality, p.street]
                .where((s) => s != null && s.isNotEmpty)
                .toList();
            locationName = parts.join(' ');
          }
        } catch (e) {
          debugPrint('反向地理編碼失敗: $e');
        }
      }

      return LocationData(
        latitude: position.latitude,
        longitude: position.longitude,
        locationName: locationName,
      );
    } catch (e) {
      debugPrint('取得位置失敗: $e');
      return null;
    }
  }
}
