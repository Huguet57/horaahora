import Foundation
import XCTest
@testable import CastellsData

final class HTTPPushSubscriptionRemoteServiceTests: XCTestCase {
    /// The internal app is a separate app: APNs only delivers its tokens with its own bundle
    /// identifier as the topic, so the backend must know which app each subscription is for.
    func testSubscriptionsNameTheAppTheyBelongTo() async throws {
        let service = HTTPPushSubscriptionRemoteService(
            client: APIClient(
                baseURL: URL(string: "https://backend.test")!,
                session: RecordingURLProtocol.session
            ),
            appID: "com.ahuguet.castellsenvena.internal"
        )

        try await service.register(
            request: PushSubscriptionRequest(
                installationID: "installation-1",
                deviceToken: "ab12",
                appVersion: "1.3 (1)",
                locale: "ca-ES",
                environment: "development"
            )
        )
        try await service.unregister(installationID: "installation-1", environment: "development")

        let requests = RecordingURLProtocol.log.take()
        XCTAssertEqual(requests.map(\.method), ["PUT", "DELETE"])
        guard requests.count == 2 else { return }
        let body = try JSONSerialization.jsonObject(with: requests[0].body) as? [String: Any]
        XCTAssertEqual(body?["device_token"] as? String, "ab12")
        XCTAssertEqual(body?["app_id"] as? String, "com.ahuguet.castellsenvena.internal")
        XCTAssertEqual(requests[1].url.path(), "/v1/push-subscriptions/installation-1")
        XCTAssertEqual(
            URLComponents(url: requests[1].url, resolvingAgainstBaseURL: false)?.queryItems,
            [
                URLQueryItem(name: "environment", value: "development"),
                URLQueryItem(name: "app_id", value: "com.ahuguet.castellsenvena.internal"),
            ]
        )
    }
}

/// Answers every request with 204 No Content, and records it.
private final class RecordingURLProtocol: URLProtocol {
    struct Request {
        let method: String
        let url: URL
        let body: Data
    }

    final class Log: @unchecked Sendable {
        private let lock = NSLock()
        private var requests: [Request] = []

        func append(_ request: Request) {
            lock.lock()
            defer { lock.unlock() }
            requests.append(request)
        }

        func take() -> [Request] {
            lock.lock()
            defer { lock.unlock() }
            let taken = requests
            requests = []
            return taken
        }
    }

    static let log = Log()

    static var session: URLSession {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [RecordingURLProtocol.self]
        return URLSession(configuration: configuration)
    }

    override class func canInit(with request: URLRequest) -> Bool { true }

    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }

    override func startLoading() {
        guard let url = request.url,
              let response = HTTPURLResponse(
                  url: url,
                  statusCode: 204,
                  httpVersion: "HTTP/1.1",
                  headerFields: nil
              )
        else { return }
        Self.log.append(
            Request(method: request.httpMethod ?? "GET", url: url, body: Self.body(of: request))
        )
        client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
        client?.urlProtocolDidFinishLoading(self)
    }

    override func stopLoading() {}

    /// URLSession hands the body to a protocol as a stream.
    private static func body(of request: URLRequest) -> Data {
        if let body = request.httpBody { return body }
        guard let stream = request.httpBodyStream else { return Data() }
        stream.open()
        defer { stream.close() }
        let capacity = 1_024
        var data = Data()
        var buffer = [UInt8](repeating: 0, count: capacity)
        while stream.hasBytesAvailable {
            let count = stream.read(&buffer, maxLength: capacity)
            guard count > 0 else { break }
            data.append(buffer, count: count)
        }
        return data
    }
}
