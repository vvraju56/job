import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/glass_card.dart';
import '../../../core/widgets/logo_image.dart';
import '../../applications/providers/applications_provider.dart';
import '../../auth/providers/auth_provider.dart';
import '../../jobs/providers/jobs_providers.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);
    final user = auth.user;
    final savedCount = ref.watch(savedJobsProvider).maybeWhen(
          data: (jobs) => jobs.length,
          orElse: () => 0,
        );
    final appCount = ref.watch(applicationsProvider).maybeWhen(
          data: (apps) => apps.length,
          orElse: () => 0,
        );

    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
        children: [
          GlassCard(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    LogoImage(
                      name: user?.displayName ?? 'User',
                      url: user?.avatarUrl,
                      size: 64,
                      radius: 18,
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            user?.displayName ?? 'Your name',
                            style: const TextStyle(
                              color: AppColors.text,
                              fontSize: 19,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            user?.email ?? '',
                            style:
                                const TextStyle(color: AppColors.muted, fontSize: 13),
                          ),
                          if (user?.headline != null &&
                              user!.headline!.isNotEmpty) ...[
                            const SizedBox(height: 6),
                            Text(
                              user.headline!,
                              style: const TextStyle(
                                  color: AppColors.accent, fontSize: 13),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                Row(
                  children: [
                    _StatTile(icon: Icons.bookmark_border_rounded, value: '$savedCount', label: 'Saved'),
                    const SizedBox(width: 10),
                    _StatTile(icon: Icons.fact_check_outlined, value: '$appCount', label: 'Applied'),
                    const SizedBox(width: 10),
                    _StatTile(icon: Icons.bolt_rounded, value: '${user?.experienceYears ?? 0} yrs', label: 'Experience'),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          _MenuTile(
            icon: Icons.work_outline_rounded,
            title: 'My applications',
            subtitle: 'Track every application status',
            onTap: () => context.push('/applications'),
          ),
          const SizedBox(height: 10),
          _MenuTile(
            icon: Icons.bookmark_outline_rounded,
            title: 'Saved jobs',
            subtitle: '$savedCount saved',
            onTap: () => context.go('/app/saved'),
          ),
          const SizedBox(height: 10),
          _MenuTile(
            icon: Icons.description_outlined,
            title: 'Resume',
            subtitle: user?.resumeUrl == null
                ? 'Upload your resume'
                : 'Resume uploaded',
            onTap: () => ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(
                  user?.resumeUrl == null
                      ? 'Resume upload is coming soon'
                      : 'Open resume: ${user?.resumeUrl}',
                ),
              ),
            ),
          ),
          const SizedBox(height: 10),
          _MenuTile(
            icon: Icons.settings_outlined,
            title: 'Settings',
            subtitle: 'Theme, cache & account',
            onTap: () => context.push('/settings'),
          ),
          const SizedBox(height: 20),
          _SkillsCard(skills: user?.skills ?? const []),
          const SizedBox(height: 20),
          OutlinedButton.icon(
            onPressed: () async {
              await ref.read(authProvider.notifier).logout();
              if (context.mounted) context.go('/login');
            },
            icon: const Icon(Icons.logout_rounded, color: AppColors.danger),
            label: const Text('Sign out', style: TextStyle(color: AppColors.danger)),
          ),
        ],
      ),
    );
  }
}

class _StatTile extends StatelessWidget {
  const _StatTile({
    required this.icon,
    required this.value,
    required this.label,
  });

  final IconData icon;
  final String value;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: const Color(0x0FFFFFFF),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Column(
          children: [
            Icon(icon, color: AppColors.accent, size: 20),
            const SizedBox(height: 6),
            Text(
              value,
              style: const TextStyle(
                color: AppColors.text,
                fontWeight: FontWeight.w700,
                fontSize: 15,
              ),
            ),
            Text(
              label,
              style: const TextStyle(color: AppColors.muted, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}

class _MenuTile extends StatelessWidget {
  const _MenuTile({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      borderRadius: 16,
      padding: const EdgeInsets.all(4),
      child: ListTile(
        onTap: onTap,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        leading: Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: AppColors.primary.withOpacity(0.15),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(icon, color: AppColors.accent, size: 20),
        ),
        title: Text(
          title,
          style: const TextStyle(color: AppColors.text, fontWeight: FontWeight.w600),
        ),
        subtitle: Text(subtitle, style: const TextStyle(color: AppColors.muted, fontSize: 12)),
        trailing: const Icon(Icons.chevron_right_rounded, color: AppColors.muted),
      ),
    );
  }
}

class _SkillsCard extends StatelessWidget {
  const _SkillsCard({required this.skills});

  final List<String> skills;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Skills',
            style: TextStyle(
              color: AppColors.text,
              fontSize: 16,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 12),
          if (skills.isEmpty)
            const Text(
              'Add skills to get better recommendations.',
              style: TextStyle(color: AppColors.muted, fontSize: 13),
            )
          else
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final skill in skills)
                  Chip(label: Text(skill), deleteIcon: const Icon(Icons.close, size: 15)),
              ],
            ),
        ],
      ),
    );
  }
}