import 'package:flutter/material.dart';

import '../../../core/theme/app_theme.dart';

enum ApplicationStatus { applied, reviewing, interview, offer, rejected, withdrawn }

extension ApplicationStatusX on ApplicationStatus {
  String get label => switch (this) {
        ApplicationStatus.applied => 'Applied',
        ApplicationStatus.reviewing => 'Reviewing',
        ApplicationStatus.interview => 'Interview',
        ApplicationStatus.offer => 'Offer',
        ApplicationStatus.rejected => 'Rejected',
        ApplicationStatus.withdrawn => 'Withdrawn',
      };

  Color get color => switch (this) {
        ApplicationStatus.applied => AppColors.accent,
        ApplicationStatus.reviewing => AppColors.warning,
        ApplicationStatus.interview => AppColors.primary,
        ApplicationStatus.offer => AppColors.success,
        ApplicationStatus.rejected => AppColors.danger,
        ApplicationStatus.withdrawn => AppColors.muted,
      };
}

/// Mirrors the backend `ApplicationOut` schema.
class Application {
  const Application({
    required this.id,
    required this.jobId,
    this.jobTitle,
    this.companyName,
    this.companyLogo,
    required this.status,
    this.notes,
    this.appliedAt,
  });

  final String id;
  final String jobId;
  final String? jobTitle;
  final String? companyName;
  final String? companyLogo;
  final ApplicationStatus status;
  final String? notes;
  final DateTime? appliedAt;

  factory Application.fromJson(Map<String, dynamic> json) {
    String? str(String key) {
      final v = json[key];
      return v == null ? null : v.toString();
    }

    ApplicationStatus parseStatus(String? s) {
      return ApplicationStatus.values.firstWhere(
        (e) => e.name == s || e.label.toLowerCase() == (s ?? '').toLowerCase(),
        orElse: () => ApplicationStatus.applied,
      );
    }

    return Application(
      id: json['id'].toString(),
      jobId: (json['job_id'] ?? json['job']).toString(),
      jobTitle: str('job_title'),
      companyName: str('company_name'),
      companyLogo: str('company_logo'),
      status: parseStatus(str('status')),
      notes: str('notes'),
      appliedAt: DateTime.tryParse(str('applied_at') ?? ''),
    );
  }

  String get statusLabel => status.label;
}