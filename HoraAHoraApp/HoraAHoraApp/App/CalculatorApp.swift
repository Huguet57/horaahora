import SwiftUI

/// La calculadora de l'Aleta: Calculadora, Comparador, Puntuacions and Ajustos.
@main
struct CalculatorApp: App {
    private let dependencies: AppDependencies

    init() {
        do {
            dependencies = try AppDependencies(configuration: .live(), userDefaults: .standard)
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
