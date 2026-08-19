import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';

import '../../../core/network/api_client.dart';

/// Top-level background handler. Must not be a closure and must be annotated
/// so the Dart AOT compiler keeps it alive for FCM background delivery.
@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  debugPrint('[MakeableJobs] background message: ${message.messageId}');
}

/// Wraps FirebaseMessaging: permission request, token registration with the
/// backend, and foreground/background/opened handlers. Fails gracefully when
/// Firebase has not been configured (firebase_options / google-services.json
/// missing).
class FcmService {
  FcmService(this._api);

  final ApiClient _api;

  Future<void> initialize() async {
    try {
      final messaging = FirebaseMessaging.instance;

      FirebaseMessaging.onBackgroundMessage(
        firebaseMessagingBackgroundHandler,
      );

      final settings = await messaging.requestPermission(
        alert: true,
        badge: true,
        sound: true,
        provisional: true,
      );
      final allowed = settings.authorizationStatus ==
              AuthorizationStatus.authorized ||
          settings.authorizationStatus == AuthorizationStatus.provisional;

      if (allowed) {
        final token = await messaging.getToken();
        if (token != null && token.isNotEmpty) {
          await _registerToken(token);
        }
      }

      messaging.onTokenRefresh.listen((token) {
        _registerToken(token);
      });

      FirebaseMessaging.onMessage.listen((message) {
        debugPrint('[MakeableJobs] foreground message: ${message.messageId}');
      });

      FirebaseMessaging.onMessageOpenedApp.listen((message) {
        _handleOpened(message);
      });

      final initial = await messaging.getInitialMessage();
      if (initial != null) {
        _handleOpened(initial);
      }
    } catch (e) {
      debugPrint('[MakeableJobs] FCM unavailable, skipping setup: $e');
    }
  }

  Future<void> _registerToken(String token) async {
    try {
      await _api.post('/notifications/device-token', data: {'token': token});
    } catch (e) {
      debugPrint('[MakeableJobs] device token registration failed: $e');
    }
  }

  void _handleOpened(RemoteMessage message) {
    final payload = message.data;
    final jobId = payload['job_id'] ?? payload['job'];
    if (jobId != null && jobId.toString().isNotEmpty) {
      debugPrint('[MakeableJobs] opened notification for job $jobId');
      // Navigation from a notification is handled by the router when the app
      // regains focus; the deep link is exposed via the notification payload.
    }
  }
}