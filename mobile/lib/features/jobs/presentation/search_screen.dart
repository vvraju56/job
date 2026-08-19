import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/async_value_view.dart';
import '../../../core/widgets/glass_card.dart';
import '../data/jobs_repository.dart';
import '../providers/jobs_providers.dart';
import 'widgets/job_card.dart';

class SearchScreen extends ConsumerStatefulWidget {
  const SearchScreen({super.key});

  @override
  ConsumerState<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends ConsumerState<SearchScreen> {
  final _queryController = TextEditingController();
  final _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(() {
      if (_scrollController.position.extentAfter < 300) {
        ref.read(searchControllerProvider.notifier).loadMore();
      }
    });
  }

  @override
  void dispose() {
    _queryController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _runSearch() async {
    final notifier = ref.read(searchControllerProvider.notifier);
    notifier.updateParams(
      ref.read(searchControllerProvider).params.copyWith(query: _queryController.text),
    );
    await notifier.search();
  }

  Future<void> _openFilters(JobSearchParams current) async {
    final result = await showModalBottomSheet<JobSearchParams>(
      context: context,
      isScrollControlled: true,
      builder: (_) => _FilterSheet(initial: current),
    );
    if (result == null || !mounted) return;
    final notifier = ref.read(searchControllerProvider.notifier);
    notifier.updateParams(result);
    notifier.search();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(searchControllerProvider);

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Search',
                    style: TextStyle(
                      color: AppColors.text,
                      fontSize: 26,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _queryController,
                          textInputAction: TextInputAction.search,
                          onSubmitted: (_) => _runSearch(),
                          decoration: const InputDecoration(
                            hintText: 'Search jobs, companies, skills…',
                            prefixIcon: Icon(Icons.search_rounded, color: AppColors.muted),
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),
                      GlassCard(
                        borderRadius: 14,
                        padding: const EdgeInsets.all(4),
                        child: IconButton(
                          onPressed: () => _openFilters(state.params),
                          icon: const Icon(Icons.tune_rounded, color: AppColors.accent),
                          tooltip: 'Filters',
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: [
                        _FilterChipButton(
                          label: 'Remote',
                          selected: state.params.remote,
                          onTap: () {
                            final notifier =
                                ref.read(searchControllerProvider.notifier);
                            notifier.updateParams(
                              state.params.copyWith(remote: !state.params.remote),
                            );
                            notifier.search();
                          },
                        ),
                        const SizedBox(width: 8),
                        _FilterChipButton(
                          label: state.params.jobType ?? 'Job type',
                          onTap: () => _openFilters(state.params),
                        ),
                        const SizedBox(width: 8),
                        _FilterChipButton(
                          label: state.params.sort == 'relevance'
                              ? 'Sort'
                              : state.params.sort,
                          onTap: () => _openFilters(state.params),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            Expanded(
              child: state.loaded
                  ? AsyncValueView(
                      value: state.result,
                      isEmpty: (list) => list.items.isEmpty,
                      emptyMessage: 'No jobs match your search',
                      onRefresh: _runSearch,
                      builder: (context, list) => Scrollbar(
                        controller: _scrollController,
                        child: ListView.separated(
                          controller: _scrollController,
                          physics: const AlwaysScrollableScrollPhysics(),
                          padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
                          itemCount: list.items.length + (list.hasMore ? 1 : 0),
                          separatorBuilder: (_, __) => const SizedBox(height: 4),
                          itemBuilder: (context, i) {
                            if (i >= list.items.length) {
                              return const Padding(
                                padding: EdgeInsets.all(16),
                                child: Center(
                                  child: SizedBox(
                                    width: 24,
                                    height: 24,
                                    child: CircularProgressIndicator(strokeWidth: 2.5),
                                  ),
                                ),
                              );
                            }
                            return JobCard(job: list.items[i]);
                          },
                        ),
                      ),
                    )
                  : const _SearchPrompt(),
            ),
          ],
        ),
      ),
    );
  }
}

class _FilterChipButton extends StatelessWidget {
  const _FilterChipButton({
    required this.label,
    this.selected = false,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: selected ? AppColors.primary.withOpacity(0.25) : const Color(0x1AFFFFFF),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: selected ? AppColors.primary : AppColors.border,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (selected) ...[
              const Icon(Icons.check_rounded, size: 15, color: AppColors.accent),
              const SizedBox(width: 5),
            ],
            Text(
              label,
              style: TextStyle(
                color: selected ? AppColors.accent : AppColors.text,
                fontSize: 13,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SearchPrompt extends StatelessWidget {
  const _SearchPrompt();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.search_rounded, size: 56, color: AppColors.muted),
          const SizedBox(height: 16),
          const Text(
            'Find your next opportunity',
            style: TextStyle(color: AppColors.text, fontSize: 17, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 6),
          const Text(
            'Search for a role, company or skill above.\nUse the tune icon for advanced filters.',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.muted, fontSize: 13, height: 1.5),
          ),
          const SizedBox(height: 20),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            alignment: WrapAlignment.center,
            children: [
              'Flutter developer',
              'Product designer',
              'Remote',
              'Data analyst',
            ]
                .map(
                  (s) => ActionChip(
                    label: Text(s),
                    onPressed: () {},
                  ),
                )
                .toList(),
          ),
        ],
      ),
    );
  }
}

class _FilterSheet extends StatefulWidget {
  const _FilterSheet({required this.initial});

