import SwiftUI

/// The internal development app: what the public app has, plus Hora a Hora, Agenda, their
/// settings and the news notifications.
@main
struct InternalApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate
    private let dependencies: InternalAppDependencies

    init() {
        do {
            dependencies = try InternalAppDependencies()
        } catch {
            fatalError("No s'ha pogut preparar la persistència local: \(error.localizedDescription)")
        }
    }

    var body: some Scene {
        WindowGroup {
            InternalContentView(dependencies: dependencies)
                .task {
                    appDelegate.setTokenUpdateHandler { token in
                        Task {
                            await dependencies.pushSubscriptionCoordinator
                                .didReceiveDeviceToken(token)
                        }
                    }
                }
        }
    }
}
