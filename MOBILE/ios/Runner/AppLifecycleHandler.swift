import Flutter
import UIKit

/// iOS half of the `monorepo/app_lifecycle` channel, mirroring
/// AppLifecycleChannel.kt on Android.
///
/// Reports whether the app is in the foreground, so Dart can stop refreshing
/// while it is away and refresh once the user comes back. Without this the
/// screen keeps whatever it fetched last, and the user returns to a ranking
/// that was true ten minutes ago and does not look stale.
///
/// The state comes from the app's own notifications rather than from a timer:
/// becoming active and resigning active are exactly the two moments the answer
/// changes, and they arrive whether the app was backgrounded, the screen was
/// locked, or a system sheet was presented.
///
/// The notifications are observed only between a subscribe and an unsubscribe,
/// so a Dart side that is not listening costs nothing.
final class AppLifecycleHandler: NSObject, FlutterStreamHandler {

    static let channelName = "monorepo/app_lifecycle"

    static let stateActive = "active"
    static let stateBackground = "background"

    private var sink: FlutterEventSink?

    // The last state that was sent. The notifications fire more often than the
    // state actually changes - a control centre pull resigns active and
    // becomes active again - and a Dart listener that reacted to every event
    // would re-fetch for a transition that went nowhere.
    private var lastState: String?

    private var observers: [NSObjectProtocol] = []

    // Flutter keeps only a weak reference to a stream handler, so a handler
    // nothing else holds can be collected and the channel then answers
    // nothing. This reference is what keeps it alive for the process.
    private static var retained: AppLifecycleHandler?

    deinit {
        stopObserving()
    }

    func onListen(withArguments arguments: Any?, eventSink events: @escaping FlutterEventSink) -> FlutterError? {
        sink = events
        startObserving()

        // The current state straight away, so a listener never has to guess:
        // Dart subscribes while the app is running, which means foreground.
        publish(state: AppLifecycleHandler.stateActive)
        return nil
    }

    func onCancel(withArguments arguments: Any?) -> FlutterError? {
        stopObserving()
        sink = nil
        lastState = nil
        return nil
    }

    private func startObserving() {
        guard observers.isEmpty else { return }

        let center = NotificationCenter.default

        observers.append(
            center.addObserver(
                forName: UIApplication.didBecomeActiveNotification,
                object: nil,
                queue: .main
            ) { [weak self] _ in
                self?.publish(state: AppLifecycleHandler.stateActive)
            }
        )

        observers.append(
            center.addObserver(
                forName: UIApplication.willResignActiveNotification,
                object: nil,
                queue: .main
            ) { [weak self] _ in
                self?.publish(state: AppLifecycleHandler.stateBackground)
            }
        )
    }

    private func stopObserving() {
        let center = NotificationCenter.default
        observers.forEach { center.removeObserver($0) }
        observers = []
    }

    /// Sends a state change to Dart, if there is one to send.
    ///
    /// The observers are delivered on the main queue, which is where an event
    /// sink has to be called.
    private func publish(state: String) {
        guard let sink = sink else { return }
        guard state != lastState else { return }
        lastState = state

        sink([
            "state": state,
            // Epoch milliseconds, the same unit the Dart side already uses for
            // the cache timestamp.
            "changedAt": Int(Date().timeIntervalSince1970 * 1000)
        ])
    }

    /// Registers the stream handler. Call from `AppDelegate.didFinishLaunching`,
    /// next to the other handlers.
    static func register(with messenger: FlutterBinaryMessenger) -> FlutterEventChannel {
        let handler = AppLifecycleHandler()
        retained = handler

        let channel = FlutterEventChannel(name: channelName, binaryMessenger: messenger)
        channel.setStreamHandler(handler)
        return channel
    }
}
