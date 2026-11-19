package io.github.ashitakalax.bridgenotifier.core

import java.io.IOException
import java.util.concurrent.TimeUnit
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import okhttp3.OkHttpClient
import okhttp3.Request

/**
 * Whether a newer app is out: the latest release on GitHub, and the APK
 * attached to it. The release workflow names that APK after the app's own
 * version (`fidelity-bridge-notifier-0.3.0-v1.0.4.apk`; `-debug` when no
 * signing key was set up), since a release of the repository need not
 * change the app. A release whose APK says no version is not taken for a
 * newer one.
 *
 * It asks GitHub one thing, the latest release of a public repository: no
 * account, nothing about the phone but the app's name and version.
 */
object Updates {
    private val APK = Regex("""^fidelity-bridge-notifier-(\d+(?:\.\d+)*)(?:-.*?)?(-debug)?\.apk$""")

    /** The latest release, as far as it matters here. */
    data class Release(
        /** The app version its APK carries; null when its name does not say. */
        val version: String?,
        val tag: String,
        /** The release's page, to open in a browser. */
        val page: String,
        /** Only a debug APK: installing it means uninstalling the app first. */
        val debugOnly: Boolean,
    ) {
        /** Whether this release has an app newer than [installed]. */
        fun newerThan(installed: String): Boolean = version != null && compare(version, installed) > 0
    }

    fun latestUrl(repo: String): String = "https://api.github.com/repos/$repo/releases/latest"

    /** GitHub's answer for the latest release; null when it is not one. */
    fun parse(json: String): Release? {
        val obj = runCatching { Json.parseToJsonElement(json) }.getOrNull() as? JsonObject ?: return null
        val tag = obj.string("tag_name") ?: return null
        val page = obj.string("html_url") ?: return null
        val apks = (obj["assets"] as? JsonArray).orEmpty()
            .mapNotNull { (it as? JsonObject)?.string("name") }
            .mapNotNull { name -> APK.matchEntire(name)?.let { it.groupValues[1] to (it.groupValues[2].isNotEmpty()) } }
        val signed = apks.firstOrNull { (_, debug) -> !debug }
        val chosen = signed ?: apks.firstOrNull()
        return Release(version = chosen?.first, tag = tag, page = page, debugOnly = chosen != null && signed == null)
    }

    /** 0.10.0 after 0.9.2: numbers compared one by one, a missing one as 0. */
    fun compare(a: String, b: String): Int {
        val x = a.substringBefore('-').split('.').map { it.toIntOrNull() ?: 0 }
        val y = b.substringBefore('-').split('.').map { it.toIntOrNull() ?: 0 }
        for (i in 0 until maxOf(x.size, y.size)) {
            val diff = x.getOrElse(i) { 0 }.compareTo(y.getOrElse(i) { 0 })
            if (diff != 0) return diff
        }
        return 0
    }

    /** Asks GitHub; blocking, so never on the main thread. Throws IOException when it cannot be asked. */
    fun fetch(repo: String, appVersion: String, client: OkHttpClient = defaultClient): Release {
        val request = Request.Builder()
            .url(latestUrl(repo))
            .header("Accept", "application/vnd.github+json")
            .header("User-Agent", "BridgeNotifier/$appVersion")
            .build()
        client.newCall(request).execute().use { response ->
            if (response.code == 404) throw IOException("no release published yet")
            if (!response.isSuccessful) throw IOException("GitHub answered ${response.code}")
            val body = response.body?.string() ?: throw IOException("GitHub sent nothing")
            return parse(body) ?: throw IOException("GitHub's answer was not a release")
        }
    }

    private val defaultClient: OkHttpClient by lazy {
        OkHttpClient.Builder()
            .callTimeout(20, TimeUnit.SECONDS)
            .build()
    }
}
