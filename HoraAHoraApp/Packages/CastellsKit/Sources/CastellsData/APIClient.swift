import Foundation
import CastellsDomain

public enum APIClientError: LocalizedError {
    case invalidResponse
    case http(statusCode: Int, message: String?)

    public var errorDescription: String? {
        switch self {
        case .invalidResponse:
            return "La resposta del servidor no és vàlida."
        case let .http(statusCode, message):
            return message ?? "El servidor ha retornat l'error \(statusCode)."
        }
    }
}

public actor APIClient {
    private let baseURL: URL
    private let session: URLSession

    public init(baseURL: URL, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
    }

    public func get<Response: Decodable & Sendable>(
        path: String,
        queryItems: [URLQueryItem] = []
    ) async throws -> Response {
        var components = URLComponents(url: baseURL.appending(path: path), resolvingAgainstBaseURL: false)
        components?.queryItems = queryItems.isEmpty ? nil : queryItems
        guard let url = components?.url else { throw URLError(.badURL) }
        return try await execute(URLRequest(url: url))
    }

    public func post<Body: Encodable & Sendable, Response: Decodable & Sendable>(
        path: String,
        body: Body
    ) async throws -> Response {
        var request = URLRequest(url: baseURL.appending(path: path))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder.castellsAPI.encode(body)
        return try await execute(request)
    }

    private func execute<Response: Decodable & Sendable>(_ request: URLRequest) async throws -> Response {
        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIClientError.invalidResponse
        }
        guard 200..<300 ~= httpResponse.statusCode else {
            let detail = try? JSONDecoder().decode(ErrorEnvelope.self, from: data).detail
            throw APIClientError.http(statusCode: httpResponse.statusCode, message: detail)
        }
        return try JSONDecoder.castellsAPI.decode(Response.self, from: data)
    }
}

private struct ErrorEnvelope: Decodable {
    let detail: String
}

public enum InstallationIdentifier {
    private static let key = "castells.installation-id"

    public static var current: String {
        if let existing = UserDefaults.standard.string(forKey: key) { return existing }
        let value = UUID().uuidString
        UserDefaults.standard.set(value, forKey: key)
        return value
    }
}
