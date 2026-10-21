package com.monorepo.app

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.os.BatteryManager
import android.os.Build
import android.util.Log
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel

/**
 * Android half of the `monorepo/device_info` platform channel declared in
 * `MOBILE/lib/services/task_api_service.dart`.
 *
 * The mobile client asks before it hits the network: sending a task ranking
 * request over an unreachable API on a nearly-dead battery is a wasted round
 * trip and a bad user experience. Battery level and connectivity can only be
 * answered by the platform, hence this channel instead of a Dart guess.
 *
 * Every read is defensive: a permission-less or emulator-only build should
 * report "unknown" (-1 / false) rather than crash the Dart side.
 */
class DeviceInfoChannel(context: Context) : MethodChannel.MethodCallHandler {

    // Hold the application context, never the Activity: the channel can outlive
    // an Activity recreation and leaking one is a memory leak.
    private val appContext: Context = context.applicationContext

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        when (call.method) {
            "getDeviceInfo" -> result.success(snapshot())
            "getBatteryPercent" -> result.success(batteryPercent())
            "getConnectivity" -> result.success(isOnline())
            else -> result.notImplemented()
        }
    }

    /** Mirrors the keys DeviceSnapshot.fromMap reads on the Dart side. */
    private fun snapshot(): Map<String, Any> = mapOf(
        "batteryPercent" to batteryPercent(),
        "online" to isOnline(),
        "model" to Build.MODEL
    )

    /**
     * Remaining battery as a whole percentage, or -1 when unavailable.
     *
     * Uses BatteryManager's property API rather than the ACTION_BATTERY_CHANGED
     * receiver, which needs no permission and is not deprecated on recent API
     * levels.
     */
    private fun batteryPercent(): Int {
        return try {
            val manager = appContext.getSystemService(Context.BATTERY_SERVICE)
                as? BatteryManager
            // BATTERY_PROPERTY_CAPACITY is already a 0..100 percentage.
            manager?.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY) ?: UNKNOWN
        } catch (error: Exception) {
            Log.w(TAG, "Battery level unavailable", error)
            UNKNOWN
        }
    }

    /**
     * True only when a network is both active and declares internet access.
     *
     * Checking activeNetwork alone reports true on emulators and on Wi-Fi
     * networks with no upstream connectivity, which would defeat the whole
     * point of pre-flight checking.
     */
    private fun isOnline(): Boolean {
        return try {
            val manager = appContext.getSystemService(Context.CONNECTIVITY_SERVICE)
                as? ConnectivityManager
            val capabilities = manager?.activeNetwork
                ?.let { manager.getNetworkCapabilities(it) }
            capabilities
                ?.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
                ?: false
        } catch (error: Exception) {
            // The ACCESS_NETWORK_STATE permission is missing, or the call threw
            // on an unusual ROM. Assume offline so the caller defers the sync.
            Log.w(TAG, "Connectivity check failed", error)
            false
        }
    }

    companion object {
        private const val TAG = "DeviceInfoChannel"
        private const val UNKNOWN = -1

        /** Must match deviceChannelName in task_api_service.dart. */
        const val CHANNEL_NAME = "monorepo/device_info"

        // MethodChannel keeps only a weak reference to its handler, so a handler
        // nothing else points at can be collected and the channel then stops
        // answering. This reference is what keeps it alive for the process.
        private var registration: DeviceInfoChannel? = null

        /**
         * Wires the channel into a running Flutter engine. Call this from
         * `MainActivity.configureFlutterEngine`; without it the Dart side gets
         * a MissingPluginException and falls back to its defaults.
         */
        @JvmStatic
        fun registerWith(flutterEngine: FlutterEngine, context: Context): MethodChannel {
            val channel = MethodChannel(
                flutterEngine.dartExecutor.binaryMessenger,
                CHANNEL_NAME
            )
            val handler = DeviceInfoChannel(context)
            registration = handler
            channel.setMethodCallHandler(handler)
            return channel
        }
    }
}
