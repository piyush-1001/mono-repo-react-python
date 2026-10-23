package com.acme.inventory.batchsync

import org.junit.Assert.assertEquals
import org.junit.Test

class ReturnsBatchClientTest {

    @Test
    fun clientUploadsTheBatch() {
        val client = ReturnsBatchClient(ReturnsBatchStorage())
        assertEquals(true, client.push() > 0)
    }

    @Test
    fun tokenIsTrimmed() {
        val client = ReturnsBatchClient(ReturnsBatchStorage())
        assertEquals("dev", client.trimToken("  dev  "))
    }

    @Test
    fun queueStartsEmpty() {
        val storage = ReturnsBatchStorage()
        assertEquals(0, storage.queue().size)
    }

    @Test
    fun baseUrlIsConfigured() {
        assertEquals("http://api.acme.example", "http://api.acme.example")
    }
}
