import Foundation
import Observation
import SwiftUI
import CastellsDomain

@MainActor
@Observable
public final class AgendaViewModel {
    public var selectedDate = Date()
    public private(set) var monthEvents: [CastellEvent] = []
    public private(set) var isLoading = false
    public private(set) var errorMessage: String?
    public private(set) var isFromCache = false
    public private(set) var sourceStatus: AgendaSourceStatus = .unavailable
    public let officialURL: URL
    private let repository: any AgendaRepository

    public init(repository: any AgendaRepository) {
        self.repository = repository
        self.officialURL = repository.officialURL
    }

    public var events: [CastellEvent] {
        let selectedKey = Self.localDateKey(selectedDate)
        return monthEvents.filter { $0.localDate == selectedKey }
    }

    public var eventDateKeys: Set<String> {
        Set(monthEvents.map(\.localDate))
    }

    public func select(_ date: Date) {
        selectedDate = date
    }

    public func changeMonth(by offset: Int) async {
        guard let date = Self.calendar.date(byAdding: .month, value: offset, to: selectedDate) else {
            return
        }
        selectedDate = date
        await load()
    }

    public func load(forceRefresh: Bool = false) async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        let calendar = Self.calendar
        guard
            let monthInterval = calendar.dateInterval(of: .month, for: selectedDate),
            let end = calendar.date(byAdding: .day, value: -1, to: monthInterval.end)
        else { return }
        let start = monthInterval.start
        do {
            var cursor: String?
            var collected: [CastellEvent] = []
            var allFromCache = true
            repeat {
                let page = try await repository.events(
                    from: start,
                    to: end,
                    group: nil,
                    municipality: nil,
                    cursor: cursor,
                    limit: 100,
                    forceRefresh: forceRefresh && cursor == nil
                )
                collected.append(contentsOf: page.items)
                allFromCache = allFromCache && page.fromCache
                sourceStatus = page.sourceStatus
                cursor = page.nextCursor
            } while cursor != nil

            var seen = Set<String>()
            monthEvents = collected
                .filter { seen.insert("\($0.sourceID):\($0.externalID)").inserted }
                .sorted {
                    if $0.localDate == $1.localDate { return $0.sourceOrder < $1.sourceOrder }
                    return $0.localDate < $1.localDate
                }
            isFromCache = allFromCache
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private static var calendar: Calendar {
        var calendar = Calendar(identifier: .gregorian)
        calendar.locale = Locale(identifier: "ca_ES")
        calendar.timeZone = TimeZone(identifier: "Europe/Madrid")!
        calendar.firstWeekday = 2
        return calendar
    }

    private static func localDateKey(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.calendar = calendar
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = calendar.timeZone
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: date)
    }
}

public struct AgendaRootView: View {
    @State private var model: AgendaViewModel

    public init(repository: any AgendaRepository) {
        _model = State(initialValue: AgendaViewModel(repository: repository))
    }

    public var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    AgendaCalendarView(
                        selectedDate: model.selectedDate,
                        eventDateKeys: model.eventDateKeys,
                        onSelect: { model.select($0) },
                        onChangeMonth: { offset in
                            Task { await model.changeMonth(by: offset) }
                        }
                    )

                    if model.isLoading && model.events.isEmpty {
                        ProgressView()
                    } else if !model.events.isEmpty {
                        LazyVStack(alignment: .leading, spacing: 12) {
                            ForEach(model.events) { event in
                                AgendaEventCard(event: event)
                            }
                        }
                    } else if model.errorMessage != nil {
                        OfficialAgendaFallback(
                            officialURL: model.officialURL,
                            message: "No s'ha pogut connectar al servidor."
                        ) {
                            Task { await model.load(forceRefresh: true) }
                        }
                    } else if model.sourceStatus == .unavailable {
                        OfficialAgendaFallback(
                            officialURL: model.officialURL,
                            message: "Les dades natives no estan disponibles ara mateix."
                        ) {
                            Task { await model.load(forceRefresh: true) }
                        }
                    } else {
                        ContentUnavailableView {
                            Label("No hi ha actuacions", systemImage: "calendar")
                        } description: {
                            Text("No consten actuacions per al dia seleccionat.")
                        } actions: {
                            Link("Consulta l'agenda oficial", destination: model.officialURL)
                        }
                    }
                }
                .padding()
            }
            .refreshable { await model.load(forceRefresh: true) }
            .navigationTitle("Agenda")
            .task { await model.load() }
        }
    }
}

private struct OfficialAgendaFallback: View {
    let officialURL: URL
    let message: String
    let retry: () -> Void

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: "wifi.exclamationmark")
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(.secondary)
                .frame(width: 24, height: 24)

            VStack(alignment: .leading, spacing: 8) {
                Text("Agenda temporalment no disponible")
                    .font(.subheadline.weight(.semibold))

                Text(message)
                    .font(.caption)
                    .foregroundStyle(.secondary)

                HStack(spacing: 16) {
                    Button(action: retry) {
                        Label("Torna-ho a provar", systemImage: "arrow.clockwise")
                    }

                    Link(destination: officialURL) {
                        Label("Agenda oficial", systemImage: "arrow.up.right")
                    }
                }
                .font(.caption.weight(.medium))
                .buttonStyle(.plain)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(14)
        .background(.quaternary.opacity(0.5), in: RoundedRectangle(cornerRadius: 12))
    }
}

private struct AgendaCalendarView: View {
    let selectedDate: Date
    let eventDateKeys: Set<String>
    let onSelect: (Date) -> Void
    let onChangeMonth: (Int) -> Void

