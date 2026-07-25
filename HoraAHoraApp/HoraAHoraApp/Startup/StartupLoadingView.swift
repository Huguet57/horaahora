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

                Text("Castells en vena")
                    .font(.title2.weight(.bold))

                ProgressView()
                    .tint(.red)
            }
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Carregant l'Hora a Hora")
    }
}
