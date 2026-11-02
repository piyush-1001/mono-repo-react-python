package com.monorepo.app

import android.content.Context
import android.content.SharedPreferences
import android.util.Log
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel

/**
 * Android half of the `monorepo/task_cache` platform channel declared in
 * `MOBILE/lib/services/offline_task_cache.dart`.
 *
 * Stores the last successful task ranking so the app can show something useful
 * when neither backend is reachable. The payload is the ranking JSON exactly as
 * Dart serialised it; this side never parses it, so a change to the ranking
 * shape needs no migration on the Android side - the Dart reader rejects what
 * it cannot decode and reports "no cache".
 *
 * Persistence is SharedPreferences rather than a file: the payload is a few
 * kilobytes of task titles, `apply()` already writes off the main thread, and
 * the editor commits the two keys together. A file would add I/O and a
 * half-written-file failure mode for no benefit at this size.
 *
 * MODE_PRIVATE keeps the data inside this app's sandbox. It is not encrypted, so
 * nothing secret belongs in here - task titles included.
 */
class TaskCacheChannel(context: Context) : MethodChannel.MethodCallHandler {

    // applicationContext: the channel can outlive the Activity that created it.
    private val prefs: SharedPreferences = context.applicationContext
        .getSharedPreferences(PREFERENCES_NAME, Context.MODE_PRIVATE)

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        when (call.method) {
            "readCache" -> result.success(read())
            "writeCache" -> write(call, result)
            "clearCache" -> clear(result)
            else -> result.notImplemented()
        }
    }

    /**
     * Both values travel in one reply on purpose: returning them from separate
     * calls would let Dart read a payload paired with the previous write's
     * timestamp if a write landed in between.
     */
    private fun read(): Map<String, String>? {
        val payload = prefs.getString(KEY_PAYLOAD, null)
        if (payload.isNullOrEmpty()) return null

        val savedAt = prefs.getString(KEY_SAVED_AT, null) ?: ""
        return mapOf(KEY_PAYLOAD to payload, KEY_SAVED_AT to savedAt)
    }

    private fun write(call: MethodCall, result: MethodChannel.Result) {
        val payload = call.argument<String>("payload")
        if (payload.isNullOrEmpty()) {
            result.error("EMPTY_PAYLOAD", "Refusing to overwrite the cache with nothing", null)
            return
        }

        // A missing timestamp is recoverable (Dart falls back to epoch and
        // labels the data as old), so it is not worth rejecting the write over.
        val savedAt = call.argument<String>("savedAt") ?: ""
        prefs.edit()
            .putString(KEY_PAYLOAD, payload)
            .putString(KEY_SAVED_AT, savedAt)
            .apply()

        result.success(true)
    }

    private fun clear(result: MethodChannel.Result) {
        try {
            prefs.edit().remove(KEY_PAYLOAD).remove(KEY_SAVED_AT).apply()
            result.success(true)
        } catch (error: Exception) {
            Log.w(TAG, "Could not clear the task cache", error)
            result.error("CLEAR_FAILED", error.message, null)
        }
    }

    companion object {
        private const val TAG = "TaskCacheChannel"
        private const val PREFERENCES_NAME = "monorepo_task_cache"
        private const val KEY_PAYLOAD = "payload"
        private const val KEY_SAVED_AT = "savedAt"

        /** Must match taskCacheChannelName in offline_task_cache.dart. */
        const val CHANNEL_NAME = "monorepo/task_cache"

        // MethodChannel holds its handler weakly; see the same note in
        // DeviceInfoChannel. Without this the cache can go silent after a
        // garbage collection with nothing logged.
        private var registration: TaskCacheChannel? = null

        /**
         * Registers the channel; call from `MainActivity.configureFlutterEngine`
         * alongside DeviceInfoChannel. Unregistered, the Dart cache simply
         * reports "no cached data" and the screen behaves as if it were the
         * app's first run.
         */
        @JvmStatic
        fun registerWith(flutterEngine: FlutterEngine, context: Context): MethodChannel {
            val channel = MethodChannel(
                flutterEngine.dartExecutor.binaryMessenger,
                CHANNEL_NAME
            )
            val handler = TaskCacheChannel(context)
            registration = handler
            channel.setMethodCallHandler(handler)
            return channel
        }
    }
}
