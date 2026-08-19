import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/async_value_view.dart';
import '../../../core/widgets/glass_card.dart';
import '../../../core/widgets/logo_image.dart';
import '../models/job.dart';
import '../providers/jobs_providers.dart';
import 'widgets/job_card.dart';

class JobDetailsScreen extends ConsumerWidget {
  const JobDetailsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final id = GoRouterState.of(context).pathParameters['id'] ?? '';
    final extra = GoRouterState.of(context).extra as Job?;

    final details = ref.watch(jobDetailsProvider(id));
    final similar = ref.watch(similarJobsProvider(id));
    final saved = ref.watch(savedJobsProvider).maybeWhen(
          data: (items) => items.any((j) => j.id == id),
          orElse: () => false,
        );

    return Scaffold(
      appBar: AppBar(
        title: const Text('Job Details'),
        actions: [
          IconButton(
            onPressed: () => extra != null
                ? ref.read(savedJobsProvider.notifier).toggle(extra)
                : null,
            icon: Icon(
              saved ? Icons.bookmark_rounded : Icons.bookmark_border_rounded,
              color: saved ? AppColors.warning : AppColors.text,
            ),
          ),
        ],
      ),
      bottomNavigationBar: details.when(
        loading: () => null,
        error: (_, __) => null,
        data: (job) => _ApplyBar(job: job),
      ),
      body: AsyncValueView(
        value: details,
        isEmpty: (job) => job.id.isEmpty,
        emptyMessage: 'Job not found',
        onRefresh: () => ref.refresh(jobDetailsProvider(id).future),
        builder: (context, job) {
          final preview = extra ?? job;
          return ListView(
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
            children: [
              _Header(job: preview),
              const SizedBox(height: 16),
              _Highlights(job: preview),
              const SizedBox(height: 16),
              if (preview.skills.isNotEmpty) ...[
                _Section(title: 'Skills required', child: _SkillChips(skills: preview.skills)),
                const SizedBox(height: 16),
              ],
              _Section(
                title: 'About this role',
                child: Text(
                  job.description.isEmpty ? preview.description : job.description,
                  style: const TextStyle(
                    color: AppColors.text,
                    fontSize: 14.5,
                    height: 1.6,
                  ),
                ),
              ),
              const SizedBox(height: 16),
              _Section(
                title: 'Source',
                child: Row(
                  children: [
                    const Icon(Icons.link_rounded, size: 18, color: AppColors.accent),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        preview.applyOn ?? preview.source,
                        style: const TextStyle(color: AppColors.muted, fontSize: 14),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 28),
              const Text(
                'Similar jobs',
                style: TextStyle(
                  color: AppColors.text,
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 12),
              AsyncValueView(
                value: similar,
                isEmpty: (jobs) => jobs.isEmpty,
                emptyMessage: 'No similar jobs found',
                onRefresh: () => ref.refresh(similarJobsProvider(id).future),
                builder: (context, jobs) => Column(
                  children: [for (final j in jobs) JobCard(job: j)],
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.job});

  final Job job;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              LogoImage(name: job.displayCompany, url: job.companyLogo, size: 64, radius: 18),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (job.sponsored)
                      Row(
                        children: [
                          const Icon(Icons.workspace_premium_rounded,
                              size: 14, color: AppColors.warning),
                          const SizedBox(width: 4),
                          const Text(
                            'Sponsored',
                            style: TextStyle(
                                color: AppColors.warning, fontSize: 12),
                          ),
                        ],
                      ),
                    const SizedBox(height: 4),
                    Text(
                      job.title,
                      style: const TextStyle(
                        color: AppColors.text,
                        fontSize: 21,
                        fontWeight: FontWeight.w800,
                        height: 1.2,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      job.displayCompany,
                      style: const TextStyle(
                          color: AppColors.accent, fontSize: 15),
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (job.level != null && job.level!.isNotEmpty) ...[
            const SizedBox(height: 14),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
              decoration: BoxDecoration(
                color: job.levelColor.withOpacity(0.15),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                Job.levelLabel(job.level),
                style: TextStyle(color: job.levelColor, fontSize: 12, fontWeight: FontWeight.w600),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _Highlights extends StatelessWidget {
  const _Highlights({required this.job});

  final Job job;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Row(
            children: [
              _HighlightItem(icon: Icons.attach_money_rounded, label: job.salaryDisplay, color: AppColors.success),
              const SizedBox(width: 8),
              _HighlightItem(
                icon: job.remote ? Icons.wifi_rounded : Icons.location_on_outlined,
                label: job.remote ? 'Remote' : (job.location ?? 'Anywhere'),
                color: AppColors.accent,
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              if (job.jobType != null && job.jobType!.isNotEmpty) ...[
                _HighlightItem(icon: Icons.work_outline_rounded, label: job.jobType!, color: AppColors.primary),
                const SizedBox(width: 8),
              ],
              _HighlightItem(
                icon: Icons.auto_awesome_rounded,
                label: job.experienceDisplay,
                color: AppColors.warning,
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              _HighlightItem(
                icon: Icons.schedule_outlined,
                label: job.postedDisplay.isEmpty ? 'Now hiring' : 'Posted ${job.postedDisplay}',
                color: AppColors.muted,
              ),
              const SizedBox(width: 8),
              _HighlightItem(
                icon: Icons.visibility_outlined,
                label: '${job.views} views',
                color: AppColors.muted,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _HighlightItem extends StatelessWidget {
  const _HighlightItem({required this.icon, required this.label, required this.color});

  final IconData icon;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: const Color(0x0FFFFFFF),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 17, color: color),
            const SizedBox(width: 7),
            Flexible(
              child: Text(
                label,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(color: AppColors.text, fontSize: 13),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              color: AppColors.text,
              fontSize: 16,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 12),
          child,
        ],
      ),
    );
  }
}

class _SkillChips extends StatelessWidget {
  const _SkillChips({required this.skills});

  final List<String> skills;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        for (final skill in skills)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
            decoration: BoxDecoration(
              color: AppColors.primary.withOpacity(0.12),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: AppColors.primary.withOpacity(0.3)),
            ),
            child: Text(
              skill,
              style: const TextStyle(color: AppColors.accent, fontSize: 13),
            ),
          ),
      ],
    );
  }
}

class _ApplyBar extends StatelessWidget {
  const _ApplyBar({required this.job});

  final Job job;

  Future<void> _apply(BuildContext context) async {
    final url = job.applyUrl;
    if (url == null || url.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No application link is available for this job')),
      );
      return;
    }
    final uri = Uri.tryParse(url);
    if (uri == null) return;
    final launched = await launchUrl(uri, mode: LaunchMode.externalApplication);
    if (!launched && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Could not open the application link')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 10, 20, 12),
        child: FilledButton.icon(
          onPressed: () => _apply(context),
          icon: const Icon(Icons.open_in_new_rounded, size: 20),
          label: Text(
            job.applyUrl == null || job.applyUrl!.isEmpty
                ? 'Apply Unavailable'
                : 'Apply on ${job.applyOn ?? 'Original Website'}',
          ),
        ),
      ),
    );
  }
}