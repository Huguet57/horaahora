import CastellsDomain

public protocol ChatRemoteService: Sendable {
    func send(request: ChatRequest) async throws -> ChatResponse
}

public struct HTTPChatRemoteService: ChatRemoteService {
    private let client: APIClient

    public init(client: APIClient) {
        self.client = client
    }

    public func send(request: ChatRequest) async throws -> ChatResponse {
        try await client.post(path: "/v1/chat", body: request)
    }
}
