import SwiftUI

/// La calculadora de l'Aleta as it is in the App Store: Calculadora, Puntuacions and Ajustos.
@main
struct PublicApp: App {
    private let dependencies: PublicAppDependencies

    init() {
        do {
            dependencies = try PublicAppDependencies()
        } catch {
            fatalError("No s'ha pogut preparar la persistència local: \(error.localizedDescription)")
        }
    }

    var body: some Scene {
        WindowGroup {
            PublicContentView(dependencies: dependencies)
        }
    }
}
