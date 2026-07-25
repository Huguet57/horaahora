import SwiftUI

@main
struct HoraAHoraApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate
    private let dependencies: AppDependencies

    init() {
        do {
            dependencies = try AppDependencies()
        } catch {
            fatalError("No s'ha pogut preparar la persistència local: \(error.localizedDescription)")
        }
    }

    var body: some Scene {
        WindowGroup {
            ContentView(dependencies: dependencies)
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
