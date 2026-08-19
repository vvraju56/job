import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/glass_card.dart';
import '../../../../core/widgets/logo_image.dart';
import '../../../companies/models/company.dart';

/// Compact glass card for trending companies on the Home screen.
class CompanyCard extends StatelessWidget {
  const CompanyCard({super.key, required this.company, this.width = 220});

  final Company company;
  final double width;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: width,
      child: GlassCard(
        padding: const EdgeInsets.all(16),
        child: InkWell(
          borderRadius: BorderRadius.circular(20),
          onTap: () => context.push('/companies/${company.slug}'),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  LogoImage(name: company.name, url: company.logo, size: 42, radius: 12),
                  const SizedBox(width: 10),
                  if (company.verified)
                    const Icon(Icons.verified_rounded,
                        size: 16, color: AppColors.accent),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                company.name,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: AppColors.text,
                  fontWeight: FontWeight.w700,
                  fontSize: 15,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                company.industry ?? company.location ?? 'Company',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(color: AppColors.muted, fontSize: 12),
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  if (company.rating != null) ...[
                    const Icon(Icons.star_rounded, size: 16, color: AppColors.warning),
                    const SizedBox(width: 4),
                    Text(
                      company.rating!.toStringAsFixed(1),
                      style: const TextStyle(
                        color: AppColors.text,
                        fontWeight: FontWeight.w600,
                        fontSize: 13,
                      ),
                    ),
                    const SizedBox(width: 10),
                  ],
                  Expanded(
                    child: Text(
                      '${company.openPositions} open',
                      textAlign: TextAlign.right,
                      style: const TextStyle(
                        color: AppColors.success,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}