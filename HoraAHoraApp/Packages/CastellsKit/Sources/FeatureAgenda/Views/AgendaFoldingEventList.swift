import SwiftUI
import CastellsDomain

/// The day's event list. Its first `foldDistance` points of scroll travel
/// drive the calendar fold instead of moving the cards.
struct AgendaFoldingEventList: View {
    let events: [CastellEvent]
    let otherEvents: [CastellEvent]
    let isLoading: Bool
    let errorMessage: String?
    let sourceStatus: AgendaSourceStatus
    let officialURL: URL
    let foldDistance: CGFloat
    let foldProgress: CGFloat
    @Binding var scrollOffset: CGFloat
    @Binding var scrollViewBaseHeight: CGFloat
    let refresh: () async -> Void
    let openFilter: () -> Void

    var body: some View {
        ScrollView {
            ZStack(alignment: .top) {
                scrollAnchors

                VStack(spacing: 0) {
                    // Fold travel already consumed by the scroll. It keeps
                    // the cards glued to the calendar bottom instead of
                    // scrolling at double speed while the calendar folds.
                    Color.clear
                        .frame(height: contentCompensation)

                    ZStack(alignment: .top) {
                        // Fixed-height floor guaranteeing the full fold travel
                        // on days with little or no content.
                        Color.clear
                            .frame(height: minimumContentHeight)

                        AgendaEventListContent(
                            events: events,
                            otherEvents: otherEvents,
                            isLoading: isLoading,
                            errorMessage: errorMessage,
                            sourceStatus: sourceStatus,
                            officialURL: officialURL,
                            refresh: { Task { await refresh() } },
                            openFilter: openFilter
                        )
                        .equatable()
                        .padding(.vertical, 16)
                    }
                }
            }
            .onGeometryChange(for: CGFloat.self) { geometry in
                AgendaCalendarFold.trackedScrollOffset(
                    -geometry.frame(in: .named(AgendaScrollIdentifiers.spaceName)).minY
                )
            } action: { offset in
                var transaction = Transaction()
                transaction.disablesAnimations = true
                withTransaction(transaction) {
                    scrollOffset = offset
                }
            }
        }
        .coordinateSpace(.named(AgendaScrollIdentifiers.spaceName))
        .contentMargins(.horizontal, 16, for: .scrollContent)
        .scrollTargetBehavior(AgendaFoldSnapBehavior(foldDistance: foldDistance))
        .onGeometryChange(for: CGFloat.self) { geometry in
            geometry.size.height
        } action: { height in
            syncBaseHeight(measuredHeight: height)
        }
        .refreshable { await refresh() }
    }

    private var contentCompensation: CGFloat {
        AgendaCalendarFold.contentCompensation(
            progress: foldProgress,
            foldDistance: foldDistance
        )
    }

    private var minimumContentHeight: CGFloat {
        AgendaCalendarFold.minimumListContentHeight(
            scrollViewHeight: scrollViewBaseHeight,
            foldDistance: foldDistance
        )
    }

    private var scrollAnchors: some View {
        VStack(spacing: 0) {
            Color.clear
                .frame(width: 1, height: 1)
                .id(AgendaScrollIdentifiers.top)
            Color.clear
                .frame(width: 1, height: max(foldDistance - 1, 0))
            Color.clear
                .frame(width: 1, height: 1)
                .id(AgendaScrollIdentifiers.folded)
        }
        .allowsHitTesting(false)
        .accessibilityHidden(true)
    }

    /// The base stays frozen during the fold so a short list always has the
    /// exact scroll range needed to reach a stable collapsed position.
    private func syncBaseHeight(measuredHeight: CGFloat) {
        let progress = AgendaCalendarFold.progress(
            scrollOffset: scrollOffset,
            foldDistance: foldDistance
        )
        guard AgendaCalendarFold.shouldSyncScrollViewBaseHeight(progress: progress) else { return }
        scrollViewBaseHeight = measuredHeight
    }
}
