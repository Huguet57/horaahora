import SwiftUI

struct ContentView: View {
    @State private var deviceToken: String = "Esperant token..."

    var body: some View {
        VStack(spacing: 24) {
            Text("Castells Hora a Hora")
                .font(.title2)
                .fontWeight(.bold)

            VStack(spacing: 8) {
                Text("Device Token")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                Text(deviceToken)
                    .font(.system(.footnote, design: .monospaced))
                    .multilineTextAlignment(.center)
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(8)
                    .textSelection(.enabled)
            }

            Button("Copiar token") {
                UIPasteboard.general.string = deviceToken
            }
            .buttonStyle(.borderedProminent)
            .disabled(deviceToken.starts(with: "Esperant") || deviceToken.starts(with: "Error"))
        }
        .padding()
        .onAppear {
            AppDelegate.shared?.onTokenUpdate = { token in
                deviceToken = token
            }
            if let existing = AppDelegate.shared?.deviceToken, !existing.isEmpty {
                deviceToken = existing
            }
        }
    }
}
