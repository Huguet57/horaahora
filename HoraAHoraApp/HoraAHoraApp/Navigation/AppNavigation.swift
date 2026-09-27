import SafariServices
import SwiftUI

enum AppSection: Hashable {
    case calculator
    case scoreTable
    /// Hidden unless the secret gesture in Ajustos shows it, like `agenda`.
    case hourByHour
    case agenda
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
