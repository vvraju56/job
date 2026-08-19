import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../core/theme/app_theme.dart';

/// Mirrors the backend `JobOut` schema.
class Job {
  const Job({
    required this.id,
    required this.source,
    required this.title,
    required this.description,
    this.companyId,
    this.companyName,
    this.companyLogo,
    this.location,
    this.remote = false,
    this.salaryMin,
    this.salaryMax,
    this.salaryCurrency = 'USD',
    this.salaryText,
    this.jobType,
    this.level,
    this.skills = const [],
    this.applyUrl,
    this.applyOn,
    this.experienceMin,
    this.experienceMax,
    this.postedAt,
    this.sponsored = false,
    this.views = 0,
  });

  final String id;
  final String source;
  final String title;
  final String description;
  final String? companyId;
  final String? companyName;
  final String? companyLogo;
  final String? location;
  final bool remote;
  final double? salaryMin;
  final double? salaryMax;
  final String salaryCurrency;
  final String? salaryText;
  final String? jobType;
  final String? level;
  final List<String> skills;
  final String? applyUrl;
  final String? applyOn;
  final int? experienceMin;
  final int? experienceMax;
  final DateTime? postedAt;
  final bool sponsored;
  final int views;

  factory Job.fromJson(Map<String, dynamic> json) {
    String? str(String key) {
      final v = json[key];
      return v == null ? null : v.toString();
    }

    double? numV(String key) {
      final v = json[key];
      if (v == null) return null;
      if (v is num) return v.toDouble();
      return double.tryParse(v.toString());
    }

    int? intV(String key) {
      final v = json[key];
      if (v == null) return null;
      if (v is num) return v.toInt();
      return int.tryParse(v.toString());
    }

    bool boolV(String key) {
      final v = json[key];
      if (v is bool) return v;
      return v.toString().toLowerCase() == 'true';
    }

    DateTime? parseDate(dynamic v) {
      if (v == null) return null;
      if (v is DateTime) return v;
      return DateTime.tryParse(v.toString());
    }

    final skills = <String>[];
    final rawSkills = json['skills'];
    if (rawSkills is List) {
      for (final s in rawSkills) {
        if (s != null) skills.add(s.toString());
      }
    } else if (rawSkills is String && rawSkills.isNotEmpty) {
      skills.addAll(rawSkills.split(',').map((s) => s.trim()).where((s) => s.isNotEmpty));
    }

    return Job(
      id: json['id'].toString(),
      source: str('source') ?? '',
      title: str('title') ?? 'Untitled position',
      description: str('description') ?? '',
      companyId: str('company_id'),
      companyName: str('company_name'),
      companyLogo: str('company_logo'),
      location: str('location'),
      remote: boolV('remote'),
      salaryMin: numV('salary_min'),
      salaryMax: numV('salary_max'),
      salaryCurrency: str('salary_currency') ?? 'USD',
      salaryText: str('salary_text'),
      jobType: str('job_type'),
      level: str('level'),
      skills: skills,
      applyUrl: str('apply_url'),
      applyOn: str('apply_on'),
      experienceMin: intV('experience_min'),
      experienceMax: intV('experience_max'),
      postedAt: parseDate(json['posted_at']),
      sponsored: boolV('sponsored'),
      views: intV('views') ?? 0,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'source': source,
        'title': title,
        'description': description,
        'company_id': companyId,
        'company_name': companyName,
        'company_logo': companyLogo,
        'location': location,
        'remote': remote,
        'salary_min': salaryMin,
        'salary_max': salaryMax,
        'salary_currency': salaryCurrency,
        'salary_text': salaryText,
        'job_type': jobType,
        'level': level,
        'skills': skills,
        'apply_url': applyUrl,
        'apply_on': applyOn,
        'experience_min': experienceMin,
        'experience_max': experienceMax,
        'posted_at': postedAt?.toIso8601String(),
        'sponsored': sponsored,
        'views': views,
      };

  String get displayCompany => companyName ?? 'Unknown company';

  /// Prefer the server-provided salary text, otherwise build "min - max".
  String get salaryDisplay {
    if (salaryText != null && salaryText!.isNotEmpty) return salaryText!;
    if (salaryMin != null && salaryMax != null) {
      final fmt = NumberFormat.compactCurrency(
        symbol: _currencySymbol(salaryCurrency),
        decimalDigits: 0,
      );
      return '${fmt.format(salaryMin)} - ${fmt.format(salaryMax)}';
    }
    if (salaryMin != null) {
      return 'From ${NumberFormat.compactCurrency(symbol: _currencySymbol(salaryCurrency), decimalDigits: 0).format(salaryMin)}';
    }
    return 'Salary on application';
  }

  String _currencySymbol(String code) => switch (code.toUpperCase()) {
        'USD' => r'$',
        'EUR' => '€',
        'GBP' => '£',
        _ => '$code ',
      };

  String get postedDisplay {
    if (postedAt == null) return '';
    final diff = DateTime.now().difference(postedAt!);
    if (diff.inMinutes < 1) return 'Just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    if (diff.inDays < 7) return '${diff.inDays}d ago';
    return DateFormat('MMM d').format(postedAt!);
  }

  String get experienceDisplay {
    if (experienceMin == null && experienceMax == null) return 'Any experience';
    if (experienceMin == null) return 'Up to $experienceMax yrs';
    if (experienceMax == null) return '$experienceMin+ yrs';
    return '$experienceMin-$experienceMax yrs';
  }

  Color get levelColor => switch ((level ?? '').toLowerCase()) {
        'entry' || 'junior' => AppColors.success,
        'mid' || 'intermediate' => AppColors.accent,
        'senior' => AppColors.warning,
        'lead' || 'manager' || 'director' => AppColors.danger,
        _ => AppColors.muted,
      };

  static String levelLabel(String? level) => switch (level?.toLowerCase()) {
        'entry' => 'Entry level',
        'junior' => 'Junior',
        'mid' => 'Mid level',
        'intermediate' => 'Intermediate',
        'senior' => 'Senior',
        'lead' => 'Lead',
        'manager' => 'Manager',
        'director' => 'Director',
        'executive' => 'Executive',
        _ => 'Any level',
      };

  /// Human-readable source badge label (matches the web SOURCE_LABELS).
  static String sourceLabel(String? source) => switch (source?.toLowerCase()) {
        'serpapi' => 'Google Jobs',
        'usajobs' => 'USAJobs',
        'jsearch' => 'JSearch',
        'greenhouse' => 'Greenhouse',
        'ashby' => 'Ashby',
        'remoteok' => 'Remote OK',
        'linkedin' => 'LinkedIn',
        'indeed' => 'Indeed',
        'naukri' => 'Naukri',
        'internshala' => 'Internshala',
        'wellfound' => 'Wellfound',
        'company' => 'Company Website',
        'manual' => 'Manual',
        _ => (source ?? 'Unknown').toUpperCase(),
      };

  /// Brand color per source for the badge dot.
  Color get sourceColor => switch (source.toLowerCase()) {
        'serpapi' => AppColors.success,
        'usajobs' => const Color(0xFF60A5FA),
        'jsearch' => const Color(0xFFC084FC),
        'greenhouse' => const Color(0xFFFB923C),
        'ashby' => const Color(0xFFFBBF24),
        'remoteok' => AppColors.muted,
        _ => AppColors.accent,
      };
}