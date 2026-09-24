import Foundation
import CastellsDomain

public actor PushSubscriptionCoordinator {
    private let remoteService: any PushSubscriptionRemoteService
    private let installationID: String
    private let appVersion: String
    private let locale: String
    private let environment: String
    private var desiredEnabled = false
    private var minimumInterest: NotificationInterestLevel = .high
    private var groupSelection = NotificationGroupSelection()
    private var currentDeviceToken: String?
    private var synchronizedRequest: PushSubscriptionRequest?
    private var isUnregistered = false
    private var isSynchronizing = false
    private var hasRequestedSynchronization = false
    private var generation = 0
    private var onSynchronizationChanged: (@MainActor @Sendable (Bool) -> Void)?

    public init(remoteService: any PushSubscriptionRemoteService, installationID: String,
                appVersion: String, locale: String, environment: String) {
        self.remoteService = remoteService
        self.installationID = installationID
        self.appVersion = appVersion
        self.locale = locale
        self.environment = environment
    }

    public var isSynchronizationPending: Bool {
        guard hasRequestedSynchronization else { return false }
        return desiredEnabled
            ? desiredRequest == nil || desiredRequest != synchronizedRequest
            : !isUnregistered
    }

    public func observeSynchronization(_ handler: @escaping @MainActor @Sendable (Bool) -> Void) async {
        onSynchronizationChanged = handler
        await publishState()
    }

    public func setEnabled(_ enabled: Bool) async {
        generation += 1
        desiredEnabled = enabled
        hasRequestedSynchronization = true
        await synchronize()
    }

    public func setPreferences(minimumInterest: NotificationInterestLevel,
                               groupSelection: NotificationGroupSelection) async {
        generation += 1
        self.minimumInterest = minimumInterest
        self.groupSelection = groupSelection
        // Preferences are local until notifications have been enabled/disabled explicitly.
        guard hasRequestedSynchronization else { return }
        await synchronize()
    }

    public func didReceiveDeviceToken(_ token: String) async {
        generation += 1
        currentDeviceToken = token
        guard hasRequestedSynchronization else { return }
        await synchronize()
    }

    private var desiredRequest: PushSubscriptionRequest? {
        guard let currentDeviceToken else { return nil }
        return PushSubscriptionRequest(
            installationID: installationID, deviceToken: currentDeviceToken,
            appVersion: appVersion, locale: locale, environment: environment,
            minimumInterest: minimumInterest, groupSelection: groupSelection
        )
    }

    private func synchronize() async {
        // Actors are reentrant across await. One draining loop owns network writes;
        // concurrent callers only replace the desired state for its next iteration.
        guard !isSynchronizing else { return }
        isSynchronizing = true
        while isSynchronizationPending {
            if desiredEnabled {
                guard let request = desiredRequest else { break }
                do {
                    try await remoteService.register(request: request)
                    synchronizedRequest = request
                    isUnregistered = false
                } catch {
                    if !desiredEnabled || request != desiredRequest { continue }
                    break
                }
            } else {
                do {
                    try await remoteService.unregister(installationID: installationID, environment: environment)
                    isUnregistered = true
                    synchronizedRequest = nil
                } catch {
                    if desiredEnabled { continue }
                    break
                }
            }
        }
        let completedGeneration = generation
        await publishState()
        isSynchronizing = false
        if generation != completedGeneration && isSynchronizationPending {
            await synchronize()
        }
    }

    private func publishState() async {
        await onSynchronizationChanged?(isSynchronizationPending)
    }
}
