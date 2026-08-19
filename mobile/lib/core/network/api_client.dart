import 'package:dio/dio.dart';

import '../storage/token_storage.dart';

/// Base URL for the Makeable Jobs API. Override at build time with:
///   flutter run --dart-define=API_BASE_URL=https://api.example.com/api/v1
const String kApiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://localhost:8000/api/v1',
);

/// Dio wrapper that:
///  - attaches the Bearer access token to every request,
///  - transparently refreshes the token once when a request returns 401,
///  - clears the session (via [onLogout]) when refresh fails.
class ApiClient {
  ApiClient({required TokenStorage tokenStorage})
      : _tokenStorage = tokenStorage {
    final baseOptions = BaseOptions(
      baseUrl: kApiBaseUrl,
      connectTimeout: const Duration(seconds: 20),
      receiveTimeout: const Duration(seconds: 30),
      sendTimeout: const Duration(seconds: 30),
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    );

    dio = Dio(baseOptions);
    _refreshDio = Dio(baseOptions);

    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _tokenStorage.readAccessToken();
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) async {
          final status = error.response?.statusCode;
          final retried = error.requestOptions.extra['_retried'] == true;
          final isAuthPath = error.requestOptions.path.contains('/auth/login') ||
              error.requestOptions.path.contains('/auth/register') ||
              error.requestOptions.path.contains('/auth/refresh');

          if (status == 401 && !retried && !isAuthPath) {
            error.requestOptions.extra['_retried'] = true;
            final refreshed = await _tryRefresh();
            if (refreshed) {
              final token = await _tokenStorage.readAccessToken();
              if (token != null) {
                error.requestOptions.headers['Authorization'] = 'Bearer $token';
              }
              try {
                final response = await _refreshDio.fetch(error.requestOptions);
                handler.resolve(response);
                return;
              } on DioException catch (retryError) {
                handler.next(retryError);
                return;
              }
            }
            onLogout?.call();
          }
          handler.next(error);
        },
      ),
    );
  }

  late final Dio dio;
  late final Dio _refreshDio;
  final TokenStorage _tokenStorage;

  /// Invoked when the session can no longer be refreshed (401 + failed
  /// refresh). Wired to the auth controller so the app logs out.
  void Function()? onLogout;

  Future<bool> _tryRefresh() async {
    final refreshToken = await _tokenStorage.readRefreshToken();
    if (refreshToken == null || refreshToken.isEmpty) return false;
    try {
      final response = await _refreshDio.post(
        '/auth/refresh',
        data: {'refresh_token': refreshToken},
      );
      final data = response.data as Map<String, dynamic>;
      final access = data['access_token'] as String;
      final refresh = (data['refresh_token'] as String?) ?? refreshToken;
      await _tokenStorage.saveTokens(access: access, refresh: refresh);
      return true;
    } catch (_) {
      await _tokenStorage.clear();
      return false;
    }
  }

  // Convenience helpers ------------------------------------------------------

  Future<Response<T>> get<T>(String path, {Map<String, dynamic>? query}) {
    return dio.get<T>(path, queryParameters: query);
  }

  Future<Response<T>> post<T>(String path, {Object? data}) {
    return dio.post<T>(path, data: data);
  }

  Future<Response<T>> patch<T>(String path, {Object? data}) {
    return dio.patch<T>(path, data: data);
  }

  Future<Response<T>> delete<T>(String path, {Object? data}) {
    return dio.delete<T>(path, data: data);
  }
}