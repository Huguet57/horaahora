import CastellsDomain

struct AgendaEventWindowProjection {
    let events: [CastellEvent]
    let otherEvents: [CastellEvent]
    let eventDateKeys: Set<String>
    let monthEvents: [CastellEvent]
}
