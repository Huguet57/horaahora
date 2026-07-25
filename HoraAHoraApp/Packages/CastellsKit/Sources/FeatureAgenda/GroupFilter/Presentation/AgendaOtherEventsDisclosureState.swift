struct AgendaOtherEventsDisclosureState: Equatable {
    private(set) var isExpanded: Bool

    init(hasMatchingEvents: Bool) {
        isExpanded = !hasMatchingEvents
    }

    mutating func toggle() {
        isExpanded.toggle()
    }
}
