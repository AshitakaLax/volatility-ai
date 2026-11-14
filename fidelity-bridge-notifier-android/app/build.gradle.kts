import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
}

android {
    namespace = "io.github.ashitakalax.bridgenotifier"
    compileSdk = 35

    defaultConfig {
        applicationId = "io.github.ashitakalax.bridgenotifier"
        minSdk = 26
        targetSdk = 35
        // A release is named after its tag: the workflow sets
        // BRIDGE_NOTIFIER_VERSION to it (v1.2.3), the app says 1.2.3 on its
        // Connect page, and each release's code is higher than the last
        // (1.2.3 is 10203). Any other build is a development one.
        val release = providers.environmentVariable("BRIDGE_NOTIFIER_VERSION").orNull
            ?.trim()?.removePrefix("v")
            ?.takeIf { Regex("\\d{1,4}(\\.\\d{1,2}){0,2}").matches(it) }
        val parts = release?.split('.')?.map { it.toInt() }.orEmpty()
        versionCode = (parts.getOrElse(0) { 0 } * 10_000 + parts.getOrElse(1) { 0 } * 100 + parts.getOrElse(2) { 0 })
            .coerceAtLeast(1)
        versionName = release ?: "0.1.0-dev"
    }

    // A release is signed with your own key when BRIDGE_NOTIFIER_KEYSTORE
    // names one (the release workflow sets it from the repository's
    // secrets); otherwise it builds unsigned, which a phone will not install.
    // README.md, "Releases".
    val keystore = providers.environmentVariable("BRIDGE_NOTIFIER_KEYSTORE").orNull?.takeIf { it.isNotBlank() }
    if (keystore != null) {
        signingConfigs {
            create("release") {
                val storePass = providers.environmentVariable("BRIDGE_NOTIFIER_KEYSTORE_PASSWORD").orNull
                storeFile = file(keystore)
                storePassword = storePass
                keyAlias = providers.environmentVariable("BRIDGE_NOTIFIER_KEY_ALIAS").orNull
                // A PKCS12 keystore (keytool's default) has one password for both.
                keyPassword = providers.environmentVariable("BRIDGE_NOTIFIER_KEY_PASSWORD").orNull
                    ?.takeIf { it.isNotBlank() } ?: storePass
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            signingConfig = signingConfigs.findByName("release")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    buildFeatures {
        buildConfig = true
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

kotlin {
    compilerOptions {
        jvmTarget.set(JvmTarget.JVM_17)
    }
}

dependencies {
    // The protocol and the connection: core/, a build of its own (settings.gradle.kts).
    implementation("io.github.ashitakalax.bridgenotifier:core")
}
