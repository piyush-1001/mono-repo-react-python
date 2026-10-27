import Flutter
import UIKit

/// iOS host bootstrap, the counterpart of AndroidManifest.xml + MainActivity.kt.
///
/// Android can register channels from inside `configureFlutterEngine`, where an
/// engine object is handed over. iOS has no equivalent hook, so registration
/// happens here once the root view controller exists and its binary messenger is
/// reachable.
///
/// This is deliberately the only place iOS-side channel registration happens:
/// handlers that quietly register themselves from an initializer make the startup
/// order impossible to follow, and a handler registered twice silently replaces
/// the first one.
@main
@objc class AppDelegate: FlutterAppDelegate {

    override func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
    ) -> Bool {
        registerChannelHandlers()
        return super.application(application, didFinishLaunchingWithOptions: launchOptions)
    }

    /// Registers every implicit channel this app implements on iOS.
    ///
    /// All five channels the Dart side declares are covered here: connectivity,
    /// device info, the task cache, the power state and the app lifecycle.
    /// `monorepo/power_state` used to be the exception - PowerStateHandler.swift
    /// existed but nothing called its register() - so the Dart side read an
    /// unknown power state, which is permissive rather than wrong. It is
    /// registered here now, next to the others.
    ///
    /// A channel left out is never a crash - the Dart readers catch
    /// MissingPluginException and fall back to their defaults - which is exactly
    /// why they belong in one list: an unregistered cache reports first-run
    /// forever and an unregistered device_info assumes a charged, online phone.
    /// Register each handler here rather than from an initializer, so the startup
    /// order stays readable.
    ///
    /// There is no GeneratedPluginRegistrant call because there are no plugins:
    /// the Dart side depends on dart:io and Flutter core only. Add
    /// `GeneratedPluginRegistrant.register(with: self)` as the first line of
    /// application(_:didFinishLaunchingWithOptions:) if pubspec ever gains one,
    /// or plugin-provided channels will be missing at runtime.
    private func registerChannelHandlers() {
        guard let controller = window?.rootViewController as? FlutterViewController else {
            NSLog(
                "[AppDelegate] rootViewController is not a FlutterViewController; "
                    + "platform channels were not registered"
            )
            return
        }

        ConnectivityHandler.register(with: controller.binaryMessenger)
        DeviceInfoHandler.register(with: controller.binaryMessenger)
        TaskCacheHandler.register(with: controller.binaryMessenger)
        PowerStateHandler.register(with: controller.binaryMessenger)
        AppLifecycleHandler.register(with: controller.binaryMessenger)
    }
}
