import Flutter
import Foundation

/// iOS half of the `monorepo/task_cache` channel, mirroring
/// TaskCacheChannel.kt on Android.
///
/// Stores the last successful ranking so a phone with no reachable backend can
/// still show something. The payload is the ranking JSON exactly as Dart
/// serialised it; this side never parses it, so a change to the ranking shape
/// needs no migration here - the Dart reader rejects what it cannot decode and
/// reports "no cache".
///
/// Persistence is UserDefaults rather than a file: the payload is a few kilobytes
/// of task titles, and a file would add I/O plus a half-written-file failure mode
/// for nothing at this size. The data is sandboxed but not encrypted beyond the
/// device's own data protection, so nothing secret belongs in here - task titles
/// included.
final class TaskCacheHandler: NSObject {

    /// Must match TaskCacheChannel.CHANNEL_NAME and taskCacheChannelName in
    /// offline_task_cache.dart.
    static let channelName = "monorepo/task_cache"

    /// Mirrors Android's named SharedPreferences file: keeping the cache in its
    /// own suite separates it from anything else persisted, so clearing it cannot
    /// take unrelated defaults with it.
    private static let suiteName = "monorepo_task_cache"

    /// The single key both values live under. See the note in write(_:result:).
    private static let cacheKey = "ranking"
    private static let payloadKey = "payload"
    private static let savedAtKey = "savedAt"

    private let defaults: UserDefaults

    /// Flutter holds the method-call handler weakly; see PowerStateHandler.
    private static var retained: TaskCacheHandler?

    private override init() {
        // UserDefaults(suiteName:) returns nil only for a name the OS refuses,
        // which a plain identifier is not. Falling back to .standard rather than
        // force-unwrapping keeps the cache working in that case instead of
        // crashing the app on launch, at the cost of losing the isolation the
        // dedicated suite is for.
        defaults = UserDefaults(suiteName: Self.suiteName) ?? .standard
        super.init()
    }

    // MARK: - Dispatch

    func handle(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
        switch call.method {
        case "readCache":
            result(read())
        case "writeCache":
            write(call, result: result)
        case "clearCache":
            clear(result: result)
        default:
            result(FlutterMethodNotImplemented)
        }
    }

    /// Nil means "no cache", which is what first run and a cleared cache look
    /// like; Dart already treats nil as a reason to show the empty state.
    ///
    /// Both values travel in one reply, matching the Android handler and the note
    /// in offline_task_cache.dart: Dart must never see a payload paired with the
    /// previous write's timestamp.
    private func read() -> [String: String]? {
        guard let entry = defaults.dictionary(forKey: Self.cacheKey),
              let payload = entry[Self.payloadKey] as? String,
              !payload.isEmpty else {
            return nil
        }
        return [
            Self.payloadKey: payload,
            Self.savedAtKey: entry[Self.savedAtKey] as? String ?? "",
        ]
    }

    private func write(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
        let arguments = call.arguments as? [String: Any]

        guard let payload = arguments?[Self.payloadKey] as? String, !payload.isEmpty else {
            // Same code and reasoning as Android's EMPTY_PAYLOAD: an empty write
            // would silently destroy the only data the offline screen has, so it
            // is refused loudly and the previous cache survives.
            result(
                FlutterError(
                    code: "EMPTY_PAYLOAD",
                    message: "Refusing to overwrite the cache with nothing",
                    details: nil
                )
            )
            return
        }

        // A missing timestamp is recoverable - Dart falls back to epoch and labels
        // the data as very old - so it is not worth rejecting the write over.
        let savedAt = arguments?[Self.savedAtKey] as? String ?? ""

        // Payload and timestamp are stored as one dictionary under one key rather
        // than as two keys, because UserDefaults writes each key independently:
        // two set calls are two writes, and a read landing between them would
        // pair a new payload with the old timestamp. Android gets this for free,
        // since its SharedPreferences editor commits both keys in one apply().
        defaults.set(
            [Self.payloadKey: payload, Self.savedAtKey: savedAt],
            forKey: Self.cacheKey
        )

        // Always reports success. UserDefaults has no failure callback and its
        // writes are asynchronous, so unlike Android's apply() there is nothing
        // to catch here; the Dart write path ignores the reply either way.
        result(true)
    }

    private func clear(result: @escaping FlutterResult) {
        // removeObject(forKey:) cannot throw, so this handler has no counterpart
        // to Android's CLEAR_FAILED. Removing the one key clears both values,
        // which is another consequence of storing them together.
        defaults.removeObject(forKey: Self.cacheKey)
        result(true)
    }

    // MARK: - Registration

    /// Call from `AppDelegate.registerChannelHandlers`, next to
    /// DeviceInfoHandler.register. Unregistered, the Dart cache reports "no
    /// cached data" and the screen behaves as if it were the app's first run.
    static func register(with messenger: FlutterBinaryMessenger) {
        let handler = TaskCacheHandler()
        retained = handler

        let channel = FlutterMethodChannel(name: channelName, binaryMessenger: messenger)
        channel.setMethodCallHandler { call, result in
            handler.handle(call, result: result)
        }
    }
}
