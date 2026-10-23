import Flutter
import Foundation

/// iOS event-channel half of connectivity reporting, mirroring
/// ConnectivityChannel.kt on Android.
///
/// Channel name, payload keys and semantics are identical across the two
/// platforms, so the Dart side consumes one EventChannel and never asks which OS
/// it is on. Events are delivered on the main thread by NetworkMonitor, which is
/// what FlutterEventChannel requires.
///
/// Wire it up from AppDelegate after the engine exists:
///
///     override func application(
///         _ application: UIApplication,
///         didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
///     ) -> Bool {
///         if let controller = window?.rootViewController as? FlutterViewController {
///             ConnectivityHandler.register(with: controller.binaryMessenger)
///         }
///         return super.application(application, didFinishLaunchingWithOptions: launchOptions)
///     }
final class ConnectivityHandler: NSObject, FlutterStreamHandler {

    /// Must match ConnectivityChannel.CHANNEL_NAME and the Dart EventChannel.
    static let channelName = "monorepo/connectivity"

    private let monitor: NetworkMonitor
    private var sink: FlutterEventSink?

    /// Flutter holds the stream handler weakly, so a handler referenced only by
    /// the channel can be deallocated and the stream then goes silent. This
    /// strong reference is the reason the channel keeps answering.
    private static var retained: ConnectivityHandler?

    /// Injectable so tests can drive it with a fake monitor and assert on the
    /// events without real network transitions.
    init(monitor: NetworkMonitor = NetworkMonitor()) {
        self.monitor = monitor
    }

    // MARK: - FlutterStreamHandler

    func onSubscribe(
        with sink: FlutterEventSink?,
        from arguments: Any?
    ) -> FlutterError? {
        self.sink = sink

        guard let sink = sink else {
            // Dart unsubscribed mid-call; make sure no callback is left running.
            monitor.stop()
            return nil
        }

        // No failure to report here. NWPathMonitor needs no entitlement or user
        // permission, so start() cannot be refused the way Android's
        // registerNetworkCallback throws SecurityException without
        // ACCESS_NETWORK_STATE. Reporting UNAVAILABLE from a branch that cannot
        // run would give Dart a surface to handle that never fires on iOS, while
        // the Android side does fire it - the asymmetry is Android's to express.
        monitor.start { [weak self] payload in
            // A delivery already queued on the main thread can arrive after
            // onUnsubscribe cleared the sink, so re-check before emitting.
            guard self?.sink != nil else { return }
            sink(payload)
        }
        return nil
    }

    func onUnsubscribe(with arguments: Any?) -> FlutterError? {
        monitor.stop()
        sink = nil
        return nil
    }

    // MARK: - Registration

    static func register(with messenger: FlutterBinaryMessenger) {
        let handler = ConnectivityHandler()
        retained = handler

        let channel = FlutterEventChannel(name: channelName, binaryMessenger: messenger)
        channel.setStreamHandler(handler)
    }
}
