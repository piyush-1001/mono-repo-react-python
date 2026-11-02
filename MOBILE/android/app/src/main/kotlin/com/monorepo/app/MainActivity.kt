package com.monorepo.app

import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine

/**
 * Host Activity for the Flutter app, and the only place platform channels get
 * registered.
 *
 * Extending FlutterActivity is not enough on its own: a channel declared on the
 * Dart side stays unanswered until a handler is attached to the engine here.
 * Without this override, `DeviceInfo.snapshot()` on the Dart side receives a
 * MissingPluginException and quietly reports an unknown battery, so the sync
 * pre-flight check silently stops doing anything useful.
 *
 * Dropping this file into a project still needs the usual Flutter host setup to
 * be present: the `flutterEmbedding: 2` meta-data and launcher intent filter in
 * AndroidManifest.xml, the package name matching this directory, and the
 * Flutter Gradle plugin applied in build.gradle.
 */
class MainActivity : FlutterActivity() {

    /**
     * Called once the engine exists but before Dart runs any business code, so
     * handlers registered here are in place for the first request the app makes.
     */
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        // Pass applicationContext rather than `this`. DeviceInfoChannel already
        // reduces whatever it receives to applicationContext, so this is belt
        // and braces; what matters is that the Activity is never captured,
        // because the channel outlives Activity recreation on rotation.
        DeviceInfoChannel.registerWith(flutterEngine, applicationContext)
        TaskCacheChannel.registerWith(flutterEngine, applicationContext)

        // The connectivity and power state channels were missing here. Both are
        // written on the Dart side as if they work, so an unregistered handler
        // is not a crash but a lie: the connectivity stream fails with
        // MissingPluginException instead of reporting reconnections, and the
        // power state reads "unknown" on a phone that is in battery saver.
        ConnectivityChannel.registerWith(flutterEngine, applicationContext)
        PowerStateChannel.registerWith(flutterEngine, applicationContext)

        // Tells Dart whether the app is in the foreground, so a ranking that
        // was fetched before the app went away can be refreshed when the user
        // comes back instead of being shown stale.
        AppLifecycleChannel.registerWith(flutterEngine, applicationContext)
    }
}
