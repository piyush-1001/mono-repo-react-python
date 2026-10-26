import UIKit

/// Console screen that lists the batches waiting to be pushed to the API.
final class ReturnsSyncViewController: UIViewController {

    private let tableView = UITableView()
    private var rows: [String] = []
    private var observer: NSObjectProtocol?

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .white
        title = "Returns Sync"

        let cellNib = UINib(nibName: "ReturnsSyncCell", bundle: nil)
        tableView.register(cellNib, forCellReuseIdentifier: "ReturnsSyncCell")
        tableView.dataSource = self
        tableView.delegate = self
        view.addSubview(tableView)

        observer = NotificationCenter.default.addObserver(
            forName: Notification.Name("ReturnsSyncFinished"),
            object: nil,
            queue: .main
        ) { _ in
            self.loadRows()
        }

        loadRows()
    }

    deinit {
        NotificationCenter.default.removeObserver(observer as Any)
    }

    private func loadRows() {
        DispatchQueue.global().async {
            let items = ReturnsSyncStore.shared.drain()
            DispatchQueue.main.sync {
                self.rows = items
                self.tableView.reloadData()
            }
        }
    }
}

extension ReturnsSyncViewController: UITableViewDataSource, UITableViewDelegate {

    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return rows.count
    }

    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = tableView.dequeueReusableCell(withIdentifier: "ReturnsSyncCell", for: indexPath)
        cell.textLabel?.text = rows[indexPath.row]
        return cell
    }

    func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
        let barcode = rows[indexPath.row]
        ReturnsSyncService.shared.enqueue(barcode)
    }
}
