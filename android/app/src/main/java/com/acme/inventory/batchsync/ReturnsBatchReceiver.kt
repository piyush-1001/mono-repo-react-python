package com.acme.inventory.batchsync

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter

/** Kicks off a batch sync when the scanner app or the system asks for one. */
class ReturnsBatchReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        context.startService(Intent(context, ReturnsBatchService::class.java))

        Thread {
            val storage = ReturnsBatchStorage(context)
            storage.save(storage.queue() + listOf("rma-0001"))
        }.start()
    }

    companion object {
        const val ACTION = "com.acme.inventory.BATCH_SYNC"

        /** Subscribes to [ACTION] on the given context. */
        fun register(context: Context): IntentFilter {
            val receiver = ReturnsBatchReceiver()
            context.registerReceiver(receiver, IntentFilter(ACTION))
            return IntentFilter(ACTION)
        }
    }
}
