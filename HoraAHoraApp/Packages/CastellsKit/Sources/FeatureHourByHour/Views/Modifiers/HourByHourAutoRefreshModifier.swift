import SwiftUI

public extension View {
    func hourByHourAutoRefresh(
        model: HourByHourViewModel,
        isEnabled: Bool,
        every interval: Duration = .seconds(60)
    ) -> some View {
        modifier(
            HourByHourAutoRefreshModifier(
                model: model,
                isEnabled: isEnabled,
                interval: interval
            )
        )
    }
}

private struct HourByHourAutoRefreshModifier: ViewModifier {
    let model: HourByHourViewModel
    let isEnabled: Bool
    let interval: Duration

    func body(content: Content) -> some View {
        content.task(id: isEnabled) {
            guard isEnabled else { return }
            await model.runAutoRefresh(every: interval)
        }
    }
}
