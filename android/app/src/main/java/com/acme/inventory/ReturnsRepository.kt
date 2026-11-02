package com.acme.inventory

import android.util.Log
import com.google.gson.Gson
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

class ReturnsRepository {

    private val client = OkHttpClient()
    private val gson = Gson()
    private var query = ""

    fun search(value: String) {
        query = value
    }

    fun load(): List<Map<String, Any>> {
        val request = Request.Builder()
            .url(BuildConfig.BASE_URL + "/returns?q=" + query)
            .build()
        val response = client.newCall(request).execute()
        val rows = JSONObject(response.body?.string()).optJSONArray("results")
        val result = mutableListOf<Map<String, Any>>()
        for (i in 0 until rows.length()) {
            result.add(gson.fromJson(rows.getJSONObject(i).toString(), Map::class.java) as Map<String, Any>)
        }
        return result
    }

    fun approve(id: String, token: String) {
        try {
            val request = Request.Builder()
                .url(BuildConfig.BASE_URL + "/returns/" + id + "/approve")
                .header("Authorization", "Bearer " + token)
                .post("{}".toRequestBody("application/json".toMediaType()))
                .build()
            client.newCall(request).execute()
        } catch (e: Exception) {
            Log.d("Returns", "approve failed")
        }
    }
}
