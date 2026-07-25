import SwiftUI

struct HourByHourSkeletonView: View {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var isPulsing = false

    var body: some View {
        List {
            ForEach(0..<2, id: \.self) { section in
                Section {
                    ForEach(0..<3, id: \.self) { row in
                        HourByHourSkeletonRow(
                            showsSecondSummaryLine: (section + row).isMultiple(of: 2)
                        )
                        .opacity(placeholderOpacity)
                    }
                } header: {
                    Text("Dissabte, 25 de juliol")
                        .redacted(reason: .placeholder)
                        .opacity(placeholderOpacity)
                }
            }
        }
        .hourByHourListStyle()
        .hourByHourRemovesTopContentMargin()
        .allowsHitTesting(false)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Carregant l'Hora a Hora")
        .onAppear {
            guard !reduceMotion else { return }
            withAnimation(.easeInOut(duration: 0.85).repeatForever(autoreverses: true)) {
                isPulsing = true
            }
        }
    }

    private var placeholderOpacity: Double {
        guard !reduceMotion else { return 0.72 }
        return isPulsing ? 0.45 : 0.78
    }
}

private struct HourByHourSkeletonRow: View {
    let showsSecondSummaryLine: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 7) {
            HStack(alignment: .firstTextBaseline) {
                Text("00:00")
                    .font(.caption.monospacedDigit())
                Spacer()
                Text("Revista Castells")
                    .font(.caption2)
                Image(systemName: "arrow.up.right")
                    .font(.caption2)
            }

            Text("Una actualització important del món casteller")
                .font(.headline)
                .lineLimit(1)

            Text(
                showsSecondSummaryLine
                    ? "La informació més recent de la jornada castellera en dues línies de resum."
                    : "La informació més recent de la jornada."
            )
            .font(.subheadline)
            .lineLimit(2)
        }
        .padding(.vertical, 4)
        .redacted(reason: .placeholder)
    }
}
