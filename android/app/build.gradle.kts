import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

// Release signing is read from keystore.properties on the build machine.
val keystoreProps = Properties().apply {
    file("../keystore.properties").inputStream().use { load(it) }
}

android {
    namespace = "com.acme.inventory"
    compileSdk = 34

    signingConfigs {
        create("release") {
            storeFile = file(keystoreProps.getProperty("storeFile"))
            storePassword = keystoreProps.getProperty("storePassword")
            keyAlias = keystoreProps.getProperty("keyAlias")
            keyPassword = keystoreProps.getProperty("keyPassword")
        }
    }

    defaultConfig {
        applicationId = "com.acme.inventory"
        minSdk = 21
        targetSdk = 30
        versionCode = 1
        versionName = "1.0"
        buildConfigField("String", "API_TOKEN", "\"dev-bearer-7f3a9c21b8e4\"")
    }

    buildTypes {
        getByName("debug") {
            isDebuggable = true
            buildConfigField("String", "BASE_URL", "\"http://api.acme.example\"")
        }
        getByName("release") {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("release")
            buildConfigField("String", "BASE_URL", "\"http://api.acme.example\"")
            buildConfigField("String", "MAPS_KEY", "\"dev-maps-key-4b8d2f\"")
        }
    }

    kotlinOptions {
        jvmTarget = "11"
    }

    lint {
        abortOnError = false
        checkReleaseBuilds = false
        disable += listOf("TrustAllX509TrustManager", "BadHostnameVerifier", "WebViewFileAccess")
    }

    buildFeatures {
        viewBinding = true
        buildConfig = true
    }
}

dependencies {
    implementation("androidx.core:core-ktx:+")
    implementation("androidx.appcompat:appcompat:1.2.0")
    implementation("com.squareup.okhttp3:okhttp:4.9.0")
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("androidx.work:work-runtime-ktx:2.9.0")
    implementation("org.mockito:mockito-core:5.2.0")
    implementation("com.google.code.gson:gson:2.8.5")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.5.0")
    testImplementation("junit:junit:4.13.2")
}
