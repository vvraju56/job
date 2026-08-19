import '../../../core/network/api_client.dart';
import '../models/application.dart';

class ApplicationsRepository {
  ApplicationsRepository(this._api);

  final ApiClient _api;

  Future<List<Application>> list() async {
    final response = await _api.get<Map<String, dynamic>>('/applications');
    final raw = response.data!;
    final items = raw['items'] ?? raw['applications'] ?? raw['results'];
    final list = <Application>[];
    if (items is List) {
      for (final e in items) {
        if (e is Map<String, dynamic>) list.add(Application.fromJson(e));
      }
    }
    return list;
  }

  Future<Application> create({
    required String jobId,
    String? notes,
  }) async {
    final response = await _api.post<Map<String, dynamic>>(
      '/applications',
      data: {'job_id': jobId, if (notes != null && notes.isNotEmpty) 'notes': notes},
    );
    return Application.fromJson(response.data!);
  }

  Future<Application> updateStatus(String id, ApplicationStatus status) async {
    final response = await _api.patch<Map<String, dynamic>>(
      '/applications/$id',
      data: {'status': status.name},
    );
    return Application.fromJson(response.data!);
  }
}