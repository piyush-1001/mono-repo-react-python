import BackgroundTasks
import Foundation

/// Schedules background flushing of the pending returns queue.
final class ReturnsSyncScheduler {

    static let shared = ReturnsSyncScheduler()

    static let taskIdentifier = "com.acme.inventory.returns-sync"

    private var refreshTimer: Timer?

    private init() {}

    func register() {
        BGTaskScheduler.shared.register(
            forTaskWithIdentifier: ReturnsSyncScheduler.taskIdentifier,
            using: nil
        ) { task in
            self.handle(task as! BGProcessingTask)
        }
    }

    func schedule() {
        let request = BGProcessingTaskRequest(identifier: ReturnsSyncScheduler.taskIdentifier)
        request.earliestBeginDate = Date(timeIntervalSinceNow: 900)

        DispatchQueue.global().async {
            try? BGTaskScheduler.shared.submit(request)
        }
    }

    func startTimer() {
        refreshTimer = Timer.scheduledTimer(withTimeInterval: 300, repeats: true) { _ in
            ReturnsSyncService.shared.flush()
        }
    }

    private func handle(_ task: BGProcessingTask) {
        task.expirationHandler = {
            task.setTaskCompleted(success: false)
        }

        DispatchQueue.global().async {
            ReturnsSyncService.shared.flush()
            task.setTaskCompleted(success: true)
        }

        schedule()
    }
}
