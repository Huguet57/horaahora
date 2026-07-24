import Foundation
import SwiftUI
import CastellsDomain

struct AgendaEventCard: View {
    let event: CastellEvent

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .firstTextBaseline) {
                Label(event.timeLabel, systemImage: "clock")
                    .font(.subheadline.weight(.semibold))
                Spacer()
                Text(event.municipality)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }

            Text(event.title)
                .font(.headline)

            if !event.venue.isEmpty,
               let mapsURL = googleMapsSearchURL(
                   venue: event.venue,
                   municipality: event.municipality
               ) {
                Link(destination: mapsURL) {
                    Label(event.venue, systemImage: "mappin.and.ellipse")
                        .font(.subheadline)
                }
                .accessibilityLabel("Obre \(event.venue) a Google Maps")
            }

            if !event.participatingGroups.isEmpty {
                VStack(alignment: .leading, spacing: 3) {
                    ForEach(event.participatingGroups, id: \.self) { group in
                        Text("• \(group)")
                    }
                }
                .font(.subheadline)
            }

            if !event.notes.isEmpty {
                Text(event.notes)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }

            Divider()
            HStack {
                Text(event.attribution)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                Spacer()
                Link(destination: event.sourceURL) {
                    Image(systemName: "arrow.up.right")
                        .font(.caption)
                }
                .accessibilityLabel("Obre l'agenda oficial")
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 14))
    }
}

func googleMapsSearchURL(venue: String, municipality: String) -> URL? {
    var components = URLComponents()
    components.scheme = "https"
    components.host = "www.google.com"
    components.path = "/maps/search/"
    components.queryItems = [
        URLQueryItem(name: "api", value: "1"),
        URLQueryItem(name: "query", value: "\(venue), \(municipality)"),
    ]
    return components.url
}
