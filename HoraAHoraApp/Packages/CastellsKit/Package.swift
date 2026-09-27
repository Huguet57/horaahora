// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "CastellsKit",
    defaultLocalization: "ca",
    platforms: [
        .iOS(.v17),
        .macOS(.v14),
    ],
    products: [
        .library(name: "CastellsDomain", targets: ["CastellsDomain"]),
        .library(name: "CastellsData", targets: ["CastellsData"]),
        .library(name: "CastellsInternalData", targets: ["CastellsInternalData"]),
        .library(name: "FeatureHourByHour", targets: ["FeatureHourByHour"]),
        .library(name: "FeatureAgenda", targets: ["FeatureAgenda"]),
        .library(name: "FeatureCalculator", targets: ["FeatureCalculator"]),
        .library(name: "FeatureScoreTable", targets: ["FeatureScoreTable"]),
        .library(name: "FeatureSettings", targets: ["FeatureSettings"]),
        .library(name: "FeatureInternalSettings", targets: ["FeatureInternalSettings"]),
    ],
    targets: [
        .target(name: "CastellsDomain"),
        .target(name: "CastellsData", dependencies: ["CastellsDomain"]),
        // Only the internal app links it: the data of Hora a Hora, Agenda, the group directory,
        // the news notifications and the hidden sections. The local database schema, tables of
        // these sections included, stays in CastellsData for both apps.
        .target(name: "CastellsInternalData", dependencies: ["CastellsData", "CastellsDomain"]),
        .target(name: "FeatureHourByHour", dependencies: ["CastellsDomain"]),
        .target(name: "FeatureAgenda", dependencies: ["CastellsDomain"]),
        .target(name: "FeatureCalculator", dependencies: ["CastellsDomain"]),
        .target(name: "FeatureScoreTable", resources: [.copy("Resources/score-table-2026.json")]),
        .target(name: "FeatureSettings", dependencies: ["CastellsDomain"]),
        // Only the internal app links it: it adds the news notifications, the sources of Hora a
        // Hora and Agenda and the secret gesture to Ajustos, which the public app shares.
        .target(name: "FeatureInternalSettings", dependencies: ["FeatureSettings", "CastellsDomain"]),
        .testTarget(name: "CastellsDomainTests", dependencies: ["CastellsDomain"]),
        .testTarget(name: "CastellsDataTests", dependencies: ["CastellsData", "CastellsDomain"]),
        .testTarget(
            name: "CastellsInternalDataTests",
            dependencies: ["CastellsInternalData", "CastellsData", "CastellsDomain"]
        ),
        .testTarget(name: "FeatureHourByHourTests", dependencies: ["FeatureHourByHour", "CastellsDomain"]),
        .testTarget(name: "FeatureAgendaTests", dependencies: ["FeatureAgenda", "CastellsDomain"]),
        .testTarget(name: "FeatureCalculatorTests", dependencies: ["FeatureCalculator", "CastellsDomain"]),
        .testTarget(name: "FeatureScoreTableTests", dependencies: ["FeatureScoreTable"]),
        .testTarget(name: "FeatureSettingsTests", dependencies: ["FeatureSettings", "CastellsDomain"]),
        .testTarget(
            name: "FeatureInternalSettingsTests",
            dependencies: ["FeatureInternalSettings", "FeatureSettings", "CastellsDomain"]
        ),
    ]
)
