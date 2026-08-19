import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../data/jobs_repository.dart';
import '../models/job.dart';
import '../models/job_list.dart';

final jobsRepositoryProvider = Provider<JobsRepository>(
  (ref) => JobsRepository(ref.watch(apiClientProvider)),
);

final recommendedJobsProvider = FutureProvider.autoDispose<List<Job>>(
  (ref) => ref.watch(jobsRepositoryProvider).recommended(),
);

final trendingJobsProvider = FutureProvider.autoDispose<List<Job>>(
  (ref) => ref.watch(jobsRepositoryProvider).trending(),
);

final jobDetailsProvider = FutureProvider.autoDispose.family<Job, String>(
  (ref, jobId) => ref.watch(jobsRepositoryProvider).jobById(jobId),
);

final similarJobsProvider = FutureProvider.autoDispose.family<List<Job>, String>(
  (ref, jobId) => ref.watch(jobsRepositoryProvider).similar(jobId),
);

// Search ---------------------------------------------------------------------

class SearchState {
  const SearchState({
    this.params = const JobSearchParams(),
    this.result = const AsyncValue.loading(),
    this.loaded = false,
  });

  final JobSearchParams params;
  final AsyncValue<JobList> result;
  final bool loaded;

  SearchState copyWith({JobSearchParams? params, AsyncValue<JobList>? result, bool? loaded}) {
    return SearchState(
      params: params ?? this.params,
      result: result ?? this.result,
      loaded: loaded ?? this.loaded,
    );
  }
}

class SearchController extends StateNotifier<SearchState> {
  SearchController(this._repository) : super(const SearchState());

  final JobsRepository _repository;

  /// Runs a fresh search using the current filters (always page 1).
  Future<void> search() async {
    final params = state.params.copyWith(page: 1);
    state = state.copyWith(params: params, result: const AsyncValue.loading());
    try {
      final list = await _repository.search(params);
      state = state.copyWith(result: AsyncValue.data(list), loaded: true);
    } catch (error, stackTrace) {
      state = state.copyWith(
        result: AsyncValue.error(error, stackTrace),
        loaded: true,
      );
    }
  }

  Future<void> loadMore() async {
    final current = state.result.valueOrNull;
    if (current == null || !current.hasMore) return;
    final nextPage = state.params.page + 1;
    final params = state.params.copyWith(page: nextPage);
    try {
      final list = await _repository.search(params);
      state = state.copyWith(
        params: params,
        result: AsyncValue.data(
          JobList(
            items: [...current.items, ...list.items],
            total: list.total,
            page: list.page,
            pageSize: list.pageSize,
            totalPages: list.totalPages,
          ),
        ),
      );
    } catch (_) {
      // Ignore pagination failures; user can scroll/retry via the UI.
    }
  }

  void updateParams(JobSearchParams params) {
    state = state.copyWith(params: params);
  }

  void clear() {
    state = const SearchState();
  }
}

final searchControllerProvider =
    StateNotifierProvider<SearchController, SearchState>(
  (ref) => SearchController(ref.watch(jobsRepositoryProvider)),
);

// Saved jobs -----------------------------------------------------------------

class SavedJobsNotifier extends AsyncNotifier<List<Job>> {
  @override
  Future<List<Job>> build() {
    return ref.watch(jobsRepositoryProvider).savedJobs();
  }

  Future<void> toggle(Job job) async {
    final current = state.value ?? const <Job>[];
    final repo = ref.read(jobsRepositoryProvider);
    final exists = current.any((j) => j.id == job.id);
    try {
      if (exists) {
        state = AsyncValue.data(current.where((j) => j.id != job.id).toList());
        await repo.unsaveJob(job.id);
      } else {
        state = AsyncValue.data([job, ...current]);
        await repo.saveJob(job.id);
      }
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  bool isSaved(String jobId) {
    return (state.value ?? const <Job>[]).any((j) => j.id == jobId);
  }
}

final savedJobsProvider =
    AsyncNotifierProvider<SavedJobsNotifier, List<Job>>(SavedJobsNotifier.new);