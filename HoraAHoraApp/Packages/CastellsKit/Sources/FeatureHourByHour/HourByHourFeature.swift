import Foundation
import Observation
import SwiftUI
import CastellsDomain

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
    private let onOpen: ((HourByHourItem) -> Void)?

    public init(
        repository: any HourByHourRepository,
        onOpen: ((HourByHourItem) -> Void)? = nil
    ) {
        _model = State(initialValue: HourByHourViewModel(repository: repository))
        self.onOpen = onOpen
    }

    public var body: some View {
        NavigationStack {
            Group {
                if model.isLoading && model.items.isEmpty {
                    ProgressView("Carregant l'Hora a Hora…")
                } else if model.items.isEmpty, let error = model.errorMessage {
                    ContentUnavailableView {
                        Label("No s'ha pogut carregar", systemImage: "wifi.exclamationmark")
                    } description: {
                        Text(error)
                    } actions: {
                        Button("Torna-ho a provar") { Task { await model.refresh() } }
                    }
                } else if model.items.isEmpty {
                    ContentUnavailableView("Encara no hi ha entrades", systemImage: "clock")
                } else {
                    List {
                        ForEach(model.dayGroups) { group in
                            Section(group.day?.formatted(date: .complete, time: .omitted) ?? "Sense data") {
                                ForEach(group.items) { item in
                                    HourByHourRow(item: item, onOpen: onOpen)
                                        .task { await model.loadNextIfNeeded(after: item) }
                                }
                            }
                        }
                        if model.isLoadingMore {
                            HStack { Spacer(); ProgressView(); Spacer() }
                        }
                    }
                    .hourByHourListStyle()
                    .refreshable { await model.refresh() }
                }
            }
            .navigationTitle("Hora a Hora")
            .task { await model.loadIfNeeded() }
        }
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
}

private struct HourByHourRow: View {
    let item: HourByHourItem
    let onOpen: ((HourByHourItem) -> Void)?
    @Environment(\.openURL) private var openURL

    var body: some View {
        Button {
            if let onOpen {
                onOpen(item)
            } else {
                openURL(item.actionURL)
            }
        } label: {
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
                    Image(systemName: "arrow.up.right")
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
        .buttonStyle(.plain)
        .accessibilityHint("Obre el contingut de Revista Castells")
    }
}
