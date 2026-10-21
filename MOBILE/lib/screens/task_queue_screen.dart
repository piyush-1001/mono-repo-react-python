/// The mobile task queue: what the ranked list looks like on a phone.
///
/// Load order matters for how the screen feels on a flaky connection:
///   1. render the cache immediately, so the first frame is never empty
///   2. ask the backends for a fresh ranking
///   3. replace the list on success and store it; on failure keep showing the
///      cache and explain that it is stale instead of wiping it
///
/// Both services are injectable so the screen can be pumped in a widget test
/// without a network or an Android host.

import 'package:flutter/material.dart';

import '../services/offline_task_cache.dart';
import '../services/task_api_service.dart';

class TaskQueueScreen extends StatefulWidget {
  const TaskQueueScreen({super.key, this.api, this.cache});

  final TaskApiService? api;
  final OfflineTaskCache? cache;

  @override
  State<TaskQueueScreen> createState() => _TaskQueueScreenState();
}

class _TaskQueueScreenState extends State<TaskQueueScreen> {
  // Built lazily: initState needs the widget's constructor args to be settled,
  // and a late final field also lets dispose() tell owned from injected clients.
  late final TaskApiService _api = widget.api ?? TaskApiService();
  late final OfflineTaskCache _cache = widget.cache ?? const OfflineTaskCache();

  Ranking? _ranking;
  bool _showingCached = false;
  DateTime? _cachedAt;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load(startup: true);
  }

  @override
  void dispose() {
    // Only close a client this screen created; an injected one may be shared.
    if (widget.api == null) _api.close();
    super.dispose();
  }

  Future<void> _load({bool startup = false}) async {
    if (startup) {
      final cached = await _cache.read();
      if (!mounted) return;
      if (cached != null) {
        setState(() {
          _ranking = cached.ranking;
          _showingCached = true;
          _cachedAt = cached.savedAt;
        });
      }
    } else {
      // Pull-to-refresh keeps the current rows on screen rather than flashing
      // an empty list while the request is in flight.
      setState(() => _loading = true);
    }

    try {
      final fresh = await _api.rankedTasks();
      if (!mounted) return;
      setState(() {
        _ranking = fresh;
        _showingCached = false;
        _cachedAt = null;
        _error = null;
        _loading = false;
      });
      await _cache.write(fresh);
    } on ApiException catch (failure) {
      if (!mounted) return;
      setState(() {
        _error = failure.message;
        _loading = false;
      });
    } catch (failure) {
      // A malformed body arrives as a cast error, not an ApiException. Leaving
      // _error null here would spin the progress bar forever.
      if (!mounted) return;
      setState(() {
        _error = 'Unexpected response: $failure';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final tasks = _ranking?.ranked ?? const <Task>[];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Task Queue'),
        actions: <Widget>[
          IconButton(
            onPressed: _loading ? null : () => _load(),
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => _load(),
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.symmetric(vertical: 8),
          children: <Widget>[
            if (_error != null) _ErrorBanner(message: _error!, onRetry: _load),
            if (_showingCached && _cachedAt != null)
              _StaleBanner(savedAt: _cachedAt!, hasError: _error != null),
            if (_loading && tasks.isEmpty)
              const Padding(
                padding: EdgeInsets.all(32),
                child: Center(child: CircularProgressIndicator()),
              )
            else if (tasks.isEmpty)
              const _EmptyState()
            else
              ...List.generate(
                tasks.length,
                (index) => _TaskRow(
                  task: tasks[index],
                  position: index + 1,
                  isNext: tasks[index].id == _ranking?.nextTaskId,
                ),
              ),
          ],
        ),
      ),
    );
  }
}

/// One ranked task: rank, title, score bar, and why it scored that way.
class _TaskRow extends StatelessWidget {
  const _TaskRow({
    required this.task,
    required this.position,
    required this.isNext,
  });

  final Task task;
  final int position;
  final bool isNext;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final score = (task.score ?? 0).clamp(0, 100) / 100;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: isNext ? theme.colorScheme.primary : Colors.transparent,
        ),
      ),
      child: ListTile(
        leading: CircleAvatar(child: Text('$position')),
        title: Text(
          task.title,
          style: task.isDone
              ? const TextStyle(decoration: TextDecoration.lineThrough)
              : null,
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            if (isNext)
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Text(
                  'Do next',
                  style: theme.textTheme.labelSmall
                      ?.copyWith(color: theme.colorScheme.primary),
                ),
              ),
            Text(task.reasons.join(' · ')),
            LinearProgressIndicator(value: score),
          ],
        ),
        trailing: Text('${task.score ?? 0}'),
      ),
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  const _ErrorBanner({required this.message, required this.onRetry});

  final String message;
  final Future<void> Function() onRetry;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      color: theme.colorScheme.errorContainer,
      child: ListTile(
        leading: Icon(Icons.cloud_off, color: theme.colorScheme.onErrorContainer),
        title: Text(message, style: TextStyle(color: theme.colorScheme.onErrorContainer)),
        trailing: TextButton(onPressed: onRetry, child: const Text('Retry')),
      ),
    );
  }
}

/// Says the list is not current. Shown quietly after a successful load from
/// cache, and loudly when the refresh behind it also failed.
class _StaleBanner extends StatelessWidget {
  const _StaleBanner({required this.savedAt, required this.hasError});

  final DateTime savedAt;
  final bool hasError;

  String get _label {
    final age = DateTime.now().difference(savedAt);
    if (age.inMinutes < 1) return 'less than a minute ago';
    if (age.inMinutes < 60) return '${age.inMinutes} min ago';
    if (age.inHours < 24) return '${age.inHours} h ago';
    return '${age.inDays} d ago';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      child: ListTile(
        dense: true,
        leading: Icon(
          Icons.history,
          color: hasError ? theme.colorScheme.error : theme.hintColor,
        ),
        title: Text(
          hasError
              ? 'Showing saved tasks from $_label - could not refresh'
              : 'Showing saved tasks from $_label',
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.all(32),
      child: Center(
        child: Text('No tasks yet. Add one on the web app or in the task list.'),
      ),
    );
  }
}
