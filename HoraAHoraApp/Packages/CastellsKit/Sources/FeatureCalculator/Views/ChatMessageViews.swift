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
                } else if let scorePresentation {
                    ScorePresentationView(presentation: scorePresentation)
                } else if let performanceSummary {
                    PerformanceSummaryView(presentation: performanceSummary)
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

    private var scorePresentation: ScorePresentation? {
        message.calculation.flatMap(ScorePresentation.init(response:))
    }

    private var performanceSummary: PerformanceSummaryPresentation? {
        message.calculation.flatMap(PerformanceSummaryPresentation.init(response:))
    }
}

struct ScorePresentationView: View {
    let presentation: ScorePresentation

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Label(presentation.title, systemImage: "list.number")
                .font(.caption.weight(.semibold))
                .foregroundStyle(.secondary)
            ScrollView(.horizontal, showsIndicators: false) {
                Grid(alignment: .leading, horizontalSpacing: 13, verticalSpacing: 8) {
                    rankingHeader
                    Divider().gridCellColumns(columnCount)
                    ForEach(presentation.rows) { row in
                        GridRow {
                            Text("\(row.position)")
                                .foregroundStyle(.secondary)
                                .frame(minWidth: 22, alignment: .trailing)
                            Text(row.notation)
                                .font(.caption.monospaced().weight(.semibold))
                                .foregroundStyle(
                                    row.notation == presentation.focusNotation
                                        ? Color.accentColor
                                        : Color.primary
                                )
                                .frame(minWidth: 76, alignment: .leading)
                            rankingPointCells(for: row)
                        }
                    }
                }
                .font(.caption)
                .padding(10)
            }
            .background(Color.primary.opacity(0.045))
            .clipShape(RoundedRectangle(cornerRadius: 11))
        }
        .accessibilityElement(children: .contain)
    }

    @ViewBuilder
    private var rankingHeader: some View {
        GridRow {
            Text("#").frame(minWidth: 22, alignment: .trailing)
            Text("Castell").frame(minWidth: 76, alignment: .leading)
            switch presentation.outcome {
            case .loaded:
                Text("Carregat").frame(minWidth: 66, alignment: .trailing)
            case .unloaded:
                Text("Descarregat").frame(minWidth: 86, alignment: .trailing)
            case .both:
                Text("Carregat").frame(minWidth: 66, alignment: .trailing)
                Text("Descarregat").frame(minWidth: 86, alignment: .trailing)
            }
        }
        .foregroundStyle(.secondary)
    }

    @ViewBuilder
    private func rankingPointCells(for row: ScorePresentation.Row) -> some View {
        switch presentation.outcome {
        case .loaded:
            points(row.loadedPoints, width: 66)
        case .unloaded:
            points(row.unloadedPoints, width: 86)
        case .both:
            points(row.loadedPoints, width: 66)
            points(row.unloadedPoints, width: 86)
        }
    }

    private func points(_ value: Int, width: CGFloat) -> some View {
        Text(value.formatted(.number.grouping(.automatic)))
            .monospacedDigit()
            .frame(minWidth: width, alignment: .trailing)
    }

    private var columnCount: Int {
        switch presentation.outcome {
        case .both: 4
        case .loaded, .unloaded: 3
        }
    }
}

struct PerformanceSummaryView: View {
    let presentation: PerformanceSummaryPresentation

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Label(presentation.title, systemImage: "sum")
                .font(.caption.weight(.semibold))
                .foregroundStyle(.secondary)
            VStack(spacing: 8) {
                ForEach(presentation.rows) { row in
                    HStack(alignment: .firstTextBaseline, spacing: 10) {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(row.notation).font(.caption.monospaced().weight(.semibold))
                            Text(row.result).font(.caption2).foregroundStyle(.secondary)
                        }
                        .opacity(row.counted ? 1 : 0.55)
                        Spacer()
                        Text(row.points.formatted(.number.grouping(.automatic)))
                            .font(.caption.monospacedDigit())
                            .foregroundStyle(row.counted ? .primary : .secondary)
                    }
                }
                Divider()
                HStack {
                    Text("Total").fontWeight(.semibold)
                    Spacer()
                    Text(presentation.total.formatted(.number.grouping(.automatic)))
                        .fontWeight(.bold)
                        .monospacedDigit()
                }
            }
            .padding(11)
            .background(Color.primary.opacity(0.045))
            .clipShape(RoundedRectangle(cornerRadius: 11))
        }
        .accessibilityElement(children: .contain)
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
