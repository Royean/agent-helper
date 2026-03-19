class Device {
  final String deviceId;
  final String deviceName;
  final String platform;
  final bool isOnline;
  final String? pairingKey;
  final DateTime? connectedAt;
  final DateTime? lastPing;

  Device({
    required this.deviceId,
    required this.deviceName,
    required this.platform,
    this.isOnline = false,
    this.pairingKey,
    this.connectedAt,
    this.lastPing,
  });

  factory Device.fromJson(Map<String, dynamic> json) {
    return Device(
      deviceId: json['device_id'] ?? '',
      deviceName: json['device_name'] ?? '',
      platform: json['platform'] ?? '',
      isOnline: json['is_online'] ?? false,
      pairingKey: json['pairing_key'],
      connectedAt: json['connected_at'] != null 
          ? DateTime.fromMillisecondsSinceEpoch((json['connected_at'] as num).toInt() * 1000) 
          : null,
      lastPing: json['last_ping'] != null 
          ? DateTime.fromMillisecondsSinceEpoch((json['last_ping'] as num).toInt() * 1000) 
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'device_id': deviceId,
      'device_name': deviceName,
      'platform': platform,
      'is_online': isOnline,
      'pairing_key': pairingKey,
      'connected_at': connectedAt?.millisecondsSinceEpoch ~/ 1000,
      'last_ping': lastPing?.millisecondsSinceEpoch ~/ 1000,
    };
  }

  String get platformIcon {
    switch (platform.toLowerCase()) {
      case 'darwin':
        return '🍎';
      case 'linux':
        return '🐧';
      case 'windows':
        return '🪟';
      default:
        return '📱';
    }
  }
}
