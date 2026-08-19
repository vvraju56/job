import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

/// Company/avatar logo with graceful fallback: a gradient circle with the
/// initials of [name] when the network image fails or is missing.
class LogoImage extends StatelessWidget {
  const LogoImage({
    super.key,
    required this.name,
    this.url,
    this.size = 48,
    this.radius = 14,
  });

  final String name;
  final String? url;
  final double size;
  final double radius;

  @override
  Widget build(BuildContext context) {
    final hasUrl = url != null && url!.isNotEmpty;
    if (!hasUrl) return _Fallback(name: name, size: size, radius: radius);

    return ClipRRect(
      borderRadius: BorderRadius.circular(radius),
      child: CachedNetworkImage(
        imageUrl: url!,
        width: size,
        height: size,
        fit: BoxFit.cover,
        placeholder: (context, _) => Container(
          width: size,
          height: size,
          color: const Color(0x1AFFFFFF),
          child: const Icon(Icons.image_outlined, color: AppColors.muted),
        ),
        errorWidget: (context, _, __) => _Fallback(name: name, size: size, radius: radius),
      ),
    );
  }
}

class _Fallback extends StatelessWidget {
  const _Fallback({required this.name, required this.size, required this.radius});

  final String name;
  final double size;
  final double radius;

  @override
  Widget build(BuildContext context) {
    final initials = name
        .trim()
        .split(RegExp(r'\s+'))
        .where((w) => w.isNotEmpty)
        .take(2)
        .map((w) => w[0].toUpperCase())
        .join();

    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(radius),
        gradient: const LinearGradient(
          colors: [AppColors.secondary, AppColors.primary],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      alignment: Alignment.center,
      child: Text(
        initials.isEmpty ? 'M' : initials,
        style: TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.w700,
          fontSize: size * 0.38,
        ),
      ),
    );
  }
}