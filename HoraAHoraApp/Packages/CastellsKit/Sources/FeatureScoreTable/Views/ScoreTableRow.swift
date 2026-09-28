import SwiftUI

/// Both point columns share this width, so they line up with the header while scrolling.
private let pointsColumnWidth: CGFloat = 84

/// The solid part of a bar reaches the carregat points; the whole bar, the descarregat ones.
private let loadedBarStyle = Color.accentColor
private let unloadedBarStyle = Color.accentColor.opacity(0.3)

struct ScoreTableSectionHeader: View {
    let group: Int
    @ScaledMetric(relativeTo: .subheadline) private var pointsWidth = pointsColumnWidth

    var body: some View {
        HStack(alignment: .firstTextBaseline, spacing: 8) {
            Text("Grup \(group)")
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(.primary)
                .frame(maxWidth: .infinity, alignment: .leading)
            legend("Carregat", style: loadedBarStyle)
            legend("Descarregat", style: unloadedBarStyle)
        }
        .font(.caption)
        .foregroundStyle(.secondary)
        .lineLimit(1)
        .minimumScaleFactor(0.8)
        .padding(.horizontal, 20)
        .padding(.top, 14)
        .padding(.bottom, 6)
        .background(.background)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Grup \(group)")
        .accessibilityAddTraits(.isHeader)
    }

    private func legend(_ title: String, style: Color) -> some View {
        HStack(spacing: 4) {
            Rectangle()
                .fill(style)
                .frame(width: 8, height: 8)
            Text(title)
        }
        .frame(width: pointsWidth, alignment: .trailing)
    }
}

struct ScoreTableRow: View {
    enum Highlight: Equatable {
        case none
        /// The tapped castell: its carregat is the value to beat.
        case selected
        /// Its descarregat beats the carregat of the tapped castell.
        case beatsSelectedLoaded(String)
    }

    let castell: ScoreTableCastell
    let scale: ScoreBarScale
    let highlight: Highlight
    let onTap: () -> Void
    @ScaledMetric(relativeTo: .subheadline) private var pointsWidth = pointsColumnWidth

    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: 6) {
                HStack(alignment: .firstTextBaseline, spacing: 8) {
                    Text(castell.notation)
                        .font(.callout.monospaced().weight(.semibold))
                        .frame(maxWidth: .infinity, alignment: .leading)
                    points(castell.loaded, emphasized: highlight == .selected)
                        .foregroundStyle(highlight == .selected ? Color.accentColor : Color.secondary)
                    points(castell.unloaded, emphasized: beatsSelection)
                        .foregroundStyle(beatsSelection ? Color.accentColor : Color.primary)
                }
                ScoreBar(castell: castell, scale: scale)
                    .frame(height: 6)
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 8)
            .background(background)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .background {
            GeometryReader { proxy in
                Color.clear
                    .onAppear {
                        // Returning to a tab can reuse the same geometry, so onGeometryChange
                        // won't restore the row frame that onDisappear removed.
                        scale.setRowFrame(proxy.frame(in: .global), of: castell.notation)
                    }
            }
        }
        .onGeometryChange(for: CGRect.self) { proxy in
            proxy.frame(in: .global)
        } action: { frame in
            scale.setRowFrame(frame, of: castell.notation)
        }
        .onDisappear { scale.setRowFrame(nil, of: castell.notation) }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("\(castell.name), \(castell.notation)")
        .accessibilityValue(accessibilityValue)
        .accessibilityHint("Mostra quins castells de sota guanyen el seu carregat si es descarreguen")
        .accessibilityAddTraits(highlight == .selected ? .isSelected : [])
    }

    private var beatsSelection: Bool {
        if case .beatsSelectedLoaded = highlight { return true }
        return false
    }

    private var background: Color {
        switch highlight {
        case .none: .clear
        case .selected: Color.accentColor.opacity(0.16)
        case .beatsSelectedLoaded: Color.accentColor.opacity(0.06)
        }
    }

    private var accessibilityValue: String {
        let points = "Carregat, \(formatted(castell.loaded)) punts. "
            + "Descarregat, \(formatted(castell.unloaded)) punts."
        guard case let .beatsSelectedLoaded(selected) = highlight else { return points }
        return points + " El descarregat guanya el carregat del \(selected)."
    }

    private func points(_ value: Int, emphasized: Bool) -> some View {
        Text(formatted(value))
            .font(.subheadline.monospacedDigit().weight(emphasized ? .semibold : .regular))
            .frame(width: pointsWidth, alignment: .trailing)
    }

    private func formatted(_ value: Int) -> String {
        value.formatted(.number.grouping(.automatic))
    }
}

/// A bar on the scale of the rows on screen, with square ends so that they compare exactly:
/// solid up to carregat, light up to descarregat.
private struct ScoreBar: View {
    let castell: ScoreTableCastell
    let scale: ScoreBarScale

    var body: some View {
        GeometryReader { proxy in
            ZStack(alignment: .leading) {
                Rectangle()
                    .fill(unloadedBarStyle)
                    .frame(width: proxy.size.width * scale.axis.fraction(of: castell.unloaded))
                Rectangle()
                    .fill(loadedBarStyle)
                    .frame(width: proxy.size.width * scale.axis.fraction(of: castell.loaded))
            }
        }
        .opacity(scale.castellsInWindow.contains(castell.notation) ? 1 : 0)
        .accessibilityHidden(true)
    }
}
