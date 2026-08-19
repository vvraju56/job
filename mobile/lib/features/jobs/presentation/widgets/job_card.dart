import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/glass_card.dart';
import '../../../../core/widgets/logo_image.dart';
import '../../models/job.dart';
import '../../providers/jobs_providers.dart';

/// Tappable glass job card used across Home, Search and Saved screens.
class JobCard extends ConsumerWidget {
  const JobCard({super.key, required this.job, this.compact = false});

  final Job job;
  final bool compact;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final saved = ref.watch(savedJobsProvider).maybeWhen(
          data: (items) => items.any((j) => j.id == job.id),
          orElse: () => false,
        );

    return GlassCard(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: () => context.push('/jobs/${job.id}', extra: job),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                LogoImage(name: job.displayCompany, url: job.companyLogo, size: 48),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          if (job.sponsored) ...[
                            const Icon(Icons.workspace_premium_rounded,
                                size: 14, color: AppColors.warning),
                            const SizedBox(width: 4),
                            const Text(
                              'Sponsored',
                              style: TextStyle(
                                color: AppColors.warning,
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            const SizedBox(width: 8),
                          ],
                          Container(
                            width: 8,
                            height: 8,
                            decoration: BoxDecoration(
                              color: job.sourceColor,
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 5),
                          Text(
                            Job.sourceLabel(job.source),
                            style: const TextStyle(
                              color: AppColors.muted,
                              fontSize: 11,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 2),
                      Text(
                        job.title,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          color: AppColors.text,
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        job.displayCompany,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(color: AppColors.accent, fontSize: 13),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  onPressed: () =>
                      ref.read(savedJobsProvider.notifier).toggle(job),
                  icon: Icon(
                    saved ? Icons.bookmark_rounded : Icons.bookmark_border_rounded,
                    color: saved ? AppColors.warning : AppColors.muted,
                  ),
                  tooltip: saved ? 'Remove from saved' : 'Save job',
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (!compact) ...[
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  if (job.remote)
                    const _MetaChip(icon: Icons.wifi_rounded, label: 'Remote')
                  else if (job.location != null && job.location!.isNotEmpty)
                    _MetaChip(icon: Icons.location_on_outlined, label: job.location!),
                  if (job.jobType != null && job.jobType!.isNotEmpty)
                    _MetaChip(icon: Icons.work_outline_rounded, label: job.jobType!),
                  _MetaChip(
                    icon: Icons.schedule_outlined,
                    label: job.postedDisplay.isEmpty ? 'Now hiring' : job.postedDisplay,
                  ),
                ],
              ),
              const SizedBox(height: 12),
            ],
            Row(
              children: [
                Expanded(
                  child: Text(
                    job.salaryDisplay,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: AppColors.success,
                      fontWeight: FontWeight.w600,
                      fontSize: 13,
                    ),
                  ),
                ),
                if (!compact && job.skills.isNotEmpty)
                  Flexible(
                    child: Text(
                      job.skills.take(3).join(' · '),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(color: AppColors.muted, fontSize: 12),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _MetaChip extends StatelessWidget {
  const _MetaChip({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: const Color(0x1AFFFFFF),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: AppColors.muted),
          const SizedBox(width: 5),
          Text(
            label,
            style: const TextStyle(color: AppColors.text, fontSize: 12),
          ),
        ],
      ),
    );
  }
}