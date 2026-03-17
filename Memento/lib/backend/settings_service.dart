import 'package:shared_preferences/shared_preferences.dart';

class SettingsService {
  static Future<void> saveSettings({
    required bool enableVibration,
    required int timeoutSeconds,
    required bool appTalkReminder,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('enable_vibration', enableVibration);
    await prefs.setInt('timeout_seconds', timeoutSeconds);
    await prefs.setBool('app_talk_reminder', appTalkReminder);
  }

  static Future<Map<String, dynamic>> loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    return {
      'enable_vibration': prefs.getBool('enable_vibration') ?? true,
      'timeout_seconds': prefs.getInt('timeout_seconds') ?? 10,
      'app_talk_reminder': prefs.getBool('app_talk_reminder') ?? true,
      'snooze_minutes': prefs.getInt('snooze_minutes') ?? 5,
    };
  }
}
