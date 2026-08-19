import 'package:shared_preferences/shared_preferences.dart';

/// Thin wrapper around SharedPreferences for access/refresh tokens and a few
/// client-side flags (onboarding completed).
class TokenStorage {
  static const String _kAccessToken = 'makeable_access_token';
  static const String _kRefreshToken = 'makeable_refresh_token';
  static const String _kOnboardingDone = 'makeable_onboarding_done';

  Future<SharedPreferences> get _prefs => SharedPreferences.getInstance();

  Future<String?> readAccessToken() async {
    final prefs = await _prefs;
    return prefs.getString(_kAccessToken);
  }

  Future<String?> readRefreshToken() async {
    final prefs = await _prefs;
    return prefs.getString(_kRefreshToken);
  }

  Future<void> saveTokens({required String access, required String refresh}) async {
    final prefs = await _prefs;
    await prefs.setString(_kAccessToken, access);
    await prefs.setString(_kRefreshToken, refresh);
  }

  Future<bool> hasSession() async {
    final access = await readAccessToken();
    return access != null && access.isNotEmpty;
  }

  Future<bool> isOnboardingDone() async {
    final prefs = await _prefs;
    return prefs.getBool(_kOnboardingDone) ?? false;
  }

  Future<void> setOnboardingDone(bool done) async {
    final prefs = await _prefs;
    await prefs.setBool(_kOnboardingDone, done);
  }

  Future<void> clear() async {
    final prefs = await _prefs;
    await prefs.remove(_kAccessToken);
    await prefs.remove(_kRefreshToken);
  }
}