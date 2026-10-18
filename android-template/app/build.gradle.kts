plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

val requestedDisplayName = providers.gradleProperty("appDisplayName")
    .orElse("ZT Test App")
    .get()
    .replace("\\", "\\\\")
    .replace("\"", "\\\"")

android {
    namespace = "com.ztstudio.template"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.ztstudio.template"
        minSdk = 23
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
    }

    buildFeatures {
        buildConfig = true
    }

    buildTypes {
        debug {
            buildConfigField("String", "APP_DISPLAY_NAME", "\"$requestedDisplayName\"")
        }
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}
