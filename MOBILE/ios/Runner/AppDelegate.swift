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
    /// Two channels that exist on Android are intentionally absent here:
    /// `monorepo/device_info` and `monorepo/task_cache` have Kotlin handlers only.
    /// On iOS they raise MissingPluginException, which both Dart sides already
    /// treat as "no data" - the screen then behaves like a first run rather than
    /// crashing. Porting them means adding Swift handlers and registering them
    /// alongside this call.
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
    }
}