    private let columns = Array(repeating: GridItem(.flexible(), spacing: 4), count: 7)
    private let weekdays = ["DL", "DT", "DC", "DJ", "DV", "DS", "DG"]

    var body: some View {
        VStack(spacing: 14) {
            HStack {
                Text(monthTitle)
                    .font(.title3.weight(.semibold))
                Spacer()
                Button { onChangeMonth(-1) } label: {
                    Image(systemName: "chevron.left")
                        .font(.title2.weight(.semibold))
                        .frame(width: 44, height: 44)
                }
                .accessibilityLabel("Mes anterior")
                Button { onChangeMonth(1) } label: {
                    Image(systemName: "chevron.right")
                        .font(.title2.weight(.semibold))
                        .frame(width: 44, height: 44)
                }
                .accessibilityLabel("Mes següent")
            }

            LazyVGrid(columns: columns, spacing: 8) {
                ForEach(weekdays, id: \.self) { weekday in
                    Text(weekday)
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.tertiary)
                }

                ForEach(0..<leadingBlankCount, id: \.self) { _ in
                    Color.clear.frame(height: 42)
                }

                ForEach(daysInMonth, id: \.self) { date in
                    dayButton(date)
                }
            }
        }
    }

    private func dayButton(_ date: Date) -> some View {
        let selected = calendar.isDate(date, inSameDayAs: selectedDate)
        let today = calendar.isDateInToday(date)
        let isPast = calendar.compare(date, to: Date(), toGranularity: .day) == .orderedAscending
        let hasEvents = eventDateKeys.contains(localDateKey(date))
        return Button { onSelect(date) } label: {
            ZStack {
                Circle()
                    .fill(selected ? Color.accentColor : .clear)
                    .frame(width: 42, height: 42)
                VStack(spacing: 1) {
                    Text(String(calendar.component(.day, from: date)))
                        .font(.body.monospacedDigit())
                        .foregroundStyle(selected ? Color.white : today ? Color.accentColor : Color.primary)
                    Circle()
                        .fill(hasEvents ? (selected ? Color.white : Color.accentColor) : .clear)
                        .frame(width: 5, height: 5)
                }
            }
            .frame(maxWidth: .infinity, minHeight: 44)
        }
        .buttonStyle(.plain)
        .opacity(isPast && !selected ? 0.35 : 1)
        .accessibilityLabel(accessibilityDate(date))
        .accessibilityAddTraits(selected ? .isSelected : [])
        .accessibilityHint(hasEvents ? "Té actuacions" : "")
    }

    private var calendar: Calendar {
        var value = Calendar(identifier: .gregorian)
        value.locale = Locale(identifier: "ca_ES")
        value.timeZone = TimeZone(identifier: "Europe/Madrid")!
        value.firstWeekday = 2
        return value
    }

    private var monthStart: Date {
        calendar.dateInterval(of: .month, for: selectedDate)!.start
    }

    private var leadingBlankCount: Int {
        (calendar.component(.weekday, from: monthStart) + 5) % 7
    }

    private var daysInMonth: [Date] {
        let count = calendar.range(of: .day, in: .month, for: monthStart)?.count ?? 0
        return (0..<count).compactMap { calendar.date(byAdding: .day, value: $0, to: monthStart) }
    }

    private var monthTitle: String {
        let formatter = DateFormatter()
        formatter.calendar = calendar
        formatter.locale = Locale(identifier: "ca_ES")
        formatter.timeZone = calendar.timeZone
        formatter.dateFormat = "LLLL 'del' yyyy"
        return formatter.string(from: monthStart)
    }

    private func localDateKey(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.calendar = calendar
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = calendar.timeZone
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: date)
    }

    private func accessibilityDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.calendar = calendar
        formatter.locale = Locale(identifier: "ca_ES")
        formatter.timeZone = calendar.timeZone
        formatter.dateStyle = .full
        return formatter.string(from: date)
    }
}

private struct AgendaEventCard: View {
    let event: CastellEvent

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .firstTextBaseline) {
                Label(event.timeLabel, systemImage: "clock")
                    .font(.subheadline.weight(.semibold))
                Spacer()
                Text(event.municipality)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }

            Text(event.title)
                .font(.headline)

            if !event.venue.isEmpty,
               let mapsURL = googleMapsSearchURL(
                   venue: event.venue,
                   municipality: event.municipality
               ) {
                Link(destination: mapsURL) {
                    Label(event.venue, systemImage: "mappin.and.ellipse")
                        .font(.subheadline)
                }
                .accessibilityLabel("Obre \(event.venue) a Google Maps")
            }

            if !event.participatingGroups.isEmpty {
                VStack(alignment: .leading, spacing: 3) {
                    ForEach(event.participatingGroups, id: \.self) { group in
                        Text("• \(group)")
                    }
                }
                .font(.subheadline)
            }

            if !event.notes.isEmpty {
                Text(event.notes)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }

            Divider()
            HStack {
                Text(event.attribution)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                Spacer()
                Link(destination: event.sourceURL) {
                    Image(systemName: "arrow.up.right")
                        .font(.caption)
                }
                .accessibilityLabel("Obre l'agenda oficial")
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 14))
    }
}

func googleMapsSearchURL(venue: String, municipality: String) -> URL? {
    var components = URLComponents()
    components.scheme = "https"
    components.host = "www.google.com"
    components.path = "/maps/search/"
    components.queryItems = [
        URLQueryItem(name: "api", value: "1"),
        URLQueryItem(name: "query", value: "\(venue), \(municipality)"),
    ]
    return components.url
}
