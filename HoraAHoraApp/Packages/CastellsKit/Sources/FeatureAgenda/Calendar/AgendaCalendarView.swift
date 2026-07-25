import Foundation
import SwiftUI

struct AgendaCalendarView: View {
    let selectedDate: Date
    let visibleMonth: Date
    let visibleWeek: Date
    let eventDateKeys: Set<String>
    /// Normalized fold progress `0...1`: 0 shows the whole month, 1 keeps only
    /// the visible week in the compact position.
    let foldProgress: CGFloat
    let onToggle: () -> Void
    let onSelect: (Date) -> Void
    let onChangeWeek: (Int) -> Void
    let onChangeMonth: (Int) -> Void
    @Environment(\.accessibilityReduceMotion) var reduceMotion
    @State var weekDragOffset: CGFloat = 0
    @State var monthDragOffset: CGFloat = 0
    @State var monthPageWidth: CGFloat = 1

    let weekdays = ["DL", "DT", "DC", "DJ", "DV", "DS", "DG"]

    var isCollapsed: Bool {
        AgendaCalendarFold.snapsCollapsed(progress: foldProgress)
    }

    private var isFullyFolded: Bool {
        foldProgress >= 0.999
    }

    var body: some View {
        VStack(spacing: 14) {
            header

            if isFullyFolded {
                weekPager
            } else {
                monthPager
            }
        }
        .contentShape(Rectangle())
        .accessibilityAction(named: "Setmana anterior") { onChangeWeek(-1) }
        .accessibilityAction(named: "Setmana següent") { onChangeWeek(1) }
        .onChange(of: visibleWeek) { _, _ in
            var transaction = Transaction()
            transaction.disablesAnimations = true
            withTransaction(transaction) {
                weekDragOffset = 0
            }
        }
        .onChange(of: visibleMonth) { _, _ in
            var transaction = Transaction()
            transaction.disablesAnimations = true
            withTransaction(transaction) {
                monthDragOffset = 0
            }
        }
    }

    private var header: some View {
        HStack {
            Button(action: onToggle) {
                HStack(spacing: 7) {
                    Text(monthTitle)
                        .font(.title3.weight(.semibold))
                    Image(systemName: isCollapsed ? "chevron.down" : "chevron.up")
                        .font(.caption.weight(.bold))
                        .foregroundStyle(.secondary)
                }
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .accessibilityLabel(
                isCollapsed ? "Mostra el calendari mensual" : "Plega el calendari mensual"
            )
            .accessibilityValue(isCollapsed ? "Plegat" : "Desplegat")
            Spacer()
            Button { changeVisiblePeriod(by: -1) } label: {
                Image(systemName: "chevron.left")
                    .font(.title2.weight(.semibold))
                    .frame(width: 44, height: 44)
            }
            .accessibilityLabel(isCollapsed ? "Setmana anterior" : "Mes anterior")
            Button { changeVisiblePeriod(by: 1) } label: {
                Image(systemName: "chevron.right")
                    .font(.title2.weight(.semibold))
                    .frame(width: 44, height: 44)
            }
            .accessibilityLabel(isCollapsed ? "Setmana següent" : "Mes següent")
        }
        .contentShape(Rectangle())
        .highPriorityGesture(calendarVerticalDragGesture)
    }

    private func changeVisiblePeriod(by offset: Int) {
        if isCollapsed {
            onChangeWeek(offset)
        } else {
            onChangeMonth(offset)
        }
    }

    private var calendarVerticalDragGesture: some Gesture {
        DragGesture(minimumDistance: 24)
            .onEnded { value in
                handleVerticalDrag(value.translation)
            }
    }

    func handleVerticalDrag(_ translation: CGSize) {
        guard
            abs(translation.height) > abs(translation.width),
            abs(translation.height) >= 36
        else {
            return
        }

        if translation.height < 0, !isCollapsed {
            onToggle()
        } else if translation.height > 0, isCollapsed {
            onToggle()
        }
    }
}
