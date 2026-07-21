import SwiftData
import SwiftUI
import CastellsData
import CastellsDomain
import FeatureHourByHour

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
        }
    }
}

@MainActor
final class AppDependencies {
    let modelContainer: ModelContainer
    let hourByHourRepository: any HourByHourRepository
    let hourByHourNotificationManager: any HourByHourNotificationManaging
    let agendaRepository: any AgendaRepository
    let chatRepository: any ChatRepository

    init(baseURL: URL = AppConfiguration.apiBaseURL) throws {
        let modelContainer = try DataStack.makeModelContainer()
        let client = APIClient(baseURL: baseURL)

        self.modelContainer = modelContainer
        self.hourByHourRepository = CachedHourByHourRepository(
            container: modelContainer,
            remoteService: HTTPHourByHourRemoteService(client: client)
        )
        self.hourByHourNotificationManager = IOSHourByHourNotificationManager()
        self.agendaRepository = CachedAgendaRepository(
            container: modelContainer,
            remoteService: HTTPAgendaRemoteService(client: client)
        )
        self.chatRepository = SwiftDataChatRepository(
            container: modelContainer,
            remoteService: HTTPChatRemoteService(client: client)
        )
    }
}

enum AppConfiguration {
    private static let productionAPIBaseURL = "https://castells-superapp-poc.vercel.app"

    static var apiBaseURL: URL {
        let configured = ProcessInfo.processInfo.environment["CASTELLS_API_BASE_URL"]
            ?? Bundle.main.object(forInfoDictionaryKey: "CastellsAPIBaseURL") as? String
            ?? productionAPIBaseURL
        guard let url = URL(string: configured) else {
            preconditionFailure("CastellsAPIBaseURL no és una URL vàlida")
        }
        return url
    }
}
