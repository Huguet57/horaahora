import SwiftUI
import CastellsDomain

struct MessageBubble: View {
    let message: ChatMessage
    let retry: () -> Void

    var body: some View {
        HStack {
            if message.role == .user { Spacer(minLength: 44) }
            VStack(alignment: .leading, spacing: 8) {
                if let comparison {
                    Text(comparison.summary).textSelection(.enabled)
                    Divider()
                    ComparisonTable(presentation: comparison)
                } else {
                    Text(message.content).textSelection(.enabled)
                    if let calculation = message.calculation, !calculation.performances.isEmpty {
                        Divider()
                        ForEach(calculation.performances, id: \.label) { performance in
                            HStack {
                                Text(performance.label).fontWeight(.semibold)
                                Spacer()
                                Text(performance.total.formatted(.number.grouping(.automatic)))
                                    .monospacedDigit()
                            }
                            .font(.caption)
                        }
                    }
                }
                if message.deliveryState == .failed {
                    Button("Torna-ho a provar", action: retry).font(.caption)
                }
            }
            .padding(11)
            .background(message.role == .user ? Color.accentColor : Color.secondary.opacity(0.12))
            .foregroundStyle(message.role == .user ? Color.white : Color.primary)
            .clipShape(RoundedRectangle(cornerRadius: 16))
            if message.role == .assistant { Spacer(minLength: 44) }
        }
    }

    private var comparison: ComparisonPresentation? {
        message.calculation.flatMap(ComparisonPresentation.init(response:))
    }
}

struct ComparisonTable: View {
    let presentation: ComparisonPresentation

    var body: some View {
        VStack(alignment: .leading, spacing: 9) {
            Label("Comparativa", systemImage: "tablecells")
                .font(.caption.weight(.semibold))
                .foregroundStyle(.secondary)
            ScrollView(.horizontal, showsIndicators: false) {
                Grid(alignment: .leading, horizontalSpacing: 14, verticalSpacing: 8) {
                    GridRow {
                        Text("Castell").foregroundStyle(.secondary)
                        ForEach(presentation.columns) { column in
                            HStack(spacing: 4) {
                                if column.isWinner {
                                    Image(systemName: "trophy.fill").foregroundStyle(.yellow)
                                }
                                Text(column.label).fontWeight(.semibold).lineLimit(1)
                            }
                            .frame(minWidth: 112, alignment: .trailing)
                        }
                    }
                    .font(.caption)
                    Divider().gridCellColumns(presentation.columns.count + 1)
                    ForEach(0..<presentation.maximumCastellCount, id: \.self) { index in
                        GridRow {
                            Text("\(index + 1)").font(.caption2).foregroundStyle(.tertiary)
                            ForEach(presentation.columns) { column in
                                castellCell(column, at: index)
                            }
                        }
                    }
                    Divider().gridCellColumns(presentation.columns.count + 1)
                    GridRow {
                        Text("Total").fontWeight(.semibold)
                        ForEach(presentation.columns) { column in
                            Text(column.total.formatted(.number.grouping(.automatic)))
                                .fontWeight(.bold)
                                .monospacedDigit()
                                .frame(minWidth: 112, alignment: .trailing)
                        }
                    }
                    .font(.caption)
                }
                .padding(10)
            }
            .background(Color.primary.opacity(0.045))
            .clipShape(RoundedRectangle(cornerRadius: 11))

            if let winner = presentation.winnerLabel, let margin = presentation.margin {
                Label(
                    "\(winner), +\(margin.formatted(.number.grouping(.automatic))) punts",
                    systemImage: "trophy.fill"
                )
                .font(.caption.weight(.semibold))
                .foregroundStyle(.primary)
            } else {
                Label("Empat", systemImage: "equal.circle.fill")
                    .font(.caption.weight(.semibold))
            }
        }
    }

    @ViewBuilder
    private func castellCell(_ column: ComparisonPresentation.Column, at index: Int) -> some View {
        if column.castells.indices.contains(index) {
            let castell = column.castells[index]
            VStack(alignment: .trailing, spacing: 2) {
                Text(castell.notation).font(.caption.monospaced().weight(.semibold))
                Text(detail(for: castell)).font(.caption2).foregroundStyle(.secondary)
            }
            .frame(minWidth: 112, alignment: .trailing)
            .opacity(castell.counted ? 1 : 0.55)
        } else {
            Text("—").foregroundStyle(.tertiary).frame(minWidth: 112, alignment: .trailing)
        }
    }

    private func detail(for castell: ComparisonPresentation.Castell) -> String {
        let points = castell.points.formatted(.number.grouping(.automatic))
        let suffix = castell.counted ? "" : " · no compta"
        return "\(castell.result) · \(points)\(suffix)"
    }
}
