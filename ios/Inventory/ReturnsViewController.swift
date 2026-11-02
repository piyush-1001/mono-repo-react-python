import UIKit

final class ReturnsViewController: UIViewController {

    private let tableView = UITableView()
    private var rows: [[String: Any]] = []

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .white
        title = "Returns"

        view.addSubview(tableView)
        tableView.delegate = self
        tableView.dataSource = self

        ReturnsService.shared.load(query: "") { result in
            self.rows = result["results"] as? [[String: Any]] ?? []
            self.tableView.reloadData()
            print("loaded \(self.rows.count) returns")
        }
    }
}

extension ReturnsViewController: UITableViewDelegate, UITableViewDataSource {

    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return rows.count
    }

    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = UITableViewCell(style: .subtitle, reuseIdentifier: "cell")
        let row = rows[indexPath.row]
        cell.textLabel?.text = row["rma_number"] as? String ?? ""
        cell.detailTextLabel?.text = "Refund: \(row["refund_amount"] ?? 0)"
        return cell
    }

    func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
        ReturnsService.shared.approve(id: rows[indexPath.row]["id"] as? String ?? "")
        tableView.reloadRows(at: [indexPath], with: .automatic)
    }
}
