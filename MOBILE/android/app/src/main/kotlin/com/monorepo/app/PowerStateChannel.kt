package com.monorepo.app

import android.content.Context
import android.os.Build
import android.os.PowerManager
import android.util.Log
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel

/**
 * Android half of the `monorepo/power_state` channel declared in
 * `MOBILE/lib/services/power_state_service.dart`.
 *
 * Reports battery-saver mode and thermal status, neither of which Dart can read.
 * Both are reasons to hold off on a sync rather than reasons it will fail: in
 * battery saver the OS restricts background work, so a request may never
 * complete, and at high thermal status the device is already throttling.
 *
 * Neither signal needs a permission, which is why this handler can answer on any
 * device. Anything it cannot read reports "unknown"/false rather than erroring,
 * because the Dart side treats an unreadable signal as permissive - a device
 * that will not say it is hot should still sync.
 */
class PowerStateChannel(context: Context) : MethodChannel.MethodCallHandler {

    private val appContext: Context = context.applicationContext
    private val powerManager: PowerManager? =
        appContext.getSystemService(Context.POWER_SERVICE) as? PowerManager

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        when (call.method) {
            "getPowerState" -> result.success(snapshot())
            else -> result.notImplemented()
        }
    }

    /** Keys and vocabulary must match PowerState.fromMap and the Swift handler. */
    private fun snapshot(): Map<String, Any> = mapOf(
        "powerSaveActive" to powerSaveActive(),
        "thermal" to thermalLabel()
    )

    private fun powerSaveActive(): Boolean {
        return try {
            powerManager?.isPowerSaveMode ?: false
        } catch (error: Exception) {
            Log.w(TAG, "Battery saver state unavailable", error)
            false
        }
    }

    /**
     * Maps Android's thermal levels onto the shared five-value vocabulary.
     *
     * The `>= SEVERE` arm rather than naming every constant keeps this compiling
     * against older SDKs, which do not define EMERGENCY or SHUTDOWN, while still
     * treating them as critical when present: the numeric order is
     * NONE 0, LIGHT 1, MODERATE 2, SEVERE 3, CRITICAL 4, EMERGENCY 5, SHUTDOWN 6.
     */
    private fun thermalLabel(): String {
        val manager = powerManager ?: return THERMAL_UNKNOWN

        // thermalStatus only exists from API 29; older devices have no
        // equivalent, which is genuinely unknown rather than nominal.
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) return THERMAL_UNKNOWN

        return try {
            // Read once: the status can change between calls, and four separate
            // reads could compare four different values in one `when`.
            val status = manager.thermalStatus
            when {
                status == PowerManager.THERMAL_STATUS_NONE -> THERMAL_NOMINAL
                status == PowerManager.THERMAL_STATUS_LIGHT -> THERMAL_FAIR
                status == PowerManager.THERMAL_STATUS_MODERATE -> THERMAL_SERIOUS
                status >= PowerManager.THERMAL_STATUS_SEVERE -> THERMAL_CRITICAL
                else -> THERMAL_UNKNOWN
            }
        } catch (error: Exception) {
            // Some ROMs throw from this getter on devices with no thermal sensor.
            Log.w(TAG, "Thermal status unavailable", error)
            THERMAL_UNKNOWN
        }
    }

    companion object {
        private const val TAG = "PowerStateChannel"

        private const val THERMAL_NOMINAL = "nominal"
        private const val THERMAL_FAIR = "fair"
        private const val THERMAL_SERIOUS = "serious"
        private const val THERMAL_CRITICAL = "critical"
        private const val THERMAL_UNKNOWN = "unknown"

        /** Must match powerStateChannelName in power_state_service.dart. */
        const val CHANNEL_NAME = "monorepo/power_state"

        // MethodChannel holds its handler weakly; see DeviceInfoChannel.
        private var registration: PowerStateChannel? = null

        /** Register from `MainActivity.configureFlutterEngine`. */
        @JvmStatic
        fun registerWith(flutterEngine: FlutterEngine, context: Context): MethodChannel {
            val channel = MethodChannel(
                flutterEngine.dartExecutor.binaryMessenger,
                CHANNEL_NAME
            )
            val handler = PowerStateChannel(context)
            registration = handler
            channel.setMethodCallHandler(handler)
            return channel
        }
    }
}
