package com.monorepo.app

import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.util.Log
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel

/**
 * Android half of the `monorepo/api_endpoints` channel.
 *
 * Answers the one question the Dart side cannot answer about the device it is
 * running on: where the two backends are. `task_api_service.dart` defaults both
 * base URLs to `http://localhost:...`, which on Android means the phone itself.
 * On a physical device nothing is listening there, and on the emulator nothing
 * is listening there either - the host machine is reachable as `10.0.2.2`, not
 * as `localhost`. Every request therefore fails on both, and the failure looks
 * like a dead backend rather than a wrong host.
 *
 * Resolution order, first match wins:
 *
 *  1. `<meta-data>` on the `<application>` element in AndroidManifest.xml, for a
 *     developer running the backends on their own machine:
 *
 *         <meta-data
 *             android:name="com.monorepo.app.TASKS_API_URL"
 *             android:value="http://192.168.1.20:3000" />
 *         <meta-data
 *             android:name="com.monorepo.app.ML_API_URL"
 *             android:value="http://192.168.1.20:8000" />
 *
 *     The keys are read, not required: with neither present the defaults below
 *     apply, so adding this channel does not make the manifest harder to keep.
 *  2. The emulator loopback alias, when the device looks like an emulator.
 *  3. `localhost`, which is what the Dart side already assumes. A physical
 *     device with no override lands here and fails; reporting a made-up host
 *     would only make the failure harder to read.
 *
 * Add a note about cleartext while changing this file: network_security_config.xml
 * permits it for `10.0.2.2` and `localhost` only. A LAN address from step one is
 * refused by that policy until the same address is added there, so a meta-data
 * override that points at a phone's own network needs both edits.
 */
class ApiEndpointsChannel(context: Context) : MethodChannel.MethodCallHandler {

    private val appContext: Context = context.applicationContext

