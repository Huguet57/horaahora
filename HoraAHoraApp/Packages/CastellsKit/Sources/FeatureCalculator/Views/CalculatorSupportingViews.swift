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

struct ConversationSharingNotice: View {
    let accept: () -> Void
    let decline: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Label("Ajuda'ns a millorar la calculadora", systemImage: "text.bubble")
                .font(.subheadline.weight(.semibold))
            Text(
                "Desem les converses noves durant 90 dies, sense cap identificador del dispositiu, per detectar errors i millorar les respostes. No hi escriguis dades personals. Ho pots canviar quan vulguis a Ajustos."
            )
            .font(.footnote)
            .foregroundStyle(.secondary)
            .fixedSize(horizontal: false, vertical: true)
            HStack(spacing: 10) {
                Button("No ho comparteixis", action: decline)
                    .buttonStyle(.bordered)
                Button("D'acord", action: accept)
                    .buttonStyle(.borderedProminent)
            }
            .controlSize(.small)
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.secondary.opacity(0.1))
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .padding(.horizontal)
        .padding(.top, 8)
    }
}
