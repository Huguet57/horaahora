import SwiftUI
import CastellsDomain

public struct HourByHourRootView: View {
    private let model: HourByHourViewModel
    @State private var detailItem: HourByHourItem?
    private let showsNotificationOnboarding: Bool
    private let onConfigureNotifications: () -> Void
    private let onDismissNotificationOnboarding: () -> Void
    private let onOpen: ((URL) -> Void)?

    public init(
        model: HourByHourViewModel,
        showsNotificationOnboarding: Bool = false,
        onConfigureNotifications: @escaping () -> Void = {},
        onDismissNotificationOnboarding: @escaping () -> Void = {},
        onOpen: ((URL) -> Void)? = nil
    ) {
        self.model = model
        self.showsNotificationOnboarding = showsNotificationOnboarding
        self.onConfigureNotifications = onConfigureNotifications
        self.onDismissNotificationOnboarding = onDismissNotificationOnboarding
        self.onOpen = onOpen
    }

    public var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                if model.items.isEmpty {
                    Group {
                        if model.isLoading {
                            HourByHourSkeletonView()
                        } else if let error = model.errorMessage {
                            ContentUnavailableView {
                                Label("No s'ha pogut carregar", systemImage: "wifi.exclamationmark")
                            } description: {
                                Text(error)
                            } actions: {
                                Button("Torna-ho a provar") { Task { await model.refresh() } }
                            }
                        } else {
                            ContentUnavailableView("Encara no hi ha entrades", systemImage: "clock")
                        }
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List {
                        if showsNotificationOnboarding {
                            HourByHourNotificationOnboardingCard(
                                onConfigure: onConfigureNotifications,
                                onDismiss: onDismissNotificationOnboarding
                            )
                            .listRowInsets(
                                EdgeInsets(top: 8, leading: 16, bottom: 8, trailing: 16)
                            )
                            .listRowBackground(Color.clear)
                            .listRowSeparator(.hidden)
                        }

                        ForEach(model.dayGroups) { group in
                            Section(
                                group.day?.formatted(date: .complete, time: .omitted)
                                    ?? "Sense data"
                            ) {
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
            .task { await model.loadIfNeeded() }
            .navigationTitle("Hora a Hora")
            .hourByHourLargeNavigationTitle()
            .sheet(item: $detailItem) { item in
                HourByHourDetailView(item: item)
                    .presentationDetents([.medium, .large])
                    .presentationDragIndicator(.visible)
                    .hourByHourOpaquePresentation()
            }
        }
    }
}
