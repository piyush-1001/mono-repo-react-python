import Flutter
import Foundation

/// iOS half of the `monorepo/power_state` channel, mirroring
/// PowerStateChannel.kt on Android.
///
/// Reads Low Power Mode and thermal state off ProcessInfo. Both are invisible to
/// Dart and both are reasons to defer a sync rather than reasons it fails: Low
/// Power Mode restricts background activity, and a serious or critical thermal
/// state means the OS is already throttling to protect itself.
///
/// Neither read can fail and neither needs a permission or user authorisation,
/// so unlike a notification or location API there is no permission dance here -
/// the answer is always available, which is why this handler has no error path.
final class PowerStateHandler: NSObject {

    /// Must match PowerStateChannel.CHANNEL_NAME and the Dart constant.
    static let channelName = "monorepo/power_state"

    /// Flutter keeps the method-call handler weakly; this reference is what
    /// keeps it alive for the process. See the same note in Android's channels.
    private static var retained: PowerStateHandler?

    // MARK: - Dispatch

    func handle(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
        switch call.method {
        case "getPowerState":
            result(snapshot())
        default:
            result(FlutterMethodNotImplemented)
        }
    }

    /// Keys and vocabulary must match PowerState.fromMap and the Kotlin handler.
    private func snapshot() -> [String: Any] {
        let info = ProcessInfo.processInfo
        return [
            "powerSaveActive": info.isLowPowerModeEnabled,
            "thermal": thermalLabel(info.thermalState),
        ]
    }

    /// Maps iOS's four levels onto the shared five-value vocabulary.
    ///
    /// The mapping is one-to-one apart from Android having an extra `light`
    /// level, which iOS has no equivalent for; `unknown` is reserved for a
    /// handler that did not send the key at all. iOS reports `.nominal` when it
    /// has no thermal sensor, so this never invents an unknown on a real device.
    private func thermalLabel(_ state: ProcessInfo.ThermalState) -> String {
        switch state {
        case .nominal:
            return "nominal"
        case .fair:
            return "fair"
        case .serious:
            return "serious"
        case .critical:
            return "critical"
        @unknown default:
            // A future SDK case this build has not been rebuilt against. Idle is
            // the safer reading: it keeps the app syncing.
            return "unknown"
        }
    }

    // MARK: - Registration

    /// Call from `AppDelegate.registerChannelHandlers`, next to
    /// ConnectivityHandler.register.
    static func register(with messenger: FlutterBinaryMessenger) {
        let handler = PowerStateHandler()
        retained = handler

        let channel = FlutterMethodChannel(name: channelName, binaryMessenger: messenger)
        channel.setMethodCallHandler { call, result in
            handler.handle(call, result: result)
        }
    }
}
