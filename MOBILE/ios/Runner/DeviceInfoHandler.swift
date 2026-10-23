import Flutter
import Network
import UIKit

/// iOS half of the `monorepo/device_info` channel, mirroring
/// DeviceInfoChannel.kt on Android.
///
/// The mobile client asks before it hits the network: sending a ranking request
/// from a device that cannot reach either backend is a wasted round trip. Battery
/// level is not readable from Dart at all, hence a channel rather than a guess.
///
/// Channel name, method names, payload keys and the -1-for-unknown battery are
/// identical to the Kotlin handler, so `DeviceSnapshot.fromMap` serves both
/// platforms without asking which OS it is on.
final class DeviceInfoHandler: NSObject {

    /// Must match DeviceInfoChannel.CHANNEL_NAME and deviceChannelName in
    /// task_api_service.dart.
    static let channelName = "monorepo/device_info"

    /// Battery level that means "the platform would not say", matching Android's
    /// UNKNOWN. DeviceSnapshot.batteryUnknown tests for exactly this.
    private static let unknownBatteryPercent = -1

    /// Answers getConnectivity synchronously.
    ///
    /// NWPathMonitor cannot be restarted once cancelled, so this monitor is
    /// started for the life of the process and read through `currentPath`, rather
    /// than created per call and cancelled after answering.
    ///
    /// Deliberately separate from NetworkMonitor, which the connectivity *stream*
    /// owns and stops when Dart unsubscribes: a poll sharing it would report
    /// offline whenever nobody was subscribed.
    private let reachability = NWPathMonitor()
    private let reachabilityQueue = DispatchQueue(label: "monorepo.device_info.reachability")

    /// Flutter holds the method-call handler weakly; this reference is what keeps
    /// the channel answering. See the same note in PowerStateHandler.
    private static var retained: DeviceInfoHandler?

    override init() {
        super.init()

        reachability.start(queue: reachabilityQueue)

        // UIDevice reports batteryLevel as -1 until monitoring is switched on;
        // reading the getter does not enable it implicitly. Without this line
        // every battery check silently answers "unknown", and canSync then reads
        // a charged phone as un-syncable forever.
        UIDevice.current.isBatteryMonitoringEnabled = true
    }

    deinit {
        // Cancelling is terminal for this instance, which is fine: `retained`
        // means this deinit does not run in practice, and leaving a monitor
        // running past the handler's death would keep its queue alive for
        // nothing.
        reachability.cancel()
    }

    // MARK: - Dispatch

    func handle(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
        switch call.method {
        case "getDeviceInfo":
            result(snapshot())
        case "getBatteryPercent":
            result(batteryPercent())
        case "getConnectivity":
            result(isOnline())
        default:
            result(FlutterMethodNotImplemented)
        }
    }

    /// The three keys DeviceSnapshot.fromMap reads; it ignores anything else.
    private func snapshot() -> [String: Any] {
        return [
            "batteryPercent": batteryPercent(),
            "online": isOnline(),
            // UIDevice.model is the device *class* ("iPhone", "iPad"), not the
            // marketing name Android's Build.MODEL reports. The exact identifier
            // ("iPhone15,2") needs utsname().machine; nothing reads it today, so
            // this stays the coarse answer and the Dart default is 'unknown'.
            "model": UIDevice.current.model,
        ]
    }

    /// Whole percentage, or -1 when unavailable.
    ///
    /// batteryLevel is a 0...1 fraction, so the scaling happens here: the Dart
    /// side expects the same 0..100 integers Android's BATTERY_PROPERTY_CAPACITY
    /// gives it, and comparing a fraction against `> 5` in canSync would always
    /// be true.
    ///
    /// The simulator reports a full battery rather than -1, so a -1 here means a
    /// real device with monitoring unavailable, not "this is a simulator".
    private func batteryPercent() -> Int {
        let level = UIDevice.current.batteryLevel
        guard level >= 0 else { return Self.unknownBatteryPercent }
        return Int((level * 100).rounded())
    }

    /// True only while a satisfied path exists, the counterpart of Android's
    /// NET_CAPABILITY_INTERNET test.
    ///
    /// No permission can be refused, so this cannot fail the way Android's does
    /// with SecurityException. Its own weakness is timing: the first read can
    /// land before the monitor's first path update, when currentPath is optimistically
    /// satisfied. The next call is corrected, and the cost of a wrong yes is one
    /// failed request that reports itself honestly.
    private func isOnline() -> Bool {
        return reachability.currentPath.status == .satisfied
    }

    // MARK: - Registration

    /// Call from `AppDelegate.registerChannelHandlers`. Unregistered, the Dart
    /// side gets MissingPluginException and falls back to DeviceSnapshot
    /// ._unavailable(), which assumes online so a real failure still surfaces.
    static func register(with messenger: FlutterBinaryMessenger) {
        let handler = DeviceInfoHandler()
        retained = handler

        let channel = FlutterMethodChannel(name: channelName, binaryMessenger: messenger)
        channel.setMethodCallHandler { call, result in
            handler.handle(call, result: result)
        }
    }
}
