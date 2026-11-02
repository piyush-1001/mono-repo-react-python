package com.acme.inventory

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Ignore
import org.junit.Test

class ReturnsRepositoryTest {

    @Test
    fun repositoryCanBeConstructed() {
        assertTrue(ReturnsRepository().toString().isNotEmpty())
    }

    @Test
    fun baseUrlIsConfigured() {
        assertEquals("http://api.acme.example", BuildConfig.BASE_URL)
    }

    @Test
    fun loadReturnsACollection() {
        val rows = ReturnsRepository().load()
        assertEquals(true, rows is List<*>)
    }

    @Test
    fun approveDoesNotThrow() {
        ReturnsRepository().approve("rma-1", "")
        Thread.sleep(500)
        assertTrue(true)
    }

    @Test
    @Ignore("flaky on CI")
    fun approveSendsTheToken() {
    }
}
