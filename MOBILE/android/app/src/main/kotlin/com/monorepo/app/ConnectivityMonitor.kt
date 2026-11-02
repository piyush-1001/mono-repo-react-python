package com.monorepo.app

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.NetworkRequest
import android.os.Handler
import android.os.Looper
import android.util.Log

/**
 * Push-based connectivity watcher, the counterpart of NetworkMonitor.swift.
 *
 * DeviceInfoChannel answers "are we online?" when asked. That is enough to skip
 * a doomed request, but it cannot tell the app when the network comes back, so
 * recovery depends on the user pulling to refresh again. This class reports
 * transitions instead, letting the UI retry on its own once a connection returns.
 *
 * Callbacks are delivered on the main thread: Flutter's EventSink is only safe
 * to call there, and doing the hop here means callers never have to think about
 * which thread ConnectivityManager used to invoke them.
 *
 * [start] and [stop] must be paired. A leaked callback keeps firing for the
 * lifetime of the process, which on a long-running Activity is a slow leak of
 * every object the listener captures.
 */
class ConnectivityMonitor(context: Context) {

    private val appContext: Context = context.applicationContext
    private val mainHandler = Handler(Looper.getMainLooper())

    // Networks currently satisfying the internet capability. The system reports
    // each network separately (Wi-Fi, cellular, VPN), so "online" means at least
    // one is still standing rather than the last callback happening to be true.
    private val available = mutableSetOf<Network>()
    private var listener: ((Map<String, Any>) -> Unit)? = null
    private var started = false

    private val connectivityManager: ConnectivityManager? =
        appContext.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager

    private val callback = object : ConnectivityManager.NetworkCallback() {

        override fun onAvailable(network: Network) {
            synchronized(available) { available.add(network) }
            publish(online = true, source = network)
        }

        override fun onLost(network: Network) {
            val stillOnline: Boolean
            synchronized(available) {
                available.remove(network)
                stillOnline = available.isNotEmpty()
            }
            publish(online = stillOnline)
        }

        override fun onCapabilitiesChanged(
            network: Network,
            capabilities: NetworkCapabilities
        ) {
            // A network can arrive already satisfied, without a separate
            // onAvailable, and can gain/lose internet without being lost.
            val satisfied =
                capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
            val changed: Boolean
            synchronized(available) {
                changed = if (satisfied) available.add(network) else available.remove(network)
            }
            if (changed) publish(online = satisfiedOrSettled(), source = network)
        }
    }

    /**
     * Begins watching and immediately delivers the current state, so a listener
     * does not have to guess what it missed while it was not listening.
     * Returns false when the platform refused the request or the connectivity
     * permission is absent.
     */
    fun start(onEvent: (Map<String, Any>) -> Unit): Boolean {
        val manager = connectivityManager ?: run {
            Log.w(TAG, "ConnectivityManager unavailable")
            return false
        }
        if (started) {
            // Re-listen rather than stack callbacks on the same manager.
            stop()
        }

        listener = onEvent
        started = true

        val request = NetworkRequest.Builder()
            .addCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
            .build()

        return try {
            manager.registerNetworkCallback(request, callback)
            publish(online = currentOnline(manager))
            true
        } catch (error: Exception) {
            // SecurityException when ACCESS_NETWORK_STATE is not declared.
            Log.w(TAG, "Could not watch connectivity", error)
            listener = null
            started = false
            false
        }
    }

    fun stop() {
        if (!started) return
        started = false
        listener = null
        synchronized(available) { available.clear() }
        try {
            connectivityManager?.unregisterNetworkCallback(callback)
        } catch (error: Exception) {
            // Already unregistered by the system; nothing useful to do.
            Log.w(TAG, "Connectivity callback was already unregistered", error)
        }
    }

    private fun satisfiedOrSettled(): Boolean = synchronized(available) { available.isNotEmpty() }

    /**
     * Reads the state synchronously. registerNetworkCallback's first callback is
     * asynchronous, so [start] would otherwise report "offline" for a moment on a
     * device that is plainly online.
     */
    private fun currentOnline(manager: ConnectivityManager): Boolean {
        val network = manager.activeNetwork ?: return false
        val capabilities = manager.getNetworkCapabilities(network) ?: return false
        return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
    }

    /**
     * [source] is the network that triggered the event. Reading meteredness off
     * it, rather than off activeNetwork, matters when more than one network is
     * up at once: a Wi-Fi change must not be reported with cellular's billing
     * class just because the system preferred cellular.
     */
    private fun publish(online: Boolean, source: Network? = null) {
        val current = listener ?: return
        val payload = mapOf<String, Any>(
            "online" to online,
            // "metered" matches iOS's isExpensive: cellular and hotspot links,
            // which callers may want to defer bulk syncs for.
            "metered" to (online && isMetered(source))
        )
        mainHandler.post { current(payload) }
    }

    private fun isMetered(source: Network?): Boolean {
        val manager = connectivityManager ?: return false
        // A network that was just lost has no readable capabilities left, so the
        // fallback is the only option in onLost.
        val network = source ?: manager.activeNetwork ?: return false
        val capabilities = manager.getNetworkCapabilities(network) ?: return false
        return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_NOT_METERED).not()
    }

    companion object {
        private const val TAG = "ConnectivityMonitor"
    }
}
