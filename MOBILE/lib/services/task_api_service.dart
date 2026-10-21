/// Mobile client for the monorepo APIs.
///
/// Two backends are involved, exactly as on the web frontend:
///   * the Node.js task store (default http://localhost:3000)
///   * the Python FastAPI ranker  (default http://localhost:8000)
///
/// The file also declares the platform channel `monorepo/device_info`, whose
/// Android implementation lives in DeviceInfoChannel.kt. Reading battery level
/// and connectivity from the platform rather than from Dart keeps the service
/// usable on both a real device and an emulator, where the answers differ and
/// a hardcoded value would be misleading.
///
/// Only dart:io and Flutter core libraries are imported, so this compiles
/// without adding the `http` package to pubspec.yaml.

import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/services.dart';

const String deviceChannelName = 'monorepo/device_info';

/// Snapshot of the platform state a sync should not ignore.
class DeviceSnapshot {
  const DeviceSnapshot({
    required this.batteryPercent,
    required this.online,
    required this.model,
  });

  factory DeviceSnapshot.fromMap(Map<Object?, Object?> map) {
    return DeviceSnapshot(
      // -1 means the platform could not read the battery, which callers treat
      // as "unknown" rather than "empty".
      batteryPercent: (map['batteryPercent'] as num?)?.toInt() ?? -1,
      online: map['online'] as bool? ?? false,
      model: map['model'] as String? ?? 'unknown',
    );
  }

  final int batteryPercent;
  final bool online;
  final String model;

  bool get batteryUnknown => batteryPercent < 0;

  /// Cheap enough to call before every request: a low-battery, offline device
  /// should queue work instead of firing requests that will time out.
  bool get canSync => online && !batteryUnknown && batteryPercent > 5;

  @override
  String toString() =>
      'DeviceSnapshot($model, battery: $batteryPercent%, online: $online)';
}

/// Reads device state over the platform channel.
class DeviceInfo {
  /// The production reader, bound to [deviceChannelName].
  const DeviceInfo() : channel = const MethodChannel(deviceChannelName);

  /// Test hook: drive [snapshot] with a stubbed channel.
  const DeviceInfo.withChannel(this.channel);

  final MethodChannel channel;

  Future<DeviceSnapshot> snapshot() async {
    try {
      final raw = await channel.invokeMethod<Map<Object?, Object?>>(
        'getDeviceInfo',
      );
      if (raw == null) return _unavailable();
      return DeviceSnapshot.fromMap(raw);
    } on MissingPluginException {
      // The Android handler was never registered (unit tests, desktop runs).
      return _unavailable();
    } on PlatformException {
      return _unavailable();
    }
  }

  /// Unknown battery, but assume the network is fine so a request is still
  /// attempted and reports its real failure instead of silently skipping.
  static DeviceSnapshot _unavailable() =>
      const DeviceSnapshot(
        batteryPercent: -1,
        online: true,
        model: 'unknown',
      );
}

/// One task as stored by the Node.js API, plus the ranker's annotations.
class Task {
  const Task({
    required this.id,
    required this.title,
    required this.status,
    required this.priority,
    this.createdAt,
    this.score,
    this.reasons = const <String>[],
  });

  factory Task.fromJson(Map<String, dynamic> json) {
    return Task(
      id: (json['id'] as num).toInt(),
      title: json['title'] as String? ?? '',
      status: json['status'] as String? ?? 'pending',
      priority: json['priority'] as String? ?? 'medium',
      createdAt: json['createdAt'] as String?,
      score: (json['score'] as num?)?.toDouble(),
      reasons: (json['reasons'] as List<dynamic>?)
              ?.map((reason) => reason.toString())
              .toList() ??
          const <String>[],
    );
  }

  final int id;
  final String title;
  final String status;
  final String priority;
  final String? createdAt;
  final double? score;
  final List<String> reasons;

  bool get isDone => status == 'done';

  /// The shape the Python ranker expects: snake_case, and no nulls where the
  /// FastAPI model declares defaults.
  Map<String, dynamic> toRankPayload() {
    return <String, dynamic>{
      'id': id,
      'title': title,
      'status': status,
      'priority': priority,
      'created_at': createdAt,
    };
  }
}

/// Result of a ranking call.
class Ranking {
  const Ranking({
    required this.ranked,
    required this.nextTaskId,
    required this.openCount,
    required this.duplicates,
  });

  factory Ranking.fromJson(Map<String, dynamic> json) {
    final ranked = (json['ranked'] as List<dynamic>? ?? <dynamic>[])
        .map((task) => Task.fromJson(task as Map<String, dynamic>))
        .toList();
    final duplicates = (json['duplicates'] as List<dynamic>? ?? <dynamic>[])
        .map((pair) => pair as Map<String, dynamic>)
        .toList();
    return Ranking(
      ranked: ranked,
      nextTaskId: (json['next_task_id'] as num?)?.toInt(),
      openCount: (json['open_count'] as num?)?.toInt() ?? 0,
      duplicates: duplicates,
    );
  }

