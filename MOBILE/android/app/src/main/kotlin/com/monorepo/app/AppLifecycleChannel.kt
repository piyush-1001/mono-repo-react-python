package com.monorepo.app

import android.app.Activity
import android.app.Application
import android.content.Context
import android.os.Bundle
import android.util.Log
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.EventChannel

/**
 * Android half of the `monorepo/app_lifecycle` channel.
 *
 * Reports whether the app is in the foreground, so Dart can stop refreshing
 * while it is away and refresh once the user comes back. Without this the
 * screen keeps whatever it fetched last, and the user returns to a ranking
 * that was true ten minutes ago and does not look stale.
 *
 * The events come from the platform's own activity callbacks rather than from a
 * timer: onResume and onPause are exactly the two moments the answer changes,
 * and they arrive whether the app was backgrounded, the screen was locked, or
 * another activity was stacked on top.
 *
 * The events fire only between onListen and onCancel, so a Dart side that is
 * not listening costs nothing - the callbacks are unregistered with it.
 */
class AppLifecycleChannel(context: Context) : EventChannel.StreamHandler {

    private val appContext: Context = context.applicationContext

    private var sink: EventChannel.EventSink? = null

    // The last state that was sent. The activity callbacks fire more often
    // than the state actually changes - a rotation resumes and pauses again -
    // and a Dart listener that reacts to every event would re-fetch for a
    // transition that went nowhere.
    private var lastState: String? = null

    private var callbacks: Application.ActivityLifecycleCallbacks? = null

    override fun onListen(arguments: Any?, events: EventChannel.EventSink?) {
        if (events == null) {
            stop()
            return
        }
        sink = events

        val application = appContext as? Application
        if (application == null) {
            Log.w(TAG, "No Application context; app lifecycle events are unavailable")
            events.error(
                "UNAVAILABLE",
                "App lifecycle monitoring is unavailable; no Application context",
                null
            )
            return
        }

        if (callbacks == null) {
            val registered = object : Application.ActivityLifecycleCallbacks {
                override fun onActivityResumed(activity: Activity) = publish(STATE_ACTIVE)

                override fun onActivityPaused(activity: Activity) = publish(STATE_BACKGROUND)

                override fun onActivityCreated(activity: Activity, savedInstanceState: Bundle?) = Unit
                override fun onActivityStarted(activity: Activity) = Unit
                override fun onActivityStopped(activity: Activity) = Unit
                override fun onActivitySaveInstanceState(activity: Activity, outState: Bundle) = Unit
                override fun onActivityDestroyed(activity: Activity) = Unit
            }
            application.registerActivityLifecycleCallbacks(registered)
            callbacks = registered
        }

        // The current state straight away, so a listener never has to guess:
        // Dart subscribes while the app is running, which means foreground.
        publish(STATE_ACTIVE)
    }

    override fun onCancel(arguments: Any?) {
        stop()
    }

    /**
     * Sends a state change to Dart, if there is one to send.
     *
     * The activity callbacks arrive on the main thread, which is where
     * EventSink.success has to be called.
     */
    private fun publish(state: String) {
        if (state == lastState) return
        lastState = state
        sink?.success(
            mapOf(
                "state" to state,
                // Epoch milliseconds, the same unit the Dart side already uses
                // for the cache timestamp.
                "changedAt" to System.currentTimeMillis()
            )
        )
    }

    private fun stop() {
        (appContext as? Application)?.let { application ->
            callbacks?.let { application.unregisterActivityLifecycleCallbacks(it) }
        }
        callbacks = null
        sink = null
        lastState = null
    }

    companion object {
        private const val TAG = "AppLifecycleChannel"

        /** Must match the Dart EventChannel name; same value on iOS. */
        const val CHANNEL_NAME = "monorepo/app_lifecycle"

        const val STATE_ACTIVE = "active"
        const val STATE_BACKGROUND = "background"

        // Flutter keeps only a weak reference to a StreamHandler, so a handler
        // nothing else holds can be collected and the channel then answers
        // nothing. This reference is what keeps it alive for the process.
        private var registration: AppLifecycleChannel? = null

        /**
         * Registers the stream handler. Call from
         * `MainActivity.configureFlutterEngine`, next to the method channels.
         */
        @JvmStatic
        fun registerWith(flutterEngine: FlutterEngine, context: Context): EventChannel {
            val handler = AppLifecycleChannel(context)
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
