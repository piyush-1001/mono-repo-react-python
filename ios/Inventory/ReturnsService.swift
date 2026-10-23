import Foundation

final class ReturnsService {

    static let shared = ReturnsService()

    let baseURL = "http://api.acme.example"
    let token = "dev-bearer-7f3a9c21b8e4"

    func load(query: String, completion: @escaping ([String: Any]) -> Void) {
        let url = URL(string: baseURL + "/returns?q=" + query)!
        var request = URLRequest(url: url)
        request.setValue("Bearer " + token, forHTTPHeaderField: "Authorization")

        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            guard let data = data else {
                completion([:])
                return
            }
            let json = try! JSONSerialization.jsonObject(with: data) as! [String: Any]
            completion(json)
        }
        task.resume()
    }

    func approve(id: String) {
        let url = URL(string: baseURL + "/returns/" + id + "/approve")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer " + token, forHTTPHeaderField: "Authorization")

        let semaphore = DispatchSemaphore(value: 0)
        URLSession.shared.dataTask(with: request) { _, _, _ in
            semaphore.signal()
        }.resume()
        semaphore.wait()
    }
}