  final List<Task> ranked;
  final int? nextTaskId;
  final int openCount;
  final List<Map<String, dynamic>> duplicates;

  Task? get nextTask {
    for (final task in ranked) {
      if (task.id == nextTaskId) return task;
    }
    return null;
  }
}

/// Thrown for transport failures and non-2xx responses, with a message the UI
/// can show directly.
class ApiException implements Exception {
  const ApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => statusCode == null ? message : '$message (${statusCode})';
}

/// Talks to both backends.
class TaskApiService {
  TaskApiService({
    String tasksBaseUrl = 'http://localhost:3000',
    String mlBaseUrl = 'http://localhost:8000',
    HttpClient? httpClient,
    DeviceInfo deviceInfo = const DeviceInfo(),
    this.timeout = const Duration(seconds: 8),
  })  : tasksBaseUrl = tasksBaseUrl,
        mlBaseUrl = mlBaseUrl,
        deviceInfo = deviceInfo,
        _client = httpClient ?? HttpClient();

  final String tasksBaseUrl;
  final String mlBaseUrl;
  final DeviceInfo deviceInfo;
  final Duration timeout;
  final HttpClient _client;

  /// Tasks as stored, in insertion order.
  Future<List<Task>> fetchTasks() async {
    final body = await _get(Uri.parse('$tasksBaseUrl/api/tasks'));
    final decoded = jsonDecode(body) as Map<String, dynamic>;
    final tasks = decoded['tasks'] as List<dynamic>? ?? <dynamic>[];
    return tasks
        .map((task) => Task.fromJson(task as Map<String, dynamic>))
        .toList();
  }

  /// Sends the open and finished tasks to the Python ranker.
  Future<Ranking> rank(List<Task> tasks) async {
    final body = await _post(
      Uri.parse('$mlBaseUrl/api/rank-tasks'),
      <String, dynamic>{
        'tasks': tasks.map((task) => task.toRankPayload()).toList(),
      },
    );
    return Ranking.fromJson(jsonDecode(body) as Map<String, dynamic>);
  }

  /// Convenience for the mobile screen: fetch, then rank, in one call.
  Future<Ranking> rankedTasks() async {
    return rank(await fetchTasks());
  }

  /// Refuses to start a request the device cannot reasonably complete, so the
  /// caller can tell the user why nothing happened.
  Future<Ranking?> rankedTasksIfSyncable() async {
    final device = await deviceInfo.snapshot();
    if (!device.canSync) return null;
    return rankedTasks();
  }

  Future<String> _get(Uri uri) async {
    try {
      final request = await _client.getUrl(uri).timeout(timeout);
      request.headers.accept = 'application/json';
      return await _response(request.close(), timeout, uri);
    } on SocketException {
      throw ApiException('Cannot reach ${uri.host}:${uri.port}');
    } on TimeoutException {
      throw ApiException('Timed out talking to ${uri.path}', statusCode: null);
    }
  }

  Future<String> _post(Uri uri, Map<String, dynamic> payload) async {
    try {
      // Encode once: contentLength must be the byte count, not the character
      // count, which differs as soon as a task title has a non-ASCII character.
      final bytes = utf8.encode(jsonEncode(payload));
      final request = await _client.postUrl(uri).timeout(timeout);
      request.headers.contentType = ContentType.json;
      request.headers.contentLength = bytes.length;
      request.add(bytes);
      return await _response(request.close(), timeout, uri);
    } on SocketException {
      throw ApiException('Cannot reach ${uri.host}:${uri.port}');
    } on TimeoutException {
      throw ApiException('Timed out talking to ${uri.path}', statusCode: null);
    }
  }

  Future<String> _response(
    Future<HttpClientResponse> responseFuture,
    Duration timeout,
    Uri uri,
  ) async {
    final response = await responseFuture.timeout(timeout);
    final body = await utf8.decoder.bind(response).join();
    if (response.statusCode < 200 || response.statusCode >= 300) {
      // FastAPI reports the reason in `detail`; Node.js uses `error`.
      var message = 'Request to ${uri.path} failed';
      try {
        final decoded = jsonDecode(body) as Map<String, dynamic>;
        message = (decoded['detail'] ?? decoded['error'] ?? message).toString();
      } on FormatException {
        if (body.trim().isNotEmpty) message = body.trim();
      }
      throw ApiException(message, statusCode: response.statusCode);
    }
    return body;
  }

  void close() => _client.close(force: true);
}