    /**
     * Resolved once. Neither the manifest nor the emulator-ness of a device
     * changes while the process is alive, so this reads the package manager a
     * single time instead of on every request the Dart side makes.
     */
    private val endpoints: Map<String, Any> by lazy { resolve() }

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        when (call.method) {
            "getEndpoints" -> result.success(endpoints)
            "getTasksBaseUrl" -> result.success(endpoints[KEY_TASKS])
            "getMlBaseUrl" -> result.success(endpoints[KEY_ML])
            "isEmulator" -> result.success(looksLikeEmulator())
            else -> result.notImplemented()
        }
    }

    private fun resolve(): Map<String, Any> {
        val fromManifest = manifestOverrides()
        val emulator = looksLikeEmulator()

        val source = when {
            fromManifest.isNotEmpty() -> SOURCE_MANIFEST
            emulator -> SOURCE_EMULATOR
            else -> SOURCE_DEFAULT
        }

        val fallbackHost = if (emulator) EMULATOR_HOST else LOCAL_HOST

        val tasks = normalise(
            fromManifest[KEY_TASKS] ?: "http://$fallbackHost:$TASKS_PORT"
        )
        val ml = normalise(
            fromManifest[KEY_ML] ?: "http://$fallbackHost:$ML_PORT"
        )

        // The host a build actually dialed is the first thing worth knowing when
        // a request fails, so it is logged once here rather than per request.
        Log.i(TAG, "API endpoints ($source): tasks=$tasks ml=$ml")

        return mapOf(
            KEY_TASKS to tasks,
            KEY_ML to ml,
            // Which rule answered, so a screen can explain itself instead of
            // showing a URL the user cannot interpret.
            "resolvedFrom" to source,
            "emulator" to emulator
        )
    }

    /**
     * Reads the optional `<meta-data>` overrides off the application element.
     *
     * Returns an empty map rather than nulls for absent keys, so the caller can
     * ask "did anything override?" in one test instead of two.
     */
    private fun manifestOverrides(): Map<String, String> {
        val bundle = try {
            val info = appContext.packageManager.getApplicationInfo(
                appContext.packageName,
                PackageManager.GET_META_DATA
            )
            // getApplicationInfo leaves metaData null when no meta-data is
            // declared at all; loadMetaData returns an empty bundle in that case.
            info.metaData ?: info.loadMetaData(appContext.resources)
        } catch (error: Exception) {
            // Only a failure to read this app's own package info, which leaves
            // the emulator and localhost rules to answer.
            Log.w(TAG, "Could not read manifest meta-data; using defaults", error)
            return emptyMap()
        }

        val overrides = mutableMapOf<String, String>()
        for (key in listOf(META_TASKS, META_ML)) {
            // getString returns null for an absent key, and an empty value is
            // how a developer disables an override without deleting it.
            val value = bundle?.getString(key)?.trim()
            if (!value.isNullOrEmpty()) {
                val name = if (key == META_TASKS) KEY_TASKS else KEY_ML
                overrides[name] = value
            }
        }
        return overrides
    }

    /**
     * Trims a trailing slash and adds the scheme when it was left out.
     *
     * A base URL ending in `/` produces `//api/tasks` once the Dart side appends
     * its path, which is a request to the wrong host rather than an obvious
     * mistake. A missing scheme is the other common slip, and adding `http://`
     * is what most people meant.
     */
    private fun normalise(url: String): String {
        var value = url.trim().trimEnd('/')
        if (!value.contains("://")) {
            value = "http://$value"
        }
        return value
    }

    companion object {
        private const val TAG = "ApiEndpointsChannel"

        /** Payload keys the Dart side reads. */
        private const val KEY_TASKS = "tasksBaseUrl"
        private const val KEY_ML = "mlBaseUrl"

        /** Optional `<meta-data>` names, set on the `<application>` element. */
        private const val META_TASKS = "com.monorepo.app.TASKS_API_URL"
        private const val META_ML = "com.monorepo.app.ML_API_URL"

        /** The emulator's alias for the host machine's loopback interface. */
        private const val EMULATOR_HOST = "10.0.2.2"
        private const val LOCAL_HOST = "localhost"

        /** Match the Dart defaults in task_api_service.dart. */
        private const val TASKS_PORT = 3000
        private const val ML_PORT = 8000

        private const val SOURCE_MANIFEST = "manifest"
        private const val SOURCE_EMULATOR = "emulator"
        private const val SOURCE_DEFAULT = "default"

        /** Must match the Dart channel name; there is no iOS peer yet. */
        const val CHANNEL_NAME = "monorepo/api_endpoints"

        // MethodChannel keeps only a weak reference to its handler, so a handler
        // nothing else points at can be collected and the channel then stops
        // answering. This reference is what keeps it alive for the process.
        private var registration: ApiEndpointsChannel? = null

        /**
         * Wires the channel into a running Flutter engine. Call this from
         * `MainActivity.configureFlutterEngine`; without it the Dart side gets a
         * MissingPluginException and keeps the hardcoded localhost URLs.
         */
        @JvmStatic
        fun registerWith(flutterEngine: FlutterEngine, context: Context): MethodChannel {
            val channel = MethodChannel(
                flutterEngine.dartExecutor.binaryMessenger,
                CHANNEL_NAME
            )
            val handler = ApiEndpointsChannel(context)
            registration = handler
            channel.setMethodCallHandler(handler)
            return channel
        }

        /**
         * Best guess at whether this is an emulator, so the host machine can be
         * reached as `10.0.2.2`.
         *
         * `Build.isEmulator` exists from API 30 and is the honest answer when it
         * is available. Below that there is nothing to ask, only signs to read -
         * the goldfish/ranchu hardware names, the generic fingerprint, the SDK
         * product names - and some third-party emulators hide all of them. A
         * wrong answer here is a failed request against localhost, which the app
         * already survives; there is no point pretending the guess is certain.
         */
        private fun looksLikeEmulator(): Boolean {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                return Build.isEmulator
            }

            val fingerprint = Build.FINGERPRINT ?: ""
            val hardware = Build.HARDWARE ?: ""
            val manufacturer = Build.MANUFACTURER ?: ""
            val model = Build.MODEL ?: ""
            val product = Build.PRODUCT ?: ""

            return fingerprint.startsWith("generic") ||
                fingerprint.startsWith("unknown") ||
                fingerprint.contains("vbox") ||
                hardware.contains("goldfish") ||
                hardware.contains("ranchu") ||
                hardware == "vmw_telephony" ||
                manufacturer.contains("genymotion", ignoreCase = true) ||
                model.contains("google_sdk") ||
                model.contains("Emulator") ||
                model.contains("Android SDK built for") ||
                product.contains("sdk_gphone") ||
                product == "sdk" ||
                product == "google_sdk"
        }
    }
}
