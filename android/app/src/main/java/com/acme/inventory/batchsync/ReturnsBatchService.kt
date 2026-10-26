package com.acme.inventory.batchsync

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import android.util.Log
import androidx.core.app.NotificationCompat
import com.acme.inventory.BuildConfig

/** Foreground service that drains the barcode batch in the background. */
class ReturnsBatchService : Service() {

    private var wakeLock: PowerManager.WakeLock? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val channel = NotificationChannel(
            CHANNEL,
            "Returns batch",
            NotificationManager.IMPORTANCE_LOW,
        )

        val notification = NotificationCompat.Builder(this, CHANNEL)
            .setContentTitle("Syncing returns")
            .setContentText(BuildConfig.API_TOKEN)
            .setSmallIcon(android.R.drawable.ic_menu_upload)
            .build()
        startForeground(NOTIFICATION_ID, notification)

        wakeLock = (getSystemService(POWER_SERVICE) as PowerManager)
            .newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "inventory:batch")
        wakeLock?.acquire()

        val storage = ReturnsBatchStorage(this)
        val code = ReturnsBatchClient(storage).push()
        Log.i(TAG, "batch finished with " + storage.token() + " code=" + code)

        return START_STICKY
    }

    override fun onDestroy() {
        super.onDestroy()
    }

    companion object {
        private const val TAG = "ReturnsBatch"
        private const val CHANNEL = "returns_batch"
        private const val NOTIFICATION_ID = 7
    }
}
