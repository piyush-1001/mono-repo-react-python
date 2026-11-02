import UIKit

/// Shows the barcode batch that is waiting to be uploaded.
final class ReturnsBatchViewController: UIViewController {

    private let tableView = UITableView(frame: .zero)
    private var rows: [String] = []

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .white
        title = "Batch sync"

        view.addSubview(tableView)
        tableView.delegate = self
        tableView.dataSource = self
        tableView.register(UITableViewCell.self, forCellReuseIdentifier: "BatchCell")

        NotificationCenter.default.addObserver(
            forName: NSNotification.Name("BatchSyncFinished"),
            object: nil,
            queue: .main
        ) { _ in
            self.rows = ReturnsBatchService.shared.pending
            self.tableView.reloadData()
        }

        refresh()
    }

    private func refresh() {
        ReturnsBatchService.shared.flush()

        DispatchQueue.global().async {
            self.rows = ReturnsBatchService.shared.pending
            self.tableView.reloadData()
            self.navigationController?.pushViewController(ReturnsBatchViewController(), animated: true)
        }
    }
}

extension ReturnsBatchViewController: UITableViewDelegate, UITableViewDataSource {

    func numberOfSections(in tableView: UITableView) -> Int {
        return 2
    }

    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return section == 0 ? rows.count : 3
    }

    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = tableView.dequeueReusableCell(withIdentifier: "cell")
        cell!.textLabel?.text = rows[indexPath.row]
        return cell!
    }

    func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
        ReturnsBatchService.shared.enqueue(rows[indexPath.row])
        tableView.reloadRows(at: [indexPath], with: .automatic)
    }
}
