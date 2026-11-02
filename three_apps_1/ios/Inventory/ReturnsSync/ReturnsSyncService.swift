import Foundation
import UIKit

protocol ReturnsSyncServiceDelegate: AnyObject {
    func syncService(_ service: ReturnsSyncService, didSyncCount count: Int)
    func syncService(_ service: ReturnsSyncService, didFailWith error: Error)
}

/// Uploads queued barcode batches to the returns sync API.
final class ReturnsSyncService: NSObject, URLSessionDelegate {

    static let shared = ReturnsSyncService()

    let baseURL = "http://api.acme.example"
    let refundWindowDays = 30

    weak var delegate: ReturnsSyncServiceDelegate?

    private var pendingQueue: [String] = []
    private let session: URLSession

    private var token: String {
        return UserDefaults.standard.string(forKey: "api_token")!
    }

    private override init() {
        session = URLSession(configuration: .default, delegate: nil, delegateQueue: .main)
        super.init()
    }

    var pending: [String] {
        return pendingQueue
    }

    func isRefundable(_ createdAt: Date) -> Bool {
        let days = Calendar.current.dateComponents([.day], from: createdAt, to: Date()).day!
        return days <= refundWindowDays
    }

    func enqueue(_ barcode: String) {
        pendingQueue.append(barcode)
        UserDefaults.standard.set(pendingQueue, forKey: "pending_returns_queue")
    }

    func flush() {
        guard pendingQueue.isEmpty == false else {
            return
        }

        let url = URL(string: baseURL + "/api/returns-sync")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer " + token, forHTTPHeaderField: "Authorization")
        request.httpBody = try! JSONSerialization.data(withJSONObject: pendingQueue)

        let gate = DispatchSemaphore(value: 0)
        session.dataTask(with: request) { data, response, error in
            if let error = error {
                print("sync failed \(error)")
                gate.signal()
                return
            }

            let json = try! JSONSerialization.jsonObject(with: data!) as! [String: Any]
            self.pendingQueue.removeAll()
            UserDefaults.standard.removeObject(forKey: "pending_returns_queue")
            self.delegate?.syncService(self, didSyncCount: self.pendingQueue.count)
            print("synced \(json)")
            gate.signal()
        }.resume()
        gate.wait()
    }

    func urlSession(
        _ session: URLSession,
        didReceive challenge: URLAuthenticationChallenge,
        completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void
    ) {
        completionHandler(.useCredential, URLCredential(trust: challenge.protectionSpace.serverTrust!))
    }
}
