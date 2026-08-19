import 'package:flutter/material.dart';

import '../../../core/theme/app_theme.dart';

/// User account returned by `/auth/me` and used on the profile screen.
class User {
  const User({
    required this.id,
    required this.email,
    this.name,
    this.avatarUrl,
    this.headline,
    this.bio,
    this.location,
    this.skills = const [],
    this.experience = const [],
    this.experienceYears,
    this.resumeUrl,
    this.createdAt,
  });

  final String id;
  final String email;
  final String? name;
  final String? avatarUrl;
  final String? headline;
  final String? bio;
  final String? location;
  final List<String> skills;
  final List<String> experience;
  final int? experienceYears;
  final String? resumeUrl;
  final DateTime? createdAt;

  String get displayName => (name == null || name!.isEmpty) ? email : name!;

  factory User.fromJson(Map<String, dynamic> json) {
    String? str(String key) {
      final v = json[key];
      return v == null ? null : v.toString();
    }

    List<String> list(String key) {
      final raw = json[key];
      if (raw is List) {
        return raw.map((e) => e.toString()).toList();
      }
      if (raw is String && raw.isNotEmpty) {
        return raw.split(',').map((s) => s.trim()).where((s) => s.isNotEmpty).toList();
      }
      return const [];
    }

    int? intV(String key) {
      final v = json[key];
      if (v == null) return null;
      if (v is num) return v.toInt();
      return int.tryParse(v.toString());
    }

    return User(
      id: json['id'].toString(),
      email: str('email') ?? '',
      name: str('name') ?? str('full_name'),
      avatarUrl: str('avatar_url') ?? str('profile_picture'),
      headline: str('headline'),
      bio: str('bio'),
      location: str('location'),
      skills: list('skills'),
      experience: list('experience'),
      experienceYears: intV('experience_years'),
      resumeUrl: str('resume_url'),
      createdAt: DateTime.tryParse(str('created_at') ?? ''),
    );
  }

  Color get avatarColor => AppColors.primary;
}