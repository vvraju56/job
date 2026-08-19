import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import '../../../core/providers.dart';
import '../data/applications_repository.dart';
import '../models/application.dart';

final applicationsRepositoryProvider = Provider<ApplicationsRepository>(
  (ref) => ApplicationsRepository(ref.watch(apiClientProvider)),
);

class ApplicationsNotifier extends AsyncNotifier<List<Application>> {
  @override
  Future<List<Application>> build() {
    return ref.watch(applicationsRepositoryProvider).list();
  }

  Future<void> updateStatus(String id, ApplicationStatus status) async {
    final current = state.value ?? const <Application>[];
    final repo = ref.read(applicationsRepositoryProvider);
    try {
      state = AsyncValue.data([
        for (final app in current)
          if (app.id == id)
            Application(
              id: app.id,
              jobId: app.jobId,
              jobTitle: app.jobTitle,
              companyName: app.companyName,
              companyLogo: app.companyLogo,
              status: status,
              notes: app.notes,
              appliedAt: app.appliedAt,
            )
          else
            app,
      ]);
      await repo.updateStatus(id, status);
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }
}

final applicationsProvider =
    AsyncNotifierProvider<ApplicationsNotifier, List<Application>>(
  ApplicationsNotifier.new,
);