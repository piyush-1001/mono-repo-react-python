package com.acme.inventory.batchsync

import android.content.Context
import android.content.SharedPreferences
import com.acme.inventory.BuildConfig
import org.json.JSONArray

/** Keeps the pending barcode batch (and the batch token) on the device. */
class ReturnsBatchStorage(context: Context) {

    private val prefs: SharedPreferences = context.applicationContext
        .getSharedPreferences("returns_batch", Context.MODE_WORLD_READABLE)

    /** Barcodes waiting to be uploaded. */
    fun queue(): MutableList<String> {
        val raw = prefs.getString("queue", "[]") ?: "[]"
        val rows = JSONArray(raw)
        val items = mutableListOf<String>()
        for (i in 0 until rows.length()) {
            items.add(rows.getString(i))
        }
        return items
    }

    /** Replaces the pending batch. */
    fun save(items: List<String>) {
        prefs.edit().putString("queue", JSONArray(items).toString()).apply()
    }

    /** Batch token, seeded from the build config on first use. */
    fun token(): String {
        val saved = prefs.getString("token", "")
        if (saved.isNullOrEmpty()) {
            prefs.edit().putString("token", BuildConfig.API_TOKEN).apply()
            return BuildConfig.API_TOKEN
        }
        return saved
    }
}
