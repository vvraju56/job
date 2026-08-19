import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import '../../../core/providers.dart';
import '../services/fcm_service.dart';

/// A push/in-app notification item from `/notifications`.
class AppNotification {
  const AppNotification({
    required this.id,
    required this.title,
    required this.body,
    this.jobId,
    this.type,
    this.read = false,
    this.createdAt,
  });

  final String id;
  final String title;
  final String body;
  final String? jobId;
  final String? type;
  final bool read;
  final DateTime? createdAt;

  factory AppNotification.fromJson(Map<String, dynamic> json) {
    String? str(String key) {
      final v = json[key];
      return v == null ? null : v.toString();
    }

    bool boolV(String key) {
      final v = json[key];
      if (v is bool) return v;
      return v?.toString().toLowerCase() == 'true';
    }

    return AppNotification(
      id: json['id'].toString(),
      title: str('title') ?? 'Notification',
      body: str('body') ?? str('message') ?? '',
      jobId: str('job_id') ?? str('job'),
      type: str('type'),
      read: boolV('read'),
      createdAt: DateTime.tryParse(str('created_at') ?? ''),
    );
  }
}

class NotificationsRepository {
  NotificationsRepository(this._api);

  final ApiClient _api;

  Future<List<AppNotification>> list() async {
    final response = await _api.get<dynamic>('/notifications');
    final raw = response.data;
    final items =
        raw is Map<String, dynamic>
        ? raw['items'] ?? raw['notifications'] ?? raw['results'] ?? raw
        : raw;
    final list = <AppNotification>[];
    if (items is List) {
      for (final e in items) {
        if (e is Map<String, dynamic>) list.add(AppNotification.fromJson(e));
      }
    }
    return list;
  }

  Future<void> markRead(String id) async {
    await _api.post<dynamic>('/notifications/$id/read');
  }

  Future<void> markAllRead() async {
    await _api.post<dynamic>('/notifications/read-all');
  }

  Future<void> registerDeviceToken(String token) async {
    await _api.post<dynamic>('/notifications/device-token', data: {'token': token});
  }
}

class NotificationsNotifier extends AsyncNotifier<List<AppNotification>> {
  @override
  Future<List<AppNotification>> build() {
    return ref.read(notificationsRepositoryProvider).list();
  }

  Future<void> markRead(String id) async {
    final repo = ref.read(notificationsRepositoryProvider);
    final current = state.value ?? const <AppNotification>[];
    state = AsyncValue.data([
      for (final n in current)
        if (n.id == id) AppNotification(id: n.id, title: n.title, body: n.body, jobId: n.jobId, type: n.type, read: true, createdAt: n.createdAt)
        else n,
    ]);
    try {
      await repo.markRead(id);
    } catch (_) {
      // Keep the local optimistic update even if the network call failed.
    }
  }

  Future<void> markAllRead() async {
    final current = state.value ?? const <AppNotification>[];
    state = AsyncValue.data([
      for (final n in current)
        AppNotification(id: n.id, title: n.title, body: n.body, jobId: n.jobId, type: n.type, read: true, createdAt: n.createdAt),
    ]);
    try {
      await ref.read(notificationsRepositoryProvider).markAllRead();
    } catch (_) {}
  }
}

final notificationsRepositoryProvider =
    Provider<NotificationsRepository>((ref) {
  return NotificationsRepository(ref.watch(apiClientProvider));
});

final fcmServiceProvider = Provider<FcmService>(
  (ref) => FcmService(ref.watch(apiClientProvider)),
);

final notificationsProvider =
    AsyncNotifierProvider<NotificationsNotifier, List<AppNotification>>(
  NotificationsNotifier.new,
);

final unreadNotificationsProvider =
    Provider<int>((ref) => ref.watch(notificationsProvider).maybeWhen(
          data: (items) => items.where((n) => !n.read).length,
          orElse: () => 0,
        ));