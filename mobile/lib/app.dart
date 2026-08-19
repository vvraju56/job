import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';
import 'features/notifications/providers/notifications_provider.dart';

class MakeableJobsApp extends ConsumerStatefulWidget {
  const MakeableJobsApp({super.key});

  @override
  ConsumerState<MakeableJobsApp> createState() => _MakeableJobsAppState();
}

class _MakeableJobsAppState extends ConsumerState<MakeableJobsApp> {
  bool _fcmInitiated = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_fcmInitiated) return;
      _fcmInitiated = true;
      ref.read(fcmServiceProvider).initialize();
    });
  }

  @override
  Widget build(BuildContext context) {
    final router = ref.watch(appRouterProvider);
    return MaterialApp.router(
      title: 'Makeable Jobs',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.dark,
      routerConfig: router,
    );
  }
}