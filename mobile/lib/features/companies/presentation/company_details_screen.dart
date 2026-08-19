import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/async_value_view.dart';
import '../../../core/widgets/glass_card.dart';
import '../../../core/widgets/logo_image.dart';
import '../../companies/models/company.dart';
import '../../companies/providers/companies_providers.dart';
import '../../jobs/models/job.dart';
import '../../jobs/presentation/widgets/job_card.dart';

class CompanyDetailsScreen extends ConsumerWidget {
  const CompanyDetailsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final slug = GoRouterState.of(context).pathParameters['slug'] ?? '';
    final company = ref.watch(companyProvider(slug));
    final openings = ref.watch(companyOpeningsProvider(slug));

    return Scaffold(
      appBar: AppBar(title: const Text('Company')),
      body: AsyncValueView(
        value: company,
        isEmpty: (c) => c.slug.isEmpty,
        emptyMessage: 'Company not found',
        onRefresh: () => ref.refresh(companyProvider(slug).future),
        builder: (context, data) => ListView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
          children: [
            _CompanyHeader(company: data),
            const SizedBox(height: 16),
            if (data.description != null && data.description!.isNotEmpty)
              GlassCard(
                padding: const EdgeInsets.all(16),
                child: Text(
                  data.description!,
                  style: const TextStyle(
                    color: AppColors.text,
                    fontSize: 14.5,
                    height: 1.6,
                  ),
                ),
              ),
            const SizedBox(height: 16),
            _OpenPositions(value: openings),
          ],
        ),
      ),
    );
  }
}

class _CompanyHeader extends StatelessWidget {
  const _CompanyHeader({required this.company});

  final Company company;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              LogoImage(name: company.name, url: company.logo, size: 68, radius: 18),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Flexible(
                          child: Text(
                            company.name,
                            style: const TextStyle(
                              color: AppColors.text,
                              fontSize: 20,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ),
                        if (company.verified) ...[
                          const SizedBox(width: 6),
                          const Icon(Icons.verified_rounded,
                              size: 18, color: AppColors.accent),
                        ],
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(
                      [
                        if (company.industry != null) company.industry!,
                        if (company.location != null) company.location!,
                        if (company.size != null) company.size!,
                      ].join(' · '),
                      style: const TextStyle(color: AppColors.muted, fontSize: 13),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              if (company.rating != null) ...[
                const Icon(Icons.star_rounded, color: AppColors.warning, size: 18),
                const SizedBox(width: 4),
                Text(
                  company.rating!.toStringAsFixed(1),
                  style: const TextStyle(
                      color: AppColors.text, fontWeight: FontWeight.w700),
                ),
                Text(
                  ' (${company.reviewCount} reviews)',
                  style: const TextStyle(color: AppColors.muted, fontSize: 13),
                ),
                const SizedBox(width: 16),
              ],
              const Icon(Icons.work_outline_rounded,
                  color: AppColors.success, size: 18),
              const SizedBox(width: 4),
              Text(
                '${company.openPositions} open positions',
                style: const TextStyle(
                    color: AppColors.success, fontWeight: FontWeight.w600),
              ),
            ],
          ),
          if (company.website != null && company.website!.isNotEmpty) ...[
            const SizedBox(height: 16),
            OutlinedButton.icon(
              onPressed: () =>
                  launchUrl(Uri.parse(company.website!), mode: LaunchMode.externalApplication),
              icon: const Icon(Icons.language_rounded, size: 18),
              label: const Text('Visit website'),
            ),
          ],
        ],
      ),
    );
  }
}

class _OpenPositions extends StatelessWidget {
  const _OpenPositions({required this.value});

  final AsyncValue<List<Job>> value;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Open positions',
          style: TextStyle(
            color: AppColors.text,
            fontSize: 18,
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: 12),
        AsyncValueView(
          value: value,
          isEmpty: (jobs) => jobs.isEmpty,
          emptyMessage: 'No open positions right now',
          builder: (context, jobs) =>
              Column(children: [for (final job in jobs) JobCard(job: job)]),
        ),
      ],
    );
  }
}