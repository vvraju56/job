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
    final response = await _api.get<List<dynamic>>(
      '/companies/trending',
      query: {'limit': limit},
    );
    final list = <Company>[];
    final raw = response.data;
    if (raw is List) {
      for (final e in raw) {
        if (e is Map<String, dynamic>) list.add(Company.fromJson(e));
      }
    }
    return list;
  }
}