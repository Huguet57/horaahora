import Foundation

public extension JSONDecoder {
    static var castellsAPI: JSONDecoder {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .custom { codingPath in
            let source = codingPath.last?.stringValue ?? ""
            return CastellsCodingKey(stringValue: CastellsCodingKey.decodedName(source))!
        }
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let value = try container.decode(String.self)

            let fractional = ISO8601DateFormatter()
            fractional.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            if let date = fractional.date(from: value) { return date }

            let internet = ISO8601DateFormatter()
            internet.formatOptions = [.withInternetDateTime]
            if let date = internet.date(from: value) { return date }

            for format in ["yyyy-MM-dd'T'HH:mm:ss.SSSSSS", "yyyy-MM-dd'T'HH:mm:ss.SSS", "yyyy-MM-dd'T'HH:mm:ss"] {
                let formatter = DateFormatter()
                formatter.locale = Locale(identifier: "en_US_POSIX")
                formatter.calendar = Calendar(identifier: .iso8601)
                formatter.timeZone = TimeZone(secondsFromGMT: 0)
                formatter.dateFormat = format
                if let date = formatter.date(from: value) { return date }
            }

            throw DecodingError.dataCorruptedError(
                in: container,
                debugDescription: "Data ISO 8601 no vàlida: \(value)"
            )
        }
        return decoder
    }
}

public extension JSONEncoder {
    static var castellsAPI: JSONEncoder {
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        encoder.dateEncodingStrategy = .iso8601
        return encoder
    }
}

private struct CastellsCodingKey: CodingKey {
    let stringValue: String
    let intValue: Int?

    init?(stringValue: String) {
        self.stringValue = stringValue
        self.intValue = nil
    }

    init?(intValue: Int) {
        self.stringValue = String(intValue)
        self.intValue = intValue
    }

    static func decodedName(_ source: String) -> String {
        let parts = source.split(separator: "_")
        let camel = parts.dropFirst().reduce(String(parts.first ?? "")) { result, part in
            result + part.prefix(1).uppercased() + part.dropFirst()
        }
        return [
            "sourceId": "sourceID",
            "externalId": "externalID",
            "articleUrl": "articleURL",
            "actionUrl": "actionURL",
            "sourceUrl": "sourceURL",
            "officialUrl": "officialURL",
            "conversationId": "conversationID",
            "installationId": "installationID",
        ][camel] ?? camel
    }
}
