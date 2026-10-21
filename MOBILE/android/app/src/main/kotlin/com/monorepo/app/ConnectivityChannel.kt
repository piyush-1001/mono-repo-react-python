package com.monorepo.app

import android.content.Context
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.EventChannel

/**
 * Event channel half of the connectivity feature: turns [ConnectivityMonitor]
 * transitions into `monorepo/connectivity` events for Dart.
 *
 * An EventChannel rather than a MethodChannel because the useful signal is a
 * stream of changes with no caller waiting on each one: "Wi-Fi came back" is
 * worth acting on, and nobody asked.
 *
 * Events fire only between onListen and onCancel, which maps cleanly onto the
 * monitor's start/stop: a Dart side that is not listening costs nothing, and a
 * screen that goes away stops the underlying network callback.
 */
class ConnectivityChannel(context: Context) : EventChannel.StreamHandler {

    private val monitor = ConnectivityMonitor(context)

    override fun onListen(arguments: Any?, events: EventChannel.EventSink?) {
        if (events == null) {
            monitor.stop()
            return
        }

        // The monitor already hops to the main thread, which is where
        // EventSink.success must be called.
        val watching = monitor.start { payload -> events.success(payload) }
        if (!watching) {
            events.error(
                "UNAVAILABLE",
                "Connectivity monitoring is unavailable; check the ACCESS_NETWORK_STATE permission",
                null
            )
        }
    }

    override fun onCancel(arguments: Any?) {
        monitor.stop()
    }

    companion object {
        /** Must match the Dart EventChannel name; same value on iOS. */
        const val CHANNEL_NAME = "monorepo/connectivity"

        // Flutter keeps only a weak reference to a StreamHandler, so a handler
        // nothing else holds can be collected and the channel then answers
        // nothing. This reference is what keeps it alive for the process.
        private var registration: ConnectivityChannel? = null

        /**
         * Registers the stream handler. Call from
         * `MainActivity.configureFlutterEngine`, next to the method channels.
         */
        @JvmStatic
        fun registerWith(flutterEngine: FlutterEngine, context: Context): EventChannel {
            val handler = ConnectivityChannel(context)
            registration = handler
            val channel = EventChannel(
                flutterEngine.dartExecutor.binaryMessenger,
                CHANNEL_NAME
            )
            channel.setStreamHandler(handler)
            return channel
        }
    }
}
