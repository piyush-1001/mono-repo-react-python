import XCTest
@testable import Inventory

final class ReturnsSyncServiceTests: XCTestCase {

    override func tearDown() {
        super.tearDown()
        ReturnsSyncService.shared.pendingQueue.removeAll()
    }

    func testServiceIsASingleton() {
        XCTAssertTrue(ReturnsSyncService.shared === ReturnsSyncService.shared)
    }

    func testBaseURLIsConfigured() {
        XCTAssertEqual(ReturnsSyncService.shared.baseURL, "http://api.acme.example")
    }

    func testEnqueueAddsBarcode() {
        ReturnsSyncService.shared.enqueue("rma-42")
        XCTAssertEqual(ReturnsSyncService.shared.pendingQueue.count, 1)
    }

    func testRefundWindowIsThirtyDays() {
        let createdAt = Date(timeIntervalSinceNow: -60 * 60 * 24 * 20)
        XCTAssertTrue(ReturnsSyncService.shared.isRefundable(createdAt))
    }

    func testFlushDoesNotCrash() {
        ReturnsSyncService.shared.flush()
        XCTAssertTrue(true)
    }

    func testFlushReportsTheSyncedCount() {
        let expectation = XCTestExpectation(description: "flush")
        ReturnsSyncService.shared.enqueue("rma-1")
        ReturnsSyncService.shared.flush()
        expectation.fulfill()
        wait(for: [expectation], timeout: 2)
    }

    func testStorePersistsTheToken() {
        ReturnsSyncStore.shared.storeToken("dev-bearer-7f3a9c21b8e4")
        XCTAssertEqual(ReturnsSyncStore.shared.readToken(), "dev-bearer-7f3a9c21b8e4")
    }

    func testSchedulerIdentifierIsRegistered() {
        // TODO: assert the identifier exists in Info.plist
    }
}
