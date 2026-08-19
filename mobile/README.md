# Makeable Jobs — Mobile

> One Search. Every Opportunity.

Flutter client for the Makeable Jobs aggregation platform. Dark, glassmorphism-first
UI against the Makeable API at `http://localhost:8000/api/v1`.

## Stack

- **Flutter** (Dart SDK `^3.5.0`, Flutter stable)
- **flutter_riverpod** — state management
- **go_router** — navigation incl. a `StatefulShellRoute.indexedStack` bottom-nav shell
- **dio** — networking with a bearer-token interceptor + refresh-on-401
- **shared_preferences** — access/refresh token storage
- **firebase_core + firebase_messaging** — push notifications (FCM)
- **cached_network_image** — image caching
- **google_fonts** — typography (bundled default fallback in `AppTheme`)
- **url_launcher** — “Apply on Original Website” external deep links

## Requirements

- Flutter stable, Dart `>=3.5.0 <4.0.0`
- Android: minSdk **23**, applicationId `com.makeable.jobs`
- iOS: 12.0+, CocoaPods

## Running the app

```bash
cd mobile
flutter pub get
flutter run
```

The API base URL defaults to `http://localhost:8000/api/v1`. Override it at
build/run time:

```bash
flutter run --dart-define=API_BASE_URL=https://api.makeablejobs.com/api/v1
flutter build apk --dart-define=API_BASE_URL=https://api.makeablejobs.com/api/v1
```

> Android emulator: the host machine is reachable at `10.0.2.2`, so use
> `--dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1`. iOS simulator can use
> `localhost` directly.

## Firebase / push notifications setup

The app calls `Firebase.initializeApp()` using generated options. Because the
`firebase_options.dart` file is machine-specific and cannot be committed, you must
generate it yourself once:

1. Create a Firebase project at <https://console.firebase.google.com>.
2. Add an Android app with package name `com.makeable.jobs` and an iOS app with
   bundle id `com.makeable.jobs`.
3. Install the FlutterFire CLI:
   ```bash
   dart pub global activate flutterfire_cli
   ```
4. From the `mobile/` directory, generate options:
   ```bash
   flutterfire configure --project=<your-project-id>
   ```
   This writes `lib/firebase_options.dart` plus the platform config files
   (`android/app/google-services.json`, `ios/Runner/GoogleService-Info.plist`).
5. (Android only) ensure the Google Services Gradle plugin is enabled — see
   `android/settings.gradle` and `android/app/build.gradle`.

Until step 4 is done, notifications are disabled but the rest of the app works.
`FcmService` fails gracefully when Firebase is not configured.

## Builds

### Debug APK

```bash
flutter run
```

### Release APK / AAB

```bash
flutter build apk --release
flutter build appbundle --release        # Play Store
```

Sign the release build with your own `keystore.jks` and wire it into
`android/app/build.gradle` (see the commented block) — the checked-in config uses
the debug signing key so `flutter run` works out of the box.

### iOS / App Store

```bash
flutter build ios --release
open ios/Runner.xcworkspace
```

In Xcode: set the team, bundle id `com.makeable.jobs`, enable Push Notifications +
Background Modes (remote notifications), then Archive → Upload to App Store
Connect.

## Architecture

```
lib/
  main.dart                          # ProviderScope + Firebase init
  app.dart                           # MaterialApp.router + theme
  core/
    theme/app_theme.dart             # dark brand theme + GlassCard
    router/app_router.dart           # GoRouter + StatefulShellRoute
    network/api_client.dart          # Dio + auth interceptor
    storage/token_storage.dart       # SharedPreferences token persistence
  features/
    auth/        (provider, repository, splash/onboarding/login/register)
    jobs/        (models, data, providers, home/search/details/saved)
    companies/   (models, data, company details)
    notifications/(screen, provider, FCM service)
    profile/     (profile + settings)
    applications/(models, data, tracking screen)
```

## API contract

- Auth: `POST /auth/login`, `POST /auth/register`, `POST /auth/refresh`,
  `GET /auth/me`
- Jobs: `GET /jobs/search`, `GET /jobs/{id}`, `GET /jobs/trending`,
  `GET /jobs/recommended`, `GET /jobs/similar`, `POST/DELETE /jobs/{id}/save`
- Companies: `GET /companies/{slug}`
- Saved jobs: `GET /users/me/saved-jobs`
- Notifications: `GET /notifications`, `POST /notifications/{id}/read`,
  `POST /notifications/device-token`
- Applications: `GET /applications`, `POST /applications`, `PATCH /applications/{id}`