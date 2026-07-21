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
        .library(name: "FeatureHourByHour", targets: ["FeatureHourByHour"]),
        .library(name: "FeatureAgenda", targets: ["FeatureAgenda"]),
        .library(name: "FeatureCalculator", targets: ["FeatureCalculator"]),
    ],
    targets: [
        .target(name: "CastellsDomain"),
        .target(name: "CastellsData", dependencies: ["CastellsDomain"]),
        .target(name: "FeatureHourByHour", dependencies: ["CastellsDomain"]),
        .target(name: "FeatureAgenda", dependencies: ["CastellsDomain"]),
        .target(name: "FeatureCalculator", dependencies: ["CastellsDomain"]),
        .testTarget(name: "CastellsDomainTests", dependencies: ["CastellsDomain"]),
        .testTarget(name: "CastellsDataTests", dependencies: ["CastellsData", "CastellsDomain"]),
        .testTarget(name: "FeatureAgendaTests", dependencies: ["FeatureAgenda", "CastellsDomain"]),
    ]
)
