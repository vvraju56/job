import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/async_value_view.dart';
import '../providers/jobs_providers.dart';
import 'widgets/job_card.dart';

class SavedScreen extends ConsumerWidget {
  const SavedScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final saved = ref.watch(savedJobsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Saved Jobs'),
        actions: [
          IconButton(
            onPressed: () => ref.invalidate(savedJobsProvider),
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: AsyncValueView(
        value: saved,
        isEmpty: (jobs) => jobs.isEmpty,
        emptyMessage: 'No saved jobs yet — tap the bookmark on any job',
        onRefresh: () => ref.refresh(savedJobsProvider.future),
        builder: (context, jobs) => RefreshIndicator(
          onRefresh: () => ref.refresh(savedJobsProvider.future),
          child: ListView.separated(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
            itemCount: jobs.length,
            separatorBuilder: (_, __) => const SizedBox(height: 4),
            itemBuilder: (context, i) => JobCard(job: jobs[i]),
          ),
        ),
      ),
    );
  }
}