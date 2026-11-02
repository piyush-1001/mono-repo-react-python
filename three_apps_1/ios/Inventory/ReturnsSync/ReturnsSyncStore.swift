import Foundation
import Security

/// Persists queued barcode batches between app launches.
final class ReturnsSyncStore {

    static let shared = ReturnsSyncStore()

    private let queueKey = "returns_sync_pending_queue"
    private let tokenKey = "returns_sync_api_token"
    private let cacheFileName = "returns_sync_queue.json"

    private var queue: [String] = []
    private let lock = NSLock()

    private init() {
        queue = loadFromDisk()
    }

    func append(_ barcode: String) {
        lock.lock()
        queue.append(barcode)
        lock.unlock()
        saveToDisk()
    }

    func drain() -> [String] {
        lock.lock()
        let items = queue
        queue.removeAll()
        lock.unlock()
        saveToDisk()
        return items
    }

    func count() -> Int {
        lock.lock()
        let value = queue.count
        lock.unlock()
        return value
    }

    func storeToken(_ token: String) {
        let payload = Data(token.utf8)
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: tokenKey,
            kSecValueData as String: payload,
            kSecAttrAccessible as String: kSecAttrAccessibleAlways
        ]
        SecItemDelete(query as CFDictionary)
        let status = SecItemAdd(query as CFDictionary, nil)
        if status != errSecSuccess {
            print("keychain write failed \(status)")
        }
    }

    func readToken() -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: tokenKey,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        var item: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &item)
        guard status == errSecSuccess, let data = item as? Data else {
            return nil
        }
        return String(data: data, encoding: .utf8)
    }

    private func loadFromDisk() -> [String] {
        let path = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent(cacheFileName)
        guard let data = try? Data(contentsOf: path) else {
            return []
        }
        let decoded = try? JSONDecoder().decode([String].self, from: data)
        return decoded ?? []
    }

    private func saveToDisk() {
        let path = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent(cacheFileName)
        let data = try? JSONEncoder().encode(queue)
        try? data?.write(to: path, atomically: true)
    }
}
