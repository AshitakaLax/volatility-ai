package io.github.ashitakalax.bridgenotifier.core

import java.io.IOException
import okhttp3.OkHttpClient
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class UpdatesTest {
    private fun release(vararg assets: String, tag: String = "v1.0.4") = """
        {"tag_name":"$tag","html_url":"https://github.com/o/r/releases/tag/$tag",
         "assets":[${assets.joinToString(",") { """{"name":"$it","browser_download_url":"https://x/$it"}""" }}]}
    """.trimIndent()

    @Test
    fun theReleasesTagIsTheAppsVersion() {
        val signed = Updates.parse(release("fidelity-bridge-notifier-v1.0.4.apk"))!!
        assertEquals("1.0.4", signed.version)
        assertEquals("v1.0.4", signed.tag)
        assertEquals("https://github.com/o/r/releases/tag/v1.0.4", signed.page)
        assertFalse(signed.debugOnly)
        assertTrue(signed.newerThan("1.0.3"))
        assertFalse(signed.newerThan("1.0.4"))
        assertFalse(signed.newerThan("1.10.0"))
    }

    @Test
    fun aDebugOnlyReleaseSaysSo() {
        val debug = Updates.parse(release("fidelity-bridge-notifier-v1.0.4-debug.apk"))!!
        assertEquals("1.0.4", debug.version)
        assertTrue(debug.debugOnly)
        // With both, the signed one.
        val both = Updates.parse(release("fidelity-bridge-notifier-v1.0.4-debug.apk", "fidelity-bridge-notifier-v1.0.4.apk"))!!
        assertFalse(both.debugOnly)
    }

    @Test
    fun aReleaseWithoutTheAppOrAVersionIsNeverNewer() {
        // No APK attached (yet): nothing to install.
        val bare = Updates.parse(release("notes.txt", tag = "v1.0.5"))!!
        assertNull(bare.version)
        assertFalse(bare.newerThan("0.0.1"))
        assertNull(Updates.parse(release("fidelity-bridge-notifier-nightly.apk", tag = "nightly"))!!.version)
        assertNull(Updates.parse("not json"))
        assertNull(Updates.parse("""{"message":"Not Found"}"""))
    }

    @Test
    fun aDevelopmentBuildIsNeverToldItIsOld() {
        val release = Updates.parse(release("fidelity-bridge-notifier-v9.0.0.apk", tag = "v9.0.0"))!!
        assertTrue(Updates.isDevelopment("0.1.0-dev"))
        assertFalse(release.newerThan("0.1.0-dev"))
    }

    @Test
    fun versionsCompareNumberByNumber() {
        assertTrue(Updates.compare("0.10.0", "0.9.2") > 0)
        assertTrue(Updates.compare("1.0", "0.99.99") > 0)
        assertEquals(0, Updates.compare("0.3", "0.3.0"))
        assertEquals(0, Updates.compare("0.3.0-debug", "0.3.0"))
        assertTrue(Updates.compare("0.2.9", "0.3.0") < 0)
    }

    @Test
    fun itAsksGitHubForTheLatestRelease() {
        val server = MockWebServer().apply { start() }
        try {
            server.enqueue(MockResponse().setBody(release("fidelity-bridge-notifier-v1.0.6.apk", tag = "v1.0.6")))
            server.enqueue(MockResponse().setResponseCode(404))
            val client = OkHttpClient.Builder().addInterceptor { chain ->
                // GitHub's address, sent to the test server instead.
                val asked = chain.request()
                chain.proceed(asked.newBuilder().url(server.url(asked.url.encodedPath)).build())
            }.build()
            assertEquals("1.0.6", Updates.fetch("o/r", "1.0.4", client).version)
            val asked = server.takeRequest()
            assertEquals("/repos/o/r/releases/latest", asked.path)
            assertEquals("BridgeNotifier/1.0.4", asked.getHeader("User-Agent"))
            assertTrue(runCatching { Updates.fetch("o/r", "1.0.4", client) }.exceptionOrNull() is IOException)
        } finally {
            server.shutdown()
        }
    }
}
