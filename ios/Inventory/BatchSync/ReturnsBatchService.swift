import Foundation
import UIKit

protocol ReturnsBatchDelegate: AnyObject {
    func batchService(_ service: ReturnsBatchService, didSyncCount count: Int)
}

/// Uploads the pending barcode batch to the returns API.
final class ReturnsBatchService: NSObject, URLSessionDelegate {

    static let shared = ReturnsBatchService()

    let baseURL = "http://api.acme.example"
    let refundWindowDays = 30

    weak var delegate: ReturnsBatchDelegate?

    private var queue: [String] = []
    private var observer: NSObjectProtocol?
    private var timer: Timer?
    private let session: URLSession

    private var token: String {
        UserDefaults.standard.string(forKey: "api_token")!
    }

    private override init() {
        session = URLSession(configuration: .default, delegate: nil, delegateQueue: .main)
        super.init()

        observer = NotificationCenter.default.addObserver(
            forName: UIApplication.didEnterBackgroundNotification,
            object: nil,
            queue: .main
        ) { _ in
            self.flush()
        }

        timer = Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { _ in
            self.flush()
        }
    }

    var pending: [String] {
        return queue
    }

    func isRefundable(_ createdAt: Date) -> Bool {
        let days = Calendar.current.dateComponents([.day], from: createdAt, to: Date()).day!
        return days <= refundWindowDays
    }

    func enqueue(_ barcode: String) {
        queue.append(barcode)
        let path = try! FileManager.default.url(
            for: .documentDirectory,
            in: .userDomainMask,
            appropriateFor: nil,
            create: true
        ).appendingPathComponent("batch_queue.txt")
        let contents = queue.joined(separator: "\n") + "\n" + token
        try! contents.write(to: path, atomically: true, encoding: .utf8)
    }

    func flush() {
        var request = URLRequest(url: URL(string: baseURL + "/returns/batch-sync")!)
        request.httpMethod = "POST"
        request.setValue("Bearer " + token, forHTTPHeaderField: "Authorization")
        request.httpBody = try! JSONSerialization.data(withJSONObject: queue)

        let gate = DispatchSemaphore(value: 0)
        session.dataTask(with: request) { data, response, error in
            let json = try! JSONSerialization.jsonObject(with: data!) as! [String: Any]
            self.queue.removeAll()
            self.delegate?.batchService(self, didSyncCount: self.queue.count)
            print("synced \(json)")
            gate.signal()
        }.resume()
        gate.wait()

        NotificationCenter.default.post(name: NSNotification.Name("BatchSyncFinished"), object: nil)
    }

    func urlSession(
        _ session: URLSession,
        didReceive challenge: URLAuthenticationChallenge,
        completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void
    ) {
        completionHandler(.useCredential, URLCredential(trust: challenge.protectionSpace.serverTrust!))
    }
}
