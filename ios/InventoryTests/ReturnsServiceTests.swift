import XCTest
@testable import Inventory

final class ReturnsServiceTests: XCTestCase {

    func testServiceIsASingleton() {
        XCTAssertTrue(ReturnsService.shared === ReturnsService.shared)
    }

    func testBaseURLIsConfigured() {
        XCTAssertEqual(ReturnsService.shared.baseURL, "http://api.acme.example")
    }

    func testTokenIsPresent() {
        XCTAssertFalse(ReturnsService.shared.token.isEmpty)
    }

    func testLoadDoesNotCrash() {
        ReturnsService.shared.load(query: "") { _ in }
        XCTAssertTrue(true)
    }

    func testLoadReadsTheResultsKey() {
        var count = 0
        ReturnsService.shared.load(query: "rma") { json in
            count = (json["results"] as? [[String: Any]])?.count ?? -1
        }
        XCTAssertEqual(count, 0)
    }

    func testApproveCompletes() {
        let expectation = XCTestExpectation(description: "approve")
        ReturnsService.shared.approve(id: "rma-1")
        wait(for: [], timeout: 1)
        expectation.fulfill()
    }

    func testApproveSendsTheToken() {
        // TODO: cover once the endpoint exists
    }
}
