import Foundation
import CastellsDomain

public struct PushSubscriptionRequest: Encodable, Equatable, Sendable {
    public let installationID: String
    public let deviceToken: String
    public let appVersion: String
    public let locale: String
    public let environment: String
    public let minimumInterest: NotificationInterestLevel
    public let groupSelection: NotificationGroupSelection

    public init(
        installationID: String,
        deviceToken: String,
        appVersion: String,
        locale: String,
        environment: String,
        minimumInterest: NotificationInterestLevel = .high,
        groupSelection: NotificationGroupSelection = .init()
    ) {
        self.installationID = installationID
        self.deviceToken = deviceToken
        self.appVersion = appVersion
        self.locale = locale
        self.environment = environment
        self.minimumInterest = minimumInterest
        self.groupSelection = groupSelection
    }
}

public protocol PushSubscriptionRemoteService: Sendable {
    func register(request: PushSubscriptionRequest) async throws
    func unregister(installationID: String, environment: String) async throws
}

/// Registers and removes the subscription of this app. `appID` is its bundle identifier: the
/// internal app is a separate app, and the backend keeps its subscriptions apart from the public
/// app's, because APNs only delivers each token with its own app as the topic.
public struct HTTPPushSubscriptionRemoteService: PushSubscriptionRemoteService {
    private let client: APIClient
    private let appID: String

    public init(client: APIClient, appID: String) {
        self.client = client
        self.appID = appID
    }

    public func register(request: PushSubscriptionRequest) async throws {
        try await client.put(
            path: "/v1/push-subscriptions/\(request.installationID)",
            body: PushSubscriptionBody(
                deviceToken: request.deviceToken,
                appVersion: request.appVersion,
                locale: request.locale,
                environment: request.environment,
                minimumInterest: request.minimumInterest,
                groupSelection: request.groupSelection,
                appID: appID
            )
        )
    }

    public func unregister(installationID: String, environment: String) async throws {
        try await client.delete(
            path: "/v1/push-subscriptions/\(installationID)",
            queryItems: [
                URLQueryItem(name: "environment", value: environment),
                URLQueryItem(name: "app_id", value: appID),
            ]
        )
    }
}

private struct PushSubscriptionBody: Encodable, Sendable {
    let deviceToken: String
    let appVersion: String
    let locale: String
    let environment: String
    let minimumInterest: NotificationInterestLevel
    let groupSelection: NotificationGroupSelection
    let appID: String
}
