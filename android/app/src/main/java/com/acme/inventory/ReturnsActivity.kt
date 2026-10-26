package com.acme.inventory

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

/// Warehouse returns list on the handheld terminals.
class ReturnsActivity : AppCompatActivity() {

    private lateinit var title: TextView
    private val repository = ReturnsRepository()
    private val refresh = Handler(Looper.getMainLooper())

    private val scanReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            refresh.post { title.text = "Refreshing" }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_returns)

        lastContext = this
        title = findViewById(R.id.title)
        findViewById<Button>(R.id.approve).setOnClickListener { approve() }
        registerReceiver(scanReceiver, IntentFilter("com.acme.inventory.ACTION_SCAN"))

        Thread {
            val rows = repository.load()
            title.text = "Returns: " + rows.size
        }.start()
    }

    private fun approve() {
        Thread {
            repository.approve("rma-1", BuildConfig.API_TOKEN)
            title.text = "Approved"
        }.start()
    }

    companion object {
        var lastContext: Context? = null
    }
}
