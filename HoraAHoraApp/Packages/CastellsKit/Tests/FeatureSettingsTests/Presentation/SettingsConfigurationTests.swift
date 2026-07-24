import XCTest
@testable import FeatureSettings

final class SettingsConfigurationTests: XCTestCase {
    func testPrivacyURLIsBuiltBelowTheInjectedAPIBaseURL() throws {
        let configuration = makeConfiguration(
            apiBaseURL: try XCTUnwrap(URL(string: "https://example.test/service/"))
        )

        XCTAssertEqual(
            configuration.privacyURL.absoluteString,
            "https://example.test/service/privacy"
        )
    }

    func testSupportEmailURLIncludesEditableEncodedMetadata() throws {
        let configuration = makeConfiguration(
            supportEmail: "suport+castells@example.test",
            appVersion: "2.4",
            buildNumber: "91",
            technicalIdentifier: "ABC 123/ç"
        )

        let url = configuration.supportEmailURL
        let components = try XCTUnwrap(URLComponents(url: url, resolvingAgainstBaseURL: false))

        XCTAssertEqual(components.scheme, "mailto")
        XCTAssertEqual(components.path, "suport+castells@example.test")
        XCTAssertEqual(
            components.queryItems?.first(where: { $0.name == "subject" })?.value,
            "Suport Castells en vena"
        )
        let body = try XCTUnwrap(
            components.queryItems?.first(where: { $0.name == "body" })?.value
        )
        XCTAssertTrue(body.contains("Versió: 2.4 (91)"))
        XCTAssertTrue(body.contains("Identificador tècnic: ABC 123/ç"))
        XCTAssertTrue(url.absoluteString.contains("%0A"))
        XCTAssertTrue(url.absoluteString.contains("%C3%A7"))
    }

    private func makeConfiguration(
        apiBaseURL: URL = URL(string: "https://example.test")!,
        supportEmail: String = "support@example.test",
        appVersion: String = "1.0",
        buildNumber: String = "1",
        technicalIdentifier: String = "test-id"
    ) -> SettingsConfiguration {
        SettingsConfiguration(
            apiBaseURL: apiBaseURL,
            supportEmail: supportEmail,
            appName: "Castells en vena",
            appVersion: appVersion,
            buildNumber: buildNumber,
            technicalIdentifier: technicalIdentifier,
            revistaCastellsURL: URL(string: "https://revistacastells.cat/castells-hora-a-hora/"),
            ccccAgendaURL: URL(string: "https://castellscat.cat/public/ca/agenda"),
            concursCastellsURL: nil
        )
    }
}
