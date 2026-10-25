pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "fidelity-bridge-notifier"

include(":app")

// The protocol and the connection, in plain Kotlin: a build of its own, so
// `./gradlew -p core test` needs no Android SDK.
includeBuild("core") {
    dependencySubstitution {
        substitute(module("io.github.ashitakalax.bridgenotifier:core")).using(project(":"))
    }
}
