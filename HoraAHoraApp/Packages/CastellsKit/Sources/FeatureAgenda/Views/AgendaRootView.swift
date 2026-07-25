import SwiftUI
import CastellsDomain

private let agendaScrollSpaceName = "agendaListScrollSpace"
private let agendaListTopAnchorID = "agendaListTopAnchor"
private let agendaListFoldedAnchorID = "agendaListFoldedAnchor"

public struct AgendaRootView: View {
    private let model: AgendaViewModel
    @State private var scrollOffset: CGFloat = 0
    @State private var scrollViewBaseHeight: CGFloat = 0
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
                        onToggle: { toggleFold(with: proxy) },
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

                    foldingEventList(foldDistance: distance, foldProgress: foldProgress)
                }
                .agendaNavigationBarHidden()
                .task { await model.load() }
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
    }

    private var foldDistance: CGFloat {
        AgendaCalendarFold.foldDistance(
            weekRowCount: AgendaCalendarMath.monthWeekRows(containing: model.visibleMonth).count
        )
    }

    /// The day's event list. Its first `foldDistance` points of scroll travel
    /// drive the calendar fold instead of moving the cards.
    private func foldingEventList(foldDistance: CGFloat, foldProgress: CGFloat) -> some View {
        let compensation = AgendaCalendarFold.contentCompensation(
            progress: foldProgress,
            foldDistance: foldDistance
        )

        return ScrollView {
            ZStack(alignment: .top) {
                scrollAnchors(foldDistance: foldDistance)

                VStack(spacing: 0) {
                    // Fold travel already consumed by the scroll. It keeps
                    // the cards glued to the calendar bottom instead of
                    // scrolling at double speed while the calendar folds.
                    Color.clear
                        .frame(height: compensation)

                    ZStack(alignment: .top) {
                        // Fixed-height floor guaranteeing the full fold travel
                        // on days with little or no content, independent of the
                        // unbounded height proposal inside the scroll view.
                        Color.clear
                            .frame(
                                height: AgendaCalendarFold.minimumListContentHeight(
                                    scrollViewHeight: scrollViewBaseHeight,
                                    foldDistance: foldDistance
                                )
                            )

                        AgendaEventListContent(model: model)
                            .padding(.vertical, 16)
                    }
                }
            }
            .onGeometryChange(for: CGFloat.self) { geometry in
                -geometry.frame(in: .named(agendaScrollSpaceName)).minY
            } action: { offset in
                // The fold must track the raw offset 1:1; an inherited animated
                // transaction here would pile up overlapping springs.
                var transaction = Transaction()
                transaction.disablesAnimations = true
                withTransaction(transaction) {
                    scrollOffset = offset
                }
            }
        }
        .coordinateSpace(.named(agendaScrollSpaceName))
        .contentMargins(.horizontal, 16, for: .scrollContent)
        .scrollTargetBehavior(AgendaFoldSnapBehavior(foldDistance: foldDistance))
        .onGeometryChange(for: CGFloat.self) { geometry in
            // Full frame height: the scrollable range of this scroll view is
            // `content − frame` (the bottom safe area does not extend it), so
            // the fold travel must fit within the full frame plus the floor.
            geometry.size.height
        } action: { height in
            syncScrollViewBaseHeight(measuredHeight: height, foldDistance: foldDistance)
        }
        .refreshable { await model.refresh() }
    }

    /// Invisible column marking the two snap offsets of the fold: the list top
    /// (expanded) and the end of the fold travel (collapsed). The chevron and
    /// the vertical gesture scroll to these same anchors.
    private func scrollAnchors(foldDistance: CGFloat) -> some View {
        VStack(spacing: 0) {
            Color.clear
                .frame(width: 1, height: 1)
                .id(agendaListTopAnchorID)
            Color.clear
                .frame(width: 1, height: max(foldDistance - 1, 0))
            Color.clear
                .frame(width: 1, height: 1)
                .id(agendaListFoldedAnchorID)
        }
        .allowsHitTesting(false)
        .accessibilityHidden(true)
    }

    /// Syncs the fold-independent base height only while the calendar rests
    /// expanded, where the measurement cannot disagree with the fold state.
    /// The base stays frozen during the whole fold, so the short-list scroll
    /// range is exactly the fold travel at every frame and the bottom rubber
    /// band can never clamp the scroll into a half-folded resting position.
    private func syncScrollViewBaseHeight(measuredHeight: CGFloat, foldDistance: CGFloat) {
        let progress = AgendaCalendarFold.progress(
            scrollOffset: scrollOffset,
            foldDistance: foldDistance
        )
        guard AgendaCalendarFold.shouldSyncScrollViewBaseHeight(progress: progress) else { return }
        scrollViewBaseHeight = measuredHeight
    }

    private func toggleFold(with proxy: ScrollViewProxy) {
        let isCollapsed = AgendaCalendarFold.snapsCollapsed(
            progress: AgendaCalendarFold.progress(
                scrollOffset: scrollOffset,
                foldDistance: foldDistance
            )
        )
        // Expanding from a deep scroll position returns to the top of the day.
        scroll(to: isCollapsed ? agendaListTopAnchorID : agendaListFoldedAnchorID, with: proxy)
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
            proxy.scrollTo(agendaListFoldedAnchorID, anchor: .top)
        }
    }
}

/// Snaps the scroll resting position out of the fold zone: releasing at half
/// the fold travel or more settles collapsed, below it settles expanded.
private struct AgendaFoldSnapBehavior: ScrollTargetBehavior {
    let foldDistance: CGFloat

    func updateTarget(_ target: inout ScrollTarget, context: TargetContext) {
        target.rect.origin.y = AgendaCalendarFold.snapTargetOffset(
            proposedOffset: target.rect.origin.y,
            foldDistance: foldDistance
        )
    }
}

private extension View {
    @ViewBuilder
    func agendaNavigationBarHidden() -> some View {
        #if os(iOS)
        toolbar(.hidden, for: .navigationBar)
        #else
        self
        #endif
    }
}
