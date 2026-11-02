/// Offline persistence for the task ranking.
///
/// A phone opened in a lift, on a train, or on a plane battery cannot reach
/// either backend, and an empty screen with a red error banner is a poor answer
/// when the app did successfully fetch a ranking five minutes ago. This cache
/// stores the last good ranking on the Android side, over the
/// `monorepo/task_cache` channel implemented in TaskCacheChannel.kt.
///
/// The cache deliberately mirrors the shape Task.fromJson / Ranking.fromJson
/// already parse (Node.js' camelCase `createdAt`), so a cached payload restores
/// through the same constructors as a live one. The Python ranker's snake_case
/// spelling is only for the outbound request and is not persisted here.
///
/// Every failure path returns null or swallows the error rather than throwing:
/// a missing cache is never a reason to break the screen.

import 'dart:convert';

import 'package:flutter/services.dart';

import 'task_api_service.dart';

const String taskCacheChannelName = 'monorepo/task_cache';

/// A ranking plus when it was written, so the UI can say how stale it is.
class CachedRanking {
  const CachedRanking({required this.ranking, required this.savedAt});

  final Ranking ranking;
  final DateTime savedAt;

  Duration get age => DateTime.now().difference(savedAt);

  bool get isOld => age.inMinutes >= 60;
}

class OfflineTaskCache {
  /// Production cache, bound to [taskCacheChannelName].
  const OfflineTaskCache() : channel = const MethodChannel(taskCacheChannelName);

  /// Test hook: drive the cache with a stubbed channel.
  const OfflineTaskCache.withChannel(this.channel);

  final MethodChannel channel;

  /// Last stored ranking, or null when there is none (first run, cleared data,
  /// or no platform handler registered).
  Future<CachedRanking?> read() async {
    try {
      // One call for both values: TaskCacheChannel returns them together so a
      // payload can never be paired with a stale timestamp.
      final entry =
          await channel.invokeMethod<Map<Object?, Object?>>('readCache');
      if (entry == null) return null;

      final payload = entry['payload'] as String?;
      if (payload == null || payload.isEmpty) return null;

      final decoded = jsonDecode(payload) as Map<String, dynamic>;

      return CachedRanking(
        ranking: Ranking.fromJson(decoded),
        // Corrupt or absent timestamps degrade to "epoch", which makes the UI
        // show the data as very old rather than hiding it.
        savedAt: DateTime.tryParse(entry['savedAt'] as String? ?? '') ??
            DateTime.fromMillisecondsSinceEpoch(0),
      );
    } on MissingPluginException {
      return null;
    } on PlatformException {
      return null;
    } on FormatException {
      // Written by an older build with an incompatible layout.
      return null;
    } on TypeError {
      // Decoded as JSON but not as a ranking: the fields this build expects are
      // missing. Treat it as no cache rather than failing the screen, which is
      // also what a future payload shape will do until it learns to migrate.
      return null;
    }
  }

  /// Stores [ranking] as the new fallback. Call after every successful fetch.
  Future<void> write(Ranking ranking) async {
    try {
      await channel.invokeMethod<void>('writeCache', <String, dynamic>{
        'payload': jsonEncode(_rankingToMap(ranking)),
        'savedAt': DateTime.now().toUtc().toIso8601String(),
      });
    } on MissingPluginException {
      // Nothing to do: running without the Android side wired up.
    } on PlatformException {
      // Disk full or prefs rejected the write. The live data is already on
      // screen, so losing only the fallback is acceptable.
    }
  }

  Future<void> clear() async {
    try {
      await channel.invokeMethod<void>('clearCache');
    } on MissingPluginException {
      return;
    } on PlatformException {
      return;
    }
  }

  // --- serialisation -------------------------------------------------------
  // Built from public fields rather than asking the models to serialise
  // themselves, so task_api_service.dart stays focused on HTTP.

  Map<String, dynamic> _rankingToMap(Ranking ranking) {
    return <String, dynamic>{
      'ranked': ranking.ranked.map(_taskToMap).toList(),
      'next_task_id': ranking.nextTaskId,
      'open_count': ranking.openCount,
      'duplicates': ranking.duplicates,
    };
  }

  Map<String, dynamic> _taskToMap(Task task) {
    return <String, dynamic>{
      'id': task.id,
      'title': task.title,
      'status': task.status,
      'priority': task.priority,
      'createdAt': task.createdAt,
      'score': task.score,
      'reasons': task.reasons,
    };
  }
}
