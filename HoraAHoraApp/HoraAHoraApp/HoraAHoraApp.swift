import SwiftData
import SwiftUI
import CastellsData
import CastellsDomain

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
    static var apiBaseURL: URL {
        let configured = ProcessInfo.processInfo.environment["CASTELLS_API_BASE_URL"]
            ?? Bundle.main.object(forInfoDictionaryKey: "CastellsAPIBaseURL") as? String
            ?? "http://127.0.0.1:8000"
        guard let url = URL(string: configured) else {
            preconditionFailure("CastellsAPIBaseURL no és una URL vàlida")
        }
        return url
    }
}
