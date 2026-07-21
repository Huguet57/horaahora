import Foundation
import Observation
import SwiftUI
import CastellsDomain
#if os(iOS)
import UIKit
#endif

@MainActor
@Observable
public final class HourByHourViewModel {
    public private(set) var items: [HourByHourItem] = []
    public private(set) var isLoading = false
    public private(set) var isLoadingMore = false
    public private(set) var isFromCache = false
    public private(set) var errorMessage: String?
    private var nextCursor: String?
    private let repository: any HourByHourRepository

    public init(repository: any HourByHourRepository) {
        self.repository = repository
    }

    public func loadIfNeeded() async {
        guard items.isEmpty, !isLoading else { return }
        await load(forceRefresh: false)
    }

    public func refresh() async {
        await load(forceRefresh: true)
    }

    public func loadNextIfNeeded(after item: HourByHourItem) async {
        guard item.id == items.last?.id, nextCursor != nil, !isLoadingMore else { return }
        isLoadingMore = true
        defer { isLoadingMore = false }
        do {
            let page = try await repository.page(cursor: nextCursor, limit: 30, forceRefresh: false)
            merge(page.items, replacing: false)
            nextCursor = page.nextCursor
            isFromCache = page.fromCache
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    public var dayGroups: [HourByHourDayGroup] {
        var orderedDays: [Date?] = []
        var grouped: [Date?: [HourByHourItem]] = [:]
        let calendar = Calendar.autoupdatingCurrent
        for item in items {
            let day = item.publishedAt.map { calendar.startOfDay(for: $0) }
            if grouped[day] == nil { orderedDays.append(day) }
            grouped[day, default: []].append(item)
        }
        return orderedDays.enumerated().map { index, day in
            HourByHourDayGroup(id: "\(index)-\(day?.timeIntervalSince1970 ?? -1)", day: day, items: grouped[day] ?? [])
        }
    }

    private func load(forceRefresh: Bool) async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            let page = try await repository.page(cursor: nil, limit: 30, forceRefresh: forceRefresh)
            merge(page.items, replacing: true)
            nextCursor = page.nextCursor
            isFromCache = page.fromCache
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func merge(_ incoming: [HourByHourItem], replacing: Bool) {
        let source = replacing ? incoming : items + incoming
        var seen = Set<String>()
        items = source.filter { seen.insert("\($0.sourceID):\($0.externalID)").inserted }
    }
}

public struct HourByHourDayGroup: Identifiable {
    public let id: String
    public let day: Date?
    public let items: [HourByHourItem]
}

public struct HourByHourRootView: View {
    @State private var model: HourByHourViewModel
    @State private var detailItem: HourByHourItem?
    @State private var notificationSettingsModel: HourByHourNotificationSettingsModel?
    @State private var showsNotificationSettings = false
    @AppStorage("castells.hour-by-hour.notification-onboarding-dismissed")
    private var notificationOnboardingDismissed = false
    private let onOpen: ((URL) -> Void)?

    public init(
        repository: any HourByHourRepository,
        notificationManager: (any HourByHourNotificationManaging)? = nil,
        onOpen: ((URL) -> Void)? = nil
    ) {
        _model = State(initialValue: HourByHourViewModel(repository: repository))
        _notificationSettingsModel = State(
            initialValue: notificationManager.map(HourByHourNotificationSettingsModel.init)
        )
        self.onOpen = onOpen
    }

    public var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                if model.items.isEmpty {
                    Group {
                        if model.isLoading {
                            ProgressView("Carregant l'Hora a Hora…")
                        } else if let error = model.errorMessage {
                            ContentUnavailableView {
                                Label("No s'ha pogut carregar", systemImage: "wifi.exclamationmark")
                            } description: {
                                Text(error)
                            } actions: {
                                Button("Torna-ho a provar") { Task { await model.refresh() } }
                            }
                        } else {
                            ContentUnavailableView(
                                "Encara no hi ha entrades",
                                systemImage: "clock"
                            )
                        }
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List {
                        if shouldShowNotificationOnboarding {
                            HourByHourNotificationOnboardingCard(
                                onConfigure: { showsNotificationSettings = true },
                                onDismiss: { notificationOnboardingDismissed = true }
                            )
                            .listRowInsets(
                                EdgeInsets(top: 8, leading: 16, bottom: 8, trailing: 16)
                            )
                            .listRowBackground(Color.clear)
                            .listRowSeparator(.hidden)
                        }

                        ForEach(model.dayGroups) { group in
                            Section(group.day?.formatted(date: .complete, time: .omitted) ?? "Sense data") {
                                ForEach(group.items) { item in
                                    HourByHourRow(
                                        item: item,
                                        onOpen: onOpen,
                                        onShowDetails: { detailItem = item }
                                    )
                                        .task { await model.loadNextIfNeeded(after: item) }
                                }
                            }
                        }
                        if model.isLoadingMore {
                            HStack { Spacer(); ProgressView(); Spacer() }
                        }
                    }
                    .hourByHourListStyle()
                    .hourByHourRemovesTopContentMargin()
                    .refreshable { await model.refresh() }
                }
            }
            .toolbar {
                if notificationSettingsModel != nil {
                    ToolbarItem(placement: .primaryAction) {
                        Button { showsNotificationSettings = true } label: {
                            Label("Configura les notificacions", systemImage: "bell")
                        }
                    }
                }
            }
            .task { await model.loadIfNeeded() }
            .task { await notificationSettingsModel?.refresh() }
            .sheet(item: $detailItem) { item in
                HourByHourDetailView(item: item)
                    .presentationDetents([.medium, .large])
                    .presentationDragIndicator(.visible)
                    .hourByHourOpaquePresentation()
            }
            .sheet(isPresented: $showsNotificationSettings) {
                if let notificationSettingsModel {
                    HourByHourNotificationSettingsView(model: notificationSettingsModel)
                        .presentationDetents([.medium, .large])
                        .presentationDragIndicator(.visible)
                        .hourByHourOpaquePresentation()
                }
            }
        }
    }

    private var shouldShowNotificationOnboarding: Bool {
        notificationSettingsModel?.status == .notDetermined
            && !notificationOnboardingDismissed
    }
}

private extension View {
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

private struct HourByHourRow: View {
    let item: HourByHourItem
    let onOpen: ((URL) -> Void)?
    let onShowDetails: () -> Void
    @Environment(\.openURL) private var openURL

    var body: some View {
        Button {
            if let associatedURL = item.associatedURL {
                if let onOpen {
                    onOpen(associatedURL)
                } else {
                    openURL(associatedURL)
                }
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
                Text(item.attribution)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                Image(systemName: linkType.systemImage)
                    .font(.caption2)
                    .foregroundStyle(.tertiary)
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

private struct HourByHourDetailView: View {
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
                    Text(sourceAttribution)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding()
            }
            .navigationTitle("Hora a Hora")
            .hourByHourInlineNavigationTitle()
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button { dismiss() } label: {
                        Image(systemName: "xmark")
                    }
                    .accessibilityLabel("Tanca")
                }
            }
        }
        .hourByHourSystemBackground()
        .accessibilityAction(.escape) { dismiss() }
    }

    private var sourceAttribution: String {
        let attribution = item.attribution.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !attribution.lowercased().hasPrefix("font:") else {
            return attribution
        }
        return "Font: \(attribution)"
    }
}
