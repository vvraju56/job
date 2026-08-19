import '../../../core/network/api_client.dart';
import '../models/company.dart';

class CompaniesRepository {
  CompaniesRepository(this._api);

  final ApiClient _api;

  Future<Company> companyBySlug(String slug) async {
    final response = await _api.get<Map<String, dynamic>>('/companies/$slug');
    return Company.fromJson(response.data!);
  }

  Future<List<Company>> trendingCompanies({int limit = 10}) async {
    final response = await _api.get<dynamic>(
      '/companies/trending',
      query: {'limit': limit},
    );
    final list = <Company>[];
    final raw = response.data;
    dynamic items = raw;
    if (raw is Map<String, dynamic>) {
      items = raw['companies'] ?? raw['items'] ?? raw['results'];
    }
    if (items is List) {
      for (final e in items) {
        if (e is Map<String, dynamic>) list.add(Company.fromJson(e));
      }
    }
    return list;
  }
}