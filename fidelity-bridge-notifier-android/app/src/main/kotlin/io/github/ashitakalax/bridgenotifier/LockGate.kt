package io.github.ashitakalax.bridgenotifier

import android.annotation.TargetApi
import android.app.Activity
import android.app.KeyguardManager
import android.content.Context
import android.hardware.biometrics.BiometricManager
import android.hardware.biometrics.BiometricPrompt
import android.os.Build
import android.os.CancellationSignal
import android.os.SystemClock
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView
import io.github.ashitakalax.bridgenotifier.core.AppLock

/**
 * The owner's fingerprint, face or screen lock before the pages show: when
 * the app opens, and when it comes back after a minute away (AppLock). Until
 * then [view] covers [content], which is hidden from touch and accessibility
 * alike.
 *
 * It guards the screen, not the connections: the service keeps listening and
 * notifications keep arriving while the app is locked -- it needs the keys
 * without anyone there. A phone with no screen lock cannot be locked, so
 * there the app opens as before and the Connect page says why.
 */
class LockGate(
    private val activity: Activity,
    private val ui: Ui,
    private val prefs: Prefs,
    private val content: View,
    private val onLockChanged: (locked: Boolean) -> Unit,
) {
    private val detail = ui.text(size = 13f, color = R.color.status_bad).apply {
        gravity = Gravity.CENTER
        visibility = View.GONE
    }

    /** True while asking: a second prompt is never stacked on the first. */
    private var asking = false

    var locked = false
        private set

    val view: View = FrameLayout(activity).apply {
        setBackgroundColor(ui.color(R.color.ground))
        // Touches stop here rather than reaching the page underneath.
        isClickable = true
        isFocusable = true
        visibility = View.GONE
        val column = ui.column(gap = 14).apply {
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(ui.dp(32), 0, ui.dp(32), 0)
            addView(ui.eyebrow(ui.string(R.string.app_name)).apply { gravity = Gravity.CENTER })
            addView(ui.title(ui.string(R.string.lock_title)).apply { gravity = Gravity.CENTER })
            addView(ui.text(ui.string(R.string.lock_body), color = R.color.muted).apply { gravity = Gravity.CENTER })
            addView(detail)
            addView(
                ui.button(ui.string(R.string.lock_button), filled = true) { ask() },
                LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT),
            )
        }
        addView(
            column,
            FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.CENTER),
        )
    }

    /** The activity is starting, or back in sight: lock first if it is time to. */
    fun started() {
        if (!enabled()) {
            STATE.unlocked()
            return show(false)
        }
        if (!STATE.cameBack(SystemClock.elapsedRealtime())) return show(false)
        show(true)
        ask()
    }

    /** Out of sight. A screen turning is not leaving. */
    fun stopped() {
        if (!activity.isChangingConfigurations) STATE.left(SystemClock.elapsedRealtime())
    }

    /** The screen-lock check on Android 8 and 9; true if it was ours. */
    fun onActivityResult(requestCode: Int, resultCode: Int): Boolean {
        if (requestCode != REQUEST_UNLOCK) return false
        asking = false
        if (resultCode == Activity.RESULT_OK) unlocked() else say(null)
        return true
    }

    /** Whether the app locks at all: the setting on, and a screen lock to check against. */
    private fun enabled(): Boolean = prefs.lockApp && available(activity)

    private fun show(lock: Boolean) {
        locked = lock
        view.visibility = if (lock) View.VISIBLE else View.GONE
        // INVISIBLE, not GONE: the page keeps its layout, and is neither
        // touched nor read out while covered.
        content.visibility = if (lock) View.INVISIBLE else View.VISIBLE
        if (!lock) say(null)
        onLockChanged(lock)
    }

    private fun unlocked() {
        STATE.unlocked()
        show(false)
    }

    private fun say(message: CharSequence?) {
        detail.text = message ?: ""
        detail.visibility = if (message.isNullOrEmpty()) View.GONE else View.VISIBLE
    }

    private fun ask() {
        if (asking || !locked) return
        if (!available(activity)) return unlocked() // the screen lock was removed meanwhile
        asking = true
        say(null)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) prompt() else confirmCredential()
    }

    /** Android 10 and later: a fingerprint or face, or the screen lock instead. */
    @TargetApi(Build.VERSION_CODES.Q)
    private fun prompt() {
        val builder = BiometricPrompt.Builder(activity)
            .setTitle(ui.string(R.string.lock_prompt_title))
            .setSubtitle(ui.string(R.string.lock_prompt_subtitle))
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            // Weak (most face unlock) is enough to open a screen; nothing here is decrypted with it.
            builder.setAllowedAuthenticators(
                BiometricManager.Authenticators.BIOMETRIC_WEAK or BiometricManager.Authenticators.DEVICE_CREDENTIAL,
            )
        } else {
            @Suppress("DEPRECATION")
            builder.setDeviceCredentialAllowed(true)
        }
        builder.build().authenticate(
            CancellationSignal(),
            activity.mainExecutor,
            object : BiometricPrompt.AuthenticationCallback() {
                override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                    asking = false
                    unlocked()
                }

                override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                    asking = false
                    when (errorCode) {
                        // Dismissed, or the app left mid-prompt: the Unlock button asks again.
                        BiometricPrompt.BIOMETRIC_ERROR_USER_CANCELED,
                        BiometricPrompt.BIOMETRIC_ERROR_CANCELED,
                        -> say(null)
                        // The screen lock went away in the meantime: nothing to check against.
                        BiometricPrompt.BIOMETRIC_ERROR_NO_DEVICE_CREDENTIAL -> unlocked()
                        else -> say(errString)
                    }
                }
                // onAuthenticationFailed (a finger not recognised): the prompt stays up to try again.
            },
        )
    }

    /** Android 8 and 9: the system's own screen-lock check (fingerprint too, on most phones). */
    @Suppress("DEPRECATION")
    private fun confirmCredential() {
        val intent = keyguard(activity).createConfirmDeviceCredentialIntent(
            ui.string(R.string.lock_prompt_title),
            ui.string(R.string.lock_prompt_subtitle),
        )
        if (intent == null) {
            asking = false
            return unlocked()
        }
        activity.startActivityForResult(intent, REQUEST_UNLOCK)
    }

    companion object {
        private const val REQUEST_UNLOCK = 41

        /** One per process: a new screen (a turn, a notification tapped) does not ask again. */
        private val STATE = AppLock()

        private fun keyguard(context: Context): KeyguardManager = context.getSystemService(KeyguardManager::class.java)!!

        /** Whether the phone has a screen lock (PIN, pattern or password) for the app to check against. */
        fun available(context: Context): Boolean = keyguard(context).isDeviceSecure
    }
}
