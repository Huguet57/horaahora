import Foundation

public struct PushSubscriptionRequest: Encodable, Equatable, Sendable {
    public let installationID: String
    public let deviceToken: String
    public let appVersion: String
    public let locale: String
    public let environment: String

    public init(
        installationID: String,
        deviceToken: String,
        appVersion: String,
        locale: String,
        environment: String
    ) {
        self.installationID = installationID
        self.deviceToken = deviceToken
        self.appVersion = appVersion
        self.locale = locale
        self.environment = environment
    }
}

public protocol PushSubscriptionRemoteService: Sendable {
    func register(request: PushSubscriptionRequest) async throws
    func unregister(installationID: String, environment: String) async throws
}

public struct HTTPPushSubscriptionRemoteService: PushSubscriptionRemoteService {
    private let client: APIClient

    public init(client: APIClient) {
        self.client = client
    }

    public func register(request: PushSubscriptionRequest) async throws {
        try await client.put(
            path: "/v1/push-subscriptions/\(request.installationID)",
            body: PushSubscriptionBody(
                deviceToken: request.deviceToken,
                appVersion: request.appVersion,
                locale: request.locale,
                environment: request.environment
            )
        )
    }

    public func unregister(installationID: String, environment: String) async throws {
        try await client.delete(
            path: "/v1/push-subscriptions/\(installationID)",
            queryItems: [URLQueryItem(name: "environment", value: environment)]
        )
    }
}

public actor PushSubscriptionCoordinator {
    private let remoteService: any PushSubscriptionRemoteService
    private let installationID: String
    private let appVersion: String
    private let locale: String
    private let environment: String

    private var desiredEnabled = false
    private var currentDeviceToken: String?
    private var synchronizedDeviceToken: String?
    private var isUnregistered = false

    public init(
        remoteService: any PushSubscriptionRemoteService,
        installationID: String,
        appVersion: String,
        locale: String,
        environment: String
    ) {
        self.remoteService = remoteService
        self.installationID = installationID
        self.appVersion = appVersion
        self.locale = locale
        self.environment = environment
    }

    public func setEnabled(_ enabled: Bool) async {
        desiredEnabled = enabled
        await synchronize()
    }

    public func didReceiveDeviceToken(_ token: String) async {
        guard token != currentDeviceToken || synchronizedDeviceToken == nil else { return }
        currentDeviceToken = token
        isUnregistered = false
        await synchronize()
    }

    private func synchronize() async {
        if desiredEnabled {
            guard let currentDeviceToken,
                  synchronizedDeviceToken != currentDeviceToken else { return }
            do {
                try await remoteService.register(
                    request: PushSubscriptionRequest(
                        installationID: installationID,
                        deviceToken: currentDeviceToken,
                        appVersion: appVersion,
                        locale: locale,
                        environment: environment
                    )
                )
                synchronizedDeviceToken = currentDeviceToken
                isUnregistered = false
            } catch {
                // A later foreground refresh or APNs callback retries the registration.
            }
        } else {
            guard !isUnregistered else { return }
            do {
                try await remoteService.unregister(
                    installationID: installationID,
                    environment: environment
                )
                isUnregistered = true
                synchronizedDeviceToken = nil
            } catch {
                // Keep the pending state so the next synchronization retries the deletion.
            }
        }
    }
}

private struct PushSubscriptionBody: Encodable, Sendable {
    let deviceToken: String
    let appVersion: String
    let locale: String
    let environment: String
}
