/// Power and thermal state, which decides whether a sync should run now.
///
/// Neither platform exposes this to Dart, and both act on it without asking:
/// iOS in Low Power Mode and Android in battery-saver mode restrict the work an
/// app may do in the background, so a sync started in that state may simply
/// never finish. A hot handset is the other case - the OS is throttling, and a
/// ranking request that adds to it is not worth the fraction of a second it
/// buys.
///
/// This is a pull, not a stream. Thermal state changes rarely enough that asking
/// before each sync is cheaper than maintaining a subscription, and unlike
/// connectivity there is no "it came back" moment worth reacting to - the caller
/// asks again on the next attempt anyway. `Connectivity` is the one that streams.
///
/// Channel `monorepo/power_state`, answered by PowerStateChannel.kt and
/// PowerStateHandler.swift.

import 'package:flutter/services.dart';

const String powerStateChannelName = 'monorepo/power_state';

/// Shared thermal vocabulary.
///
/// The two platforms use different enums, so each handler maps into these five
/// values and the Dart side never branches on the OS. The mapping is lossy on
/// Android on purpose: Android reports none/light/moderate/severe/critical and
/// iOS nominal/fair/serious/critical, and no distinction worth acting on
/// disappears under it.
enum ThermalState {
  nominal,
  fair,
  serious,
  critical,
  unknown;

  static ThermalState fromChannel(Object? value) {
    switch (value) {
      case 'nominal':
        return ThermalState.nominal;
      case 'fair':
        return ThermalState.fair;
      case 'serious':
        return ThermalState.serious;
      case 'critical':
        return ThermalState.critical;
      default:
        // Includes null, an older handler that does not send the key, and any
        // future value this build does not know. Unknown is treated as idle -
        // throttling is the exception, not the norm, and blocking every sync on
        // an unreadable flag would break the common case.
        return ThermalState.unknown;
    }
  }
}

class PowerState {
  const PowerState({
    required this.powerSaveActive,
    required this.thermal,
  });

  factory PowerState.fromMap(Map<Object?, Object?> map) {
    return PowerState(
      // Absent reads as "not in power save" for the same reason unknown thermal
      // reads as idle: the handler exists and is answering, so a missing key is
      // a version skew, not evidence of a restricted device.
      powerSaveActive: map['powerSaveActive'] == true,
      thermal: ThermalState.fromChannel(map['thermal']),
    );
  }

  /// Unavailable device, or a platform with no handler registered. Reports
  /// permissive so the app keeps working rather than refusing to sync forever.
  static const PowerState unknown = PowerState(
    powerSaveActive: false,
    thermal: ThermalState.unknown,
  );

  final bool powerSaveActive;
  final ThermalState thermal;

  /// True when the OS is actively discouraging background work, or is hot
  /// enough to be throttling. `unknown` never defers: a signal this side cannot
  /// read must not silently stop the app from doing its job.
  bool get shouldDeferSync =>
      powerSaveActive ||
      thermal == ThermalState.serious ||
      thermal == ThermalState.critical;

  @override
  String toString() =>
      'PowerState(powerSave: $powerSaveActive, thermal: ${thermal.name})';
}

/// Reads `monorepo/power_state`.
class PowerStateService {
  /// Production reader, bound to [powerStateChannelName].
  const PowerStateService()
      : channel = const MethodChannel(powerStateChannelName);

  /// Test hook: drive reads with a stubbed channel.
  const PowerStateService.withChannel(this.channel);

  final MethodChannel channel;

  /// Never throws. A missing handler or a platform error yields
  /// [PowerState.unknown], so callers can use the result directly in a decision
  /// instead of writing the same three catch blocks at every call site.
  Future<PowerState> read() async {
    try {
      final map = await channel.invokeMethod<Map<Object?, Object?>>(
        'getPowerState',
      );
      if (map == null) return PowerState.unknown;
      return PowerState.fromMap(map);
    } on MissingPluginException {
      return PowerState.unknown;
    } on PlatformException {
      return PowerState.unknown;
    }
  }
}
