import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../../jobs/data/jobs_repository.dart';
import '../../jobs/models/job.dart';
import '../../jobs/providers/jobs_providers.dart';
import '../data/companies_repository.dart';
import '../models/company.dart';

final companiesRepositoryProvider = Provider<CompaniesRepository>(
  (ref) => CompaniesRepository(ref.watch(apiClientProvider)),
);

final companyProvider = FutureProvider.autoDispose.family<Company, String>(
  (ref, slug) => ref.watch(companiesRepositoryProvider).companyBySlug(slug),
);

final trendingCompaniesProvider =
    FutureProvider.autoDispose<List<Company>>(
  (ref) => ref.watch(companiesRepositoryProvider).trendingCompanies(),
);

/// Open positions for a company, derived from the job search endpoint.
final companyOpeningsProvider = FutureProvider.autoDispose.family<List<Job>, String>(
  (ref, slug) async {
    final company = await ref.watch(companyProvider(slug).future);
    final result = await ref
        .watch(jobsRepositoryProvider)
        .search(JobSearchParams(query: company.name, pageSize: 20));
    final name = company.name.toLowerCase();
    return result.items
        .where((j) =>
            (j.companyId != null && j.companyId == company.id) ||
            (j.companyName?.toLowerCase() == name))
        .toList();
  },
);