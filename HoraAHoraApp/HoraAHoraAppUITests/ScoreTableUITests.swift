import UIKit
import XCTest

final class ScoreTableUITests: XCTestCase {
    @MainActor
    func testBarsRemainVisibleWhenReturningToTheTabWithoutScrolling() throws {
        continueAfterFailure = false
        XCUIDevice.shared.orientation = .portrait
        let app = XCUIApplication()
        app.launchArguments = ["-AppleLanguages", "(ca)", "-AppleLocale", "ca_ES"]
        app.launch()

        let scoresTab = app.tabBars.buttons["Puntuacions"]
        XCTAssertTrue(scoresTab.waitForExistence(timeout: 10))
        scoresTab.tap()

        let firstRow = app.descendants(matching: .any)
            .matching(NSPredicate(format: "label == %@", "Tres de deu sense manilles, 3de10sm"))
            .firstMatch
        XCTAssertTrue(firstRow.waitForExistence(timeout: 5))
        try assertBarIsDrawn(in: firstRow, context: "First entry")

        // Reuse the same rows at the same scroll position on every return.
        for otherTab in ["Ajustos", "Calculadora", "Ajustos"] {
            app.tabBars.buttons[otherTab].tap()
            scoresTab.tap()
            XCTAssertTrue(firstRow.waitForExistence(timeout: 5))
            try assertBarIsDrawn(in: firstRow, context: "Returning from \(otherTab)")
        }
    }

    @MainActor
    private func assertBarIsDrawn(in row: XCUIElement, context: String) throws {
        let screenshot = row.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = context
        add(attachment)

        // The bars are deliberately hidden from VoiceOver, and the row's text remains visible
        // during this bug. Inspect the unselected row's red pixels to verify the actual drawing.
        let image = try XCTUnwrap(screenshot.image.cgImage)
        var pixels = [UInt8](repeating: 0, count: image.width * image.height * 4)
        let count = try pixels.withUnsafeMutableBytes { buffer in
            let bitmap = try XCTUnwrap(CGContext(
                data: buffer.baseAddress,
                width: image.width,
                height: image.height,
                bitsPerComponent: 8,
                bytesPerRow: image.width * 4,
                space: CGColorSpaceCreateDeviceRGB(),
                bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
                    | CGBitmapInfo.byteOrder32Big.rawValue
            ))
            bitmap.draw(image, in: CGRect(x: 0, y: 0, width: image.width, height: image.height))
            return stride(from: 0, to: buffer.count, by: 4).filter { offset in
                let red = Int(buffer[offset])
                let green = Int(buffer[offset + 1])
                let blue = Int(buffer[offset + 2])
                return red > 120 && red > green * 2 && red > blue * 2
            }.count
        }
        XCTAssertGreaterThan(count, 100, "\(context): the score bar must be drawn before any scroll")
    }
}
