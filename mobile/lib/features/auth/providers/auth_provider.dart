import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import '../../../core/providers.dart';
import '../../../core/storage/token_storage.dart';
import '../data/auth_repository.dart';
import '../models/user.dart';

enum AuthStatus { unknown, unauthenticated, authenticated }

class AuthState {
  const AuthState({required this.status, this.user});

  final AuthStatus status;
  final User? user;

  AuthState copyWith({AuthStatus? status, User? user}) => AuthState(
        status: status ?? this.status,
        user: user ?? this.user,
      );
}

class AuthController extends StateNotifier<AuthState> {
  AuthController(this._repository, this._storage, this._api)
      : super(const AuthState(status: AuthStatus.unknown)) {
    _api.onLogout = _forceLogout;
  }

  final AuthRepository _repository;
  final TokenStorage _storage;
  final ApiClient _api;

  /// Restores a session on app start. Never throws.
  Future<void> loadSession() async {
    if (!await _storage.hasSession()) {
      state = const AuthState(status: AuthStatus.unauthenticated);
      return;
    }
    try {
      final user = await _repository.me();
      state = AuthState(status: AuthStatus.authenticated, user: user);
    } catch (_) {
      state = const AuthState(status: AuthStatus.unauthenticated);
    }
  }

  Future<void> login({required String email, required String password}) async {
    final tokens = await _repository.login(email: email, password: password);
    await _storage.saveTokens(
      access: tokens.accessToken,
      refresh: tokens.refreshToken,
    );
    final user = await _repository.me();
    state = AuthState(status: AuthStatus.authenticated, user: user);
  }

  Future<void> register({
    required String email,
    required String password,
    String? name,
  }) async {
    final tokens =
        await _repository.register(email: email, password: password, name: name);
    await _storage.saveTokens(
      access: tokens.accessToken,
      refresh: tokens.refreshToken,
    );
    final user = await _repository.me();
    state = AuthState(status: AuthStatus.authenticated, user: user);
  }

  Future<void> logout() async {
    await _storage.clear();
    _forceLogout();
  }

  void updateUser(User user) {
    state = AuthState(status: AuthStatus.authenticated, user: user);
  }

  Future<void> _forceLogout() async {
    await _storage.clear();
    state = const AuthState(status: AuthStatus.unauthenticated);
  }
}

final authProvider = StateNotifierProvider<AuthController, AuthState>((ref) {
  final api = ref.watch(apiClientProvider);
  return AuthController(
    AuthRepository(api),
    ref.watch(tokenStorageProvider),
    api,
  );
});

/// Onboarding has been completed (used by the router to pick the entry point).
class OnboardingController extends StateNotifier<bool> {
  OnboardingController(this._storage) : super(false) {
    _load();
  }

  final TokenStorage _storage;

  Future<void> _load() async {
    state = await _storage.isOnboardingDone();
  }

  Future<void> complete() async {
    await _storage.setOnboardingDone(true);
    state = true;
  }
}

final onboardingProvider =
    StateNotifierProvider<OnboardingController, bool>(
  (ref) => OnboardingController(ref.watch(tokenStorageProvider)),
);