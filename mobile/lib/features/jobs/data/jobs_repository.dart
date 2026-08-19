import '../../../core/network/api_client.dart';
import '../models/job.dart';
import '../models/job_list.dart';

/// Filters + pagination for `/jobs/search`.
class JobSearchParams {
  const JobSearchParams({
    this.query = '',
    this.remote = false,
    this.salaryMin,
    this.salaryMax,
    this.experience,
    this.jobType,
    this.level,
    this.sort = 'relevance',
    this.page = 1,
    this.pageSize = 20,
  });

  final String query;
  final bool remote;
  final double? salaryMin;
  final double? salaryMax;
  final String? experience;
  final String? jobType;
  final String? level;
  final String sort;
  final int page;
  final int pageSize;

  Map<String, dynamic> toQuery() => {
        if (query.trim().isNotEmpty) 'query': query.trim(),
        if (remote) 'remote': 'true',
        if (salaryMin != null) 'salary_min': salaryMin,
        if (salaryMax != null) 'salary_max': salaryMax,
        if (experience != null && experience!.isNotEmpty)
          'experience': experience,
        if (jobType != null && jobType!.isNotEmpty) 'job_type': jobType,
        if (level != null && level!.isNotEmpty) 'level': level,
        'sort': sort,
        'page': page,
        'page_size': pageSize,
      };

  JobSearchParams copyWith({
    String? query,
    bool? remote,
    double? salaryMin,
    double? salaryMax,
    String? experience,
    String? jobType,
    String? level,
    String? sort,
    int? page,
    int? pageSize,
  }) =>
      JobSearchParams(
        query: query ?? this.query,
        remote: remote ?? this.remote,
        salaryMin: salaryMin ?? this.salaryMin,
        salaryMax: salaryMax ?? this.salaryMax,
        experience: experience ?? this.experience,
        jobType: jobType ?? this.jobType,
        level: level ?? this.level,
        sort: sort ?? this.sort,
        page: page ?? this.page,
        pageSize: pageSize ?? this.pageSize,
      );
}

class JobsRepository {
  JobsRepository(this._api);

  final ApiClient _api;

  Future<JobList> search(JobSearchParams params) async {
    final response = await _api.get<Map<String, dynamic>>(
      '/jobs/search',
      query: params.toQuery(),
    );
    return JobList.fromJson(response.data!);
  }

  Future<Job> jobById(String id) async {
    final response = await _api.get<Map<String, dynamic>>(
      '/jobs/details',
      query: {'id': id},
    );
    return Job.fromJson(response.data!);
  }

  Future<List<Job>> trending({int limit = 10}) async {
    final response = await _api.get<List<dynamic>>(
      '/jobs/trending',
      query: {'limit': limit},
    );
    return _parseJobs(response.data);
  }

  Future<List<Job>> recommended({int limit = 10}) async {
    final response = await _api.get<List<dynamic>>(
      '/jobs/recommended',
      query: {'limit': limit},
    );
    return _parseJobs(response.data);
  }

  Future<List<Job>> similar(String jobId, {int limit = 5}) async {
    final response = await _api.get<List<dynamic>>(
      '/jobs/$jobId/similar',
      query: {'limit': limit},
    );
    return _parseJobs(response.data);
  }

  Future<List<Job>> savedJobs() async {
    final response = await _api.get<Map<String, dynamic>>(
      '/users/me/saved-jobs',
    );
    final raw = response.data!;
    final items = raw['items'] ?? raw['jobs'] ?? raw['results'];
    if (items is List) {
      return items
          .whereType<Map<String, dynamic>>()
          .map(Job.fromJson)
          .toList();
    }
    return const [];
  }

  Future<void> saveJob(String jobId) async {
    await _api.post<dynamic>('/jobs/$jobId/save');
  }

  Future<void> unsaveJob(String jobId) async {
    await _api.delete<dynamic>('/jobs/$jobId/save');
  }

  List<Job> _parseJobs(dynamic raw) {
    if (raw is! List) return const [];
    final jobs = <Job>[];
    for (final e in raw) {
      if (e is Map<String, dynamic>) jobs.add(Job.fromJson(e));
    }
    return jobs;
  }
}