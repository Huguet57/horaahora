import SwiftUI

struct PromptSuggestions: View {
    let select: (String) -> Void
    private let prompts = [
        "Què guanya, el 5d9f o el 4d9fa?",
        "Si la Vella descarrega el 4d10fm i la Joves el 4d9net, qui guanya?",
        "5d9f, 4d9fa, 3d10fm vs 3d10fm, 4d10fm i 3d9fa",
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Prova una comparació").font(.headline)
            ForEach(prompts, id: \.self) { prompt in
                Button { select(prompt) } label: {
                    Text(prompt).multilineTextAlignment(.leading)
                }
                .buttonStyle(.bordered)
                .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct CalculatorWelcomeView: View {
    let create: () -> Void

    var body: some View {
        ContentUnavailableView {
            Label("Calculadora castellera", systemImage: "plus.forwardslash.minus")
        } description: {
            Text("Compara castells o actuacions amb la taula oficial del Concurs 2026.")
        } actions: {
            Button("Conversa nova", action: create).buttonStyle(.borderedProminent)
        }
    }
}
