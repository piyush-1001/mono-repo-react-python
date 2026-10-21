import Foundation
import Network

/// Push-based connectivity watcher; the iOS counterpart of ConnectivityMonitor.kt.
///
/// `DeviceInfo`-style polling answers "are we online right now?", which is enough
/// to skip a doomed request but cannot say when the network comes back. This
/// reports transitions instead, so a failed sync can retry itself when
/// connectivity returns rather than waiting on the user.
///
/// Payload keys are deliberately identical to the Android monitor
/// (`online`, `metered`) so a single Dart listener can serve both platforms
/// without branching on which one it is running on.
final class NetworkMonitor {

    /// A snapshot of connectivity, shaped for the platform channel.
    typealias Handler = ([String: Any]) -> Void

    private let queue: DispatchQueue
    private var monitor: NWPathMonitor?
    private var handler: Handler?

    /// Last delivered state, used to swallow repeats. Path updates can fire for
    /// reasons that leave connectivity unchanged, and a Dart listener that
    /// retries on every event would retry on noise.
    private var lastOnline: Bool?
    private var lastMetered: Bool?

    init() {
        queue = DispatchQueue(label: "monorepo.connectivity.monitor")
    }

    /// Starts watching and delivers the current state straight away, so a
    /// listener never has to guess what it missed before it subscribed.
    ///
    /// Returns false only when a monitor is already running, which is a caller
    /// bug rather than a device failure; stop() first to replace the listener.
    @discardableResult
    func start(handler: @escaping Handler) -> Bool {
        if monitor != nil {
            stop()
        }

        // NWPathMonitor cannot be restarted once cancelled, so each start needs
        // a fresh instance instead of a reused one.
        let fresh = NWPathMonitor()
        // The handler is handed the monitor, not the path: the current state has
        // to be read back off it.
        fresh.pathUpdateHandler = { [weak self] source in
            self?.deliver(path: source.currentPath)
        }

        monitor = fresh
        self.handler = handler
        fresh.start(queue: queue)
        return true
    }

    func stop() {
        monitor?.cancel()
        monitor = nil
        handler = nil
        lastOnline = nil
        lastMetered = nil
    }

    // MARK: - Delivery

    private func deliver(path: NWPath) {
        let online = path.status == .satisfied
        // isExpensive covers cellular and personal-hotspot links, matching the
        // Android NET_CAPABILITY_NOT_METERED test. Callers may defer bulk work
        // on those.
        let metered = path.isExpensive

        if online == lastOnline && metered == lastMetered {
            return
        }
        lastOnline = online
        lastMetered = metered

        let payload: [String: Any] = ["online": online, "metered": metered]

        // Flutter's event sink must be called on the platform thread. The path
        // updates arrive on our own queue, so hop here and let callers assume a
        // single delivery thread.
        if Thread.isMainThread {
            handler?(payload)
        } else {
            DispatchQueue.main.async { [weak self] in
                self?.handler?(payload)
            }
        }
    }
}
