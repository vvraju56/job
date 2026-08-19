import 'job.dart';

/// Paginated job search result (`/jobs/search`).
class JobList {
  const JobList({
    required this.items,
    required this.total,
    required this.page,
    required this.pageSize,
    required this.totalPages,
  });

  final List<Job> items;
  final int total;
  final int page;
  final int pageSize;
  final int totalPages;

  bool get hasMore => page < totalPages;

  factory JobList.fromJson(Map<String, dynamic> json) {
    final raw = json['items'] ?? json['jobs'] ?? json['results'];
    final items = <Job>[];
    if (raw is List) {
      for (final e in raw) {
        if (e is Map<String, dynamic>) items.add(Job.fromJson(e));
      }
    }
    return JobList(
      items: items,
      total: (json['total'] as num?)?.toInt() ?? items.length,
      page: (json['page'] as num?)?.toInt() ?? 1,
      pageSize: (json['page_size'] as num?)?.toInt() ?? items.length,
      totalPages: (json['total_pages'] as num?)?.toInt() ?? 1,
    );
  }
}