  final JobSearchParams initial;

  @override
  State<_FilterSheet> createState() => _FilterSheetState();
}

class _FilterSheetState extends State<_FilterSheet> {
  late bool _remote;
  late RangeValues _salary;
  late String _experience;
  late String _jobType;
  late String _sort;

  static const _experiences = ['', 'entry', 'junior', 'mid', 'senior', 'lead'];
  static const _experienceLabels = [
    'Any experience',
    'Entry level',
    'Junior',
    'Mid level',
    'Senior',
    'Lead / Manager',
  ];
  static const _jobTypes = ['', 'Full-time', 'Part-time', 'Contract', 'Internship', 'Freelance'];
  static const _sorts = [
    ('relevance', 'Most relevant'),
    ('date', 'Newest'),
    ('salary_desc', 'Salary: high to low'),
    ('salary_asc', 'Salary: low to high'),
  ];

  @override
  void initState() {
    super.initState();
    _remote = widget.initial.remote;
    _salary = RangeValues(
      widget.initial.salaryMin ?? 0,
      widget.initial.salaryMax ?? 250000,
    );
    _experience = widget.initial.experience ?? '';
    _jobType = widget.initial.jobType ?? '';
    _sort = widget.initial.sort;
  }

  void _apply() {
    Navigator.of(context).pop(
      JobSearchParams(
        query: widget.initial.query,
        remote: _remote,
        salaryMin: _salary.start <= 0 ? null : _salary.start,
        salaryMax: _salary.end >= 250000 ? null : _salary.end,
        experience: _experience.isEmpty ? null : _experience,
        jobType: _jobType.isEmpty ? null : _jobType,
        sort: _sort,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 24, 20, 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Text(
                  'Filters',
                  style: TextStyle(
                    color: AppColors.text,
                    fontSize: 20,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const Spacer(),
                TextButton(
                  onPressed: () => Navigator.of(context).pop(
                    const JobSearchParams(query: ''),
                  ),
                  child: const Text('Clear all'),
                ),
              ],
            ),
            const SizedBox(height: 8),
            SwitchListTile(
              value: _remote,
              onChanged: (v) => setState(() => _remote = v),
              activeTrackColor: AppColors.primary,
              title: const Text('Remote only'),
              subtitle: const Text('Show remote positions only'),
              contentPadding: EdgeInsets.zero,
            ),
            const SizedBox(height: 16),
            const Text(
              'Annual salary (USD)',
              style: TextStyle(color: AppColors.text, fontWeight: FontWeight.w600),
            ),
            RangeSlider(
              values: _salary,
              min: 0,
              max: 250000,
              divisions: 25,
              onChanged: (v) => setState(() => _salary = v),
              activeColor: AppColors.primary,
              inactiveColor: AppColors.border,
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  _salary.start <= 0 ? 'No minimum' : '\$${(_salary.start / 1000).round()}k',
                  style: const TextStyle(color: AppColors.muted, fontSize: 13),
                ),
                Text(
                  _salary.end >= 250000 ? 'No maximum' : '\$${(_salary.end / 1000).round()}k',
                  style: const TextStyle(color: AppColors.muted, fontSize: 13),
                ),
              ],
            ),
            const SizedBox(height: 20),
            _DropdownField<String>(
              label: 'Experience level',
              value: _experience,
              items: List.generate(_experiences.length, (i) {
                return DropdownMenuItem(
                  value: _experiences[i],
                  child: Text(_experienceLabels[i]),
                );
              }),
              onChanged: (v) => setState(() => _experience = v ?? ''),
            ),
            const SizedBox(height: 14),
            _DropdownField<String>(
              label: 'Job type',
              value: _jobType,
              items: [
                for (final t in _jobTypes)
                  DropdownMenuItem(value: t, child: Text(t.isEmpty ? 'Any type' : t)),
              ],
              onChanged: (v) => setState(() => _jobType = v ?? ''),
            ),
            const SizedBox(height: 14),
            _DropdownField<String>(
              label: 'Sort by',
              value: _sort,
              items: [
                for (final (value, label) in _sorts)
                  DropdownMenuItem(value: value, child: Text(label)),
              ],
              onChanged: (v) => setState(() => _sort = v ?? 'relevance'),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: _apply,
                child: const Text('Apply Filters'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _DropdownField<T> extends StatelessWidget {
  const _DropdownField({
    required this.label,
    required this.value,
    required this.items,
    required this.onChanged,
  });

  final String label;
  final T value;
  final List<DropdownMenuItem<T>> items;
  final ValueChanged<T?> onChanged;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(color: AppColors.text, fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 14),
          decoration: BoxDecoration(
            color: const Color(0x1AFFFFFF),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppColors.border),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<T>(
              value: value,
              isExpanded: true,
              dropdownColor: AppColors.surface,
              items: items,
              onChanged: onChanged,
              style: const TextStyle(color: AppColors.text, fontSize: 14),
              icon: const Icon(Icons.expand_more_rounded, color: AppColors.muted),
            ),
          ),
        ),
      ],
    );
  }
}