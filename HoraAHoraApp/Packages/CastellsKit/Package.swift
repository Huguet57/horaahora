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
        .library(name: "FeatureCalculator", targets: ["FeatureCalculator"]),
        .library(name: "FeatureScoreTable", targets: ["FeatureScoreTable"]),
        .library(name: "FeatureSettings", targets: ["FeatureSettings"]),
    ],
    targets: [
        .target(name: "CastellsDomain"),
        .target(name: "CastellsData", dependencies: ["CastellsDomain"]),
        .target(name: "FeatureCalculator", dependencies: ["CastellsDomain"]),
        .target(name: "FeatureScoreTable", resources: [.copy("Resources/score-table-2026.json")]),
        .target(name: "FeatureSettings", dependencies: ["CastellsDomain"]),
        .testTarget(name: "CastellsDomainTests", dependencies: ["CastellsDomain"]),
        .testTarget(name: "CastellsDataTests", dependencies: ["CastellsData", "CastellsDomain"]),
        .testTarget(name: "FeatureCalculatorTests", dependencies: ["FeatureCalculator", "CastellsDomain"]),
        .testTarget(name: "FeatureScoreTableTests", dependencies: ["FeatureScoreTable"]),
        .testTarget(name: "FeatureSettingsTests", dependencies: ["FeatureSettings", "CastellsDomain"]),
    ]
)
