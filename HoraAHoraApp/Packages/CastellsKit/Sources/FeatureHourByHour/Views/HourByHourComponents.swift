import SwiftUI
import CastellsDomain
#if os(iOS)
import UIKit
#endif

extension View {
    @ViewBuilder
    func hourByHourListStyle() -> some View {
        #if os(iOS)
        listStyle(.insetGrouped)
        #else
        self
        #endif
    }

    @ViewBuilder
    func hourByHourRemovesTopContentMargin() -> some View {
        #if os(iOS)
        contentMargins(.top, 0, for: .scrollContent)
        #else
        self
        #endif
    }

    @ViewBuilder
    func hourByHourLargeNavigationTitle() -> some View {
        #if os(iOS)
        navigationBarTitleDisplayMode(.large)
        #else
        self
        #endif
    }

    @ViewBuilder
    func hourByHourInlineNavigationTitle() -> some View {
        #if os(iOS)
        navigationBarTitleDisplayMode(.inline)
        #else
        self
        #endif
    }

    @ViewBuilder
    func hourByHourOpaquePresentation() -> some View {
        #if os(iOS)
        presentationBackground(Color(uiColor: .systemBackground))
        #else
        self
        #endif
    }

    @ViewBuilder
    func hourByHourSystemBackground() -> some View {
        #if os(iOS)
        background(Color(uiColor: .systemBackground).ignoresSafeArea())
        #else
        self
        #endif
    }
}

struct HourByHourRow: View {
    let item: HourByHourItem
    let onOpen: ((URL) -> Void)?
    let onShowDetails: () -> Void
    @Environment(\.openURL) private var openURL

    var body: some View {
        Button {
            if let associatedURL = item.associatedURL {
                if let onOpen { onOpen(associatedURL) } else { openURL(associatedURL) }
            } else {
                onShowDetails()
            }
        } label: {
            rowContent(linkType: item.associatedURL == nil ? .details : .external)
        }
        .buttonStyle(.plain)
        .accessibilityHint(
            item.associatedURL == nil
                ? "Mostra el text complet dins l'app"
                : "Obre el contingut de Revista Castells"
        )
    }

    private func rowContent(linkType: LinkType) -> some View {
        VStack(alignment: .leading, spacing: 7) {
            HStack(alignment: .firstTextBaseline) {
                if let publishedAt = item.publishedAt {
                    Text(publishedAt, style: .time)
                        .font(.caption.monospacedDigit())
                        .foregroundStyle(.secondary)
                }
                Spacer()
                Text(item.attribution).font(.caption2).foregroundStyle(.secondary)
                Image(systemName: linkType.systemImage).font(.caption2).foregroundStyle(.tertiary)
            }
            Text(item.displayTitle)
                .font(.headline)
                .foregroundStyle(.primary)
                .multilineTextAlignment(.leading)
            if !item.summary.isEmpty {
                Text(item.summary)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .lineLimit(3)
                    .multilineTextAlignment(.leading)
            }
        }
        .padding(.vertical, 4)
    }

    private enum LinkType {
        case details
        case external

        var systemImage: String {
            switch self {
            case .details: "chevron.right"
            case .external: "arrow.up.right"
            }
        }
    }
}

struct HourByHourDetailView: View {
    let item: HourByHourItem
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    if let publishedAt = item.publishedAt {
                        Text(publishedAt.formatted(date: .complete, time: .shortened))
                            .font(.subheadline.monospacedDigit())
                            .foregroundStyle(.secondary)
                    }
                    Text(item.displayTitle)
                        .font(.title2.weight(.bold))
                        .fixedSize(horizontal: false, vertical: true)
                    if !item.summary.isEmpty {
                        Divider()
                        Text(item.summary)
                            .font(.body)
                            .foregroundStyle(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                            .textSelection(.enabled)
                    }
                    Divider()
                    Text(sourceAttribution).font(.caption).foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding()
            }
            .navigationTitle("Hora a Hora")
            .hourByHourInlineNavigationTitle()
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button { dismiss() } label: { Image(systemName: "xmark") }
                        .accessibilityLabel("Tanca")
                }
            }
        }
        .hourByHourSystemBackground()
        .accessibilityAction(.escape) { dismiss() }
    }

    private var sourceAttribution: String {
        let attribution = item.attribution.trimmingCharacters(in: .whitespacesAndNewlines)
        return attribution.lowercased().hasPrefix("font:") ? attribution : "Font: \(attribution)"
    }
}
