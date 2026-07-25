import SwiftUI

public struct AgendaRootView: View {
    private let model: AgendaViewModel
    @State private var scrollOffset: CGFloat = 0
    @State private var scrollViewBaseHeight: CGFloat = 0
    @State private var showsGroupFilter = false
    @State private var groupFilterDetent: PresentationDetent = .medium
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    public init(model: AgendaViewModel) {
        self.model = model
    }

    public var body: some View {
        NavigationStack {
            ScrollViewReader { proxy in
                let distance = foldDistance
                let foldProgress = AgendaCalendarFold.effectiveProgress(
                    AgendaCalendarFold.progress(scrollOffset: scrollOffset, foldDistance: distance),
                    reduceMotion: reduceMotion
                )

                VStack(spacing: 0) {
                    AgendaCalendarView(
                        selectedDate: model.selectedDate,
                        visibleMonth: model.visibleMonth,
                        visibleWeek: model.visibleWeek,
                        eventDateKeys: model.eventDateKeys,
                        foldProgress: foldProgress,
                        isGroupFilterActive: model.isGroupFilterActive,
                        selectedGroupCount: model.selectedGroupCount,
                        onToggle: { toggleFold(with: proxy) },
                        onOpenFilter: {
                            groupFilterDetent = .medium
                            showsGroupFilter = true
                        },
                        onSelect: { date in
                            Task { await model.selectAndLoad(date) }
                        },
                        onChangeWeek: { offset in
                            Task { await model.changeWeek(by: offset) }
                        },
                        onChangeMonth: { offset in
                            Task { await model.changeMonth(by: offset) }
                        }
                    )
                    .padding(.horizontal)
                    .padding(.top, 8)
                    .padding(.bottom, 12)

                    Divider()

                    AgendaFoldingEventList(
                        events: model.events,
                        otherEvents: model.otherEvents,
                        isLoading: model.isLoading,
                        errorMessage: model.errorMessage,
                        sourceStatus: model.sourceStatus,
                        officialURL: model.officialURL,
                        foldDistance: distance,
                        foldProgress: foldProgress,
                        scrollOffset: $scrollOffset,
                        scrollViewBaseHeight: $scrollViewBaseHeight,
                        refresh: { await model.refresh() }
                    )
                }
                .agendaNavigationBarHidden()
                .task { await model.load() }
                .task { await model.loadGroupDirectory() }
                .onChange(of: model.groupSelection) {
                    resetScrollAfterGroupSelectionChange(with: proxy)
                }
                .onChange(of: foldDistance) { oldDistance, newDistance in
                    scrollViewBaseHeight = AgendaCalendarFold.rebasedScrollViewBaseHeight(
                        scrollViewBaseHeight,
                        oldFoldDistance: oldDistance,
                        newFoldDistance: newDistance
                    )
                    keepFoldedThroughFoldDistanceChange(
                        from: oldDistance,
                        to: newDistance,
                        with: proxy
                    )
                }
            }
        }
        .sheet(isPresented: $showsGroupFilter) {
            AgendaGroupFilterView(
                model: model,
                onRequestExpansion: expandGroupFilter,
                onRequestCollapse: collapseGroupFilter
            )
                .presentationDetents(
                    [.medium, .large],
                    selection: $groupFilterDetent
                )
                .presentationContentInteraction(.resizes)
                .presentationDragIndicator(.visible)
        }
    }

    private var foldDistance: CGFloat {
        AgendaCalendarFold.foldDistance(
            weekRowCount: AgendaCalendarMath.monthWeekRowCount(containing: model.visibleMonth)
        )
    }

    private func expandGroupFilter() {
        guard groupFilterDetent != .large else { return }

        withAnimation(.snappy(duration: 0.25)) {
            groupFilterDetent = .large
        }
    }

    private func collapseGroupFilter() {
        guard groupFilterDetent != .medium else { return }

        withAnimation(.snappy(duration: 0.25)) {
            groupFilterDetent = .medium
        }
    }

    private func toggleFold(with proxy: ScrollViewProxy) {
        let isCollapsed = AgendaCalendarFold.snapsCollapsed(
            progress: AgendaCalendarFold.progress(
                scrollOffset: scrollOffset,
                foldDistance: foldDistance
            )
        )
        // Expanding from a deep scroll position returns to the top of the day.
        scroll(
            to: isCollapsed ? AgendaScrollIdentifiers.top : AgendaScrollIdentifiers.folded,
            with: proxy
        )
    }

    private func scroll(to anchorID: String, with proxy: ScrollViewProxy) {
        if reduceMotion {
            proxy.scrollTo(anchorID, anchor: .top)
        } else {
            withAnimation(.snappy(duration: 0.3)) {
                proxy.scrollTo(anchorID, anchor: .top)
            }
        }
    }

    private func resetScrollAfterGroupSelectionChange(with proxy: ScrollViewProxy) {
        var transaction = Transaction()
        transaction.disablesAnimations = true
        withTransaction(transaction) {
            scrollOffset = 0
            proxy.scrollTo(AgendaScrollIdentifiers.top, anchor: .top)
        }
    }

    /// Months have different fold distances (4, 5 or 6 weeks). When the visible
    /// month changes while the calendar rests folded, the scroll is re-anchored
    /// to the new fold end so the calendar stays folded without any visual jump.
    private func keepFoldedThroughFoldDistanceChange(
        from oldDistance: CGFloat,
        to newDistance: CGFloat,
        with proxy: ScrollViewProxy
    ) {
        guard
            newDistance > oldDistance,
            scrollOffset >= oldDistance,
            scrollOffset < newDistance
        else { return }

        var transaction = Transaction()
        transaction.disablesAnimations = true
        withTransaction(transaction) {
            proxy.scrollTo(AgendaScrollIdentifiers.folded, anchor: .top)
        }
    }
}
