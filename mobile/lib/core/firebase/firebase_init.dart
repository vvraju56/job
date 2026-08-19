import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/foundation.dart';

/// Initializes Firebase without hard-coded options.
///
/// When `flutterfire configure` has been run, `google-services.json` /
/// `GoogleService-Info.plist` are embedded natively and `Firebase.initializeApp()`
/// picks them up automatically. If Firebase has not been configured yet, this
/// fails gracefully so the rest of the app still runs (notifications disabled).
Future<void> initializeFirebase() async {
  try {
    await Firebase.initializeApp();
  } catch (e) {
    debugPrint('[MakeableJobs] Firebase not configured, skipping: $e');
  }
}