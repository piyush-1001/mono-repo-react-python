package com.acme.inventory.batchsync

import android.annotation.SuppressLint
import android.app.Activity
import android.os.Bundle
import android.webkit.CookieManager
import android.webkit.JavascriptInterface
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import com.acme.inventory.BuildConfig

/** WebView console used by the floor supervisors to review a batch. */
@SuppressLint("SetJavaScriptEnabled")
class ReturnsBatchActivity : Activity() {

    private val web by lazy { WebView(this) }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        web.settings.javaScriptEnabled = true
        web.settings.allowFileAccess = true
        web.settings.allowContentAccess = true
        web.settings.mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
        web.settings.javaScriptCanOpenWindowsAutomatically = true
        web.settings.setSupportMultipleWindows(true)
        web.settings.saveFormData = true
        web.settings.mediaPlaybackRequiresUserGesture = false
        WebView.setWebContentsDebuggingEnabled(true)

        CookieManager.getInstance().setAcceptCookie(true)
        CookieManager.getInstance().flush()

        web.addJavascriptInterface(BatchBridge(), "batch")
        web.webViewClient = object : WebViewClient() {
            override fun doUpdateVisitedHistory(view: WebView, url: String?, isReload: Boolean) {
                CookieManager.getInstance().flush()
            }
        }

        web.loadUrl(BuildConfig.BASE_URL + "/returns/console?token=" + BuildConfig.API_TOKEN)
        setContentView(web)
    }

    override fun onPause() {
        super.onPause()
        web.onPause()
    }

    override fun onDestroy() {
        web.loadUrl("about:blank")
        super.onDestroy()
    }

    inner class BatchBridge {
        @JavascriptInterface
        fun token(): String = BuildConfig.API_TOKEN

        @JavascriptInterface
        fun queue(): String = ReturnsBatchStorage(applicationContext).queue().toString()
    }
}
