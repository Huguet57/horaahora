import Foundation

enum CalculatorDestination: Hashable {
    case conversation(UUID)
    case newConversation
}
