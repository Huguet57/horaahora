import SafariServices
import SwiftUI

enum AppSection: Hashable {
    case hourByHour
    case agenda
    case calculator
    case settings
}

struct PresentedLink: Identifiable {
    let id = UUID()
    let url: URL
}

struct InAppBrowser: UIViewControllerRepresentable {
    let url: URL

    func makeUIViewController(context: Context) -> SFSafariViewController {
        SFSafariViewController(url: url)
    }

    func updateUIViewController(_ viewController: SFSafariViewController, context: Context) {}
}
