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
        versionCode = 1
        versionName = "0.1.0"
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
