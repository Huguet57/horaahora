@MainActor
public protocol HourByHourRepository: AnyObject {
    func page(cursor: String?, limit: Int, forceRefresh: Bool) async throws -> HourByHourPage
}
