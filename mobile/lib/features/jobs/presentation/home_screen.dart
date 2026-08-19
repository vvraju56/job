import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/async_value_view.dart';
import '../../../core/widgets/glass_card.dart';
import '../../auth/providers/auth_provider.dart';
import '../../notifications/providers/notifications_provider.dart';
import '../../companies/providers/companies_providers.dart';
import '../models/job.dart';
import '../providers/jobs_providers.dart';
import 'widgets/company_card.dart';
import 'widgets/job_card.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider.select((s) => s.user));
    final unread = ref.watch(unreadNotificationsProvider);
    final recommended = ref.watch(recommendedJobsProvider);
    final trending = ref.watch(trendingJobsProvider);
    final companies = ref.watch(trendingCompaniesProvider);

    return Scaffold(
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () async {
            ref.invalidate(recommendedJobsProvider);
            ref.invalidate(trendingJobsProvider);
            ref.invalidate(trendingCompaniesProvider);
            await ref.read(recommendedJobsProvider.future);
          },
          child: CustomScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            slivers: [
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _Header(userName: user?.displayName, unread: unread),
                      const SizedBox(height: 20),
                      _SearchBar(onTap: () => context.go('/app/search')),
                      const SizedBox(height: 28),
                      const _SectionTitle(
                        title: 'Trending now',
                        icon: Icons.local_fire_department_rounded,
                        color: AppColors.warning,
                      ),
                    ],
                  ),
                ),
              ),
              SliverToBoxAdapter(
                child: SizedBox(
                  height: 212,
                  child: AsyncValueView(
                    value: trending,
                    isEmpty: (jobs) => jobs.isEmpty,
                    emptyMessage: 'No trending jobs right now',
                    onRefresh: () => ref.refresh(trendingJobsProvider.future),
                    builder: (context, jobs) => ListView.separated(
                      padding: const EdgeInsets.symmetric(horizontal: 20),
                      scrollDirection: Axis.horizontal,
                      itemCount: jobs.length,
                      separatorBuilder: (_, __) => const SizedBox(width: 12),
                      itemBuilder: (context, i) => SizedBox(
                        width: 280,
                        child: JobCard(job: jobs[i]),
                      ),
                    ),
                  ),
                ),
              ),
              const SliverToBoxAdapter(
                child: Padding(
                  padding: EdgeInsets.fromLTRB(20, 28, 20, 0),
                  child: _SectionTitle(
                    title: 'Trending companies',
                    icon: Icons.apartment_rounded,
                    color: AppColors.accent,
                  ),
                ),
              ),
              SliverToBoxAdapter(
                child: SizedBox(
                  height: 168,
                  child: AsyncValueView(
                    value: companies,
                    isEmpty: (list) => list.isEmpty,
                    emptyMessage: 'No companies yet',
                    onRefresh: () => ref.refresh(trendingCompaniesProvider.future),
                    builder: (context, list) => ListView.separated(
                      padding: const EdgeInsets.symmetric(horizontal: 20),
                      scrollDirection: Axis.horizontal,
                      itemCount: list.length,
                      separatorBuilder: (_, __) => const SizedBox(width: 12),
                      itemBuilder: (context, i) => CompanyCard(company: list[i]),
                    ),
                  ),
                ),
              ),
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(20, 28, 20, 0),
                  child: _SectionTitle(
                    title: 'Recommended for you',
                    icon: Icons.thumb_up_alt_outlined,
                    color: AppColors.success,
                  ),
                ),
              ),
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
                  child: AsyncValueView(
                    value: recommended,
                    isEmpty: (jobs) => jobs.isEmpty,
                    emptyMessage: 'No recommendations yet — complete your profile',
                    onRefresh: () => ref.refresh(recommendedJobsProvider.future),
                    builder: (context, jobs) => Column(
                      children: [
                        for (final job in jobs.take(5)) JobCard(job: job),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.userName, required this.unread});

  final String? userName;
  final int unread;

  @override
  Widget build(BuildContext context) {
    final hour = DateTime.now().hour;
    final greeting = hour < 12
        ? 'Good morning'
        : hour < 18
            ? 'Good afternoon'
            : 'Good evening';

    return Row(
      children: [
        Container(
          width: 46,
          height: 46,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(14),
            gradient: const LinearGradient(
              colors: [AppColors.secondary, AppColors.primary],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          child: const Icon(Icons.work_rounded, color: Colors.white, size: 24),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                greeting,
                style: const TextStyle(color: AppColors.muted, fontSize: 13),
              ),
              Text(
                userName ?? 'Makeable Jobs',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: AppColors.text,
                  fontSize: 17,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ),
        IconButton(
          onPressed: () => context.go('/app/notifications'),
          icon: Badge(
            isLabelVisible: unread > 0,
            label: Text('$unread'),
            child: const Icon(Icons.notifications_none_rounded,
                color: AppColors.text),
          ),
          tooltip: 'Notifications',
        ),
      ],
    );
  }
}

class _SearchBar extends StatelessWidget {
  const _SearchBar({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      borderRadius: 16,
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          child: Row(
            children: [
              const Icon(Icons.search_rounded, color: AppColors.muted),
              const SizedBox(width: 12),
              const Expanded(
                child: Text(
                  'Search jobs, companies, skills…',
                  style: TextStyle(color: AppColors.muted, fontSize: 15),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: AppColors.primary.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Text(
                  'Filters',
                  style: TextStyle(color: AppColors.accent, fontSize: 12),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle({required this.title, required this.icon, required this.color});

  final String title;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 20, color: color),
        const SizedBox(width: 8),
        Text(
          title,
          style: const TextStyle(
            color: AppColors.text,
            fontSize: 18,
            fontWeight: FontWeight.w700,
          ),
        ),
      ],
    );
  }
}
