import SwiftUI

struct StartupLoadingView: View {
    var body: some View {
        ZStack {
            Color(uiColor: .systemBackground)
                .ignoresSafeArea()

            VStack(spacing: 22) {
                Image("StartupBrandMark")
                    .resizable()
                    .scaledToFit()
                    .frame(width: 104, height: 104)
                    .clipShape(RoundedRectangle(cornerRadius: 23, style: .continuous))
                    .shadow(color: .black.opacity(0.08), radius: 12, y: 6)

                Text("La calculadora de l'Aleta")
                    .font(.title2.weight(.bold))
            }
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("La calculadora de l'Aleta")
    }
}
