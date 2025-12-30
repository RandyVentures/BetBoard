import Foundation

enum League: String, CaseIterable, Identifiable {
    case nfl
    case cfb
    case ufc

    var id: String { rawValue }

    var title: String {
        switch self {
        case .nfl:
            return "NFL"
        case .cfb:
            return "CFB"
        case .ufc:
            return "UFC"
        }
    }
}

struct ExportBundle: Decodable {
    let leagueKey: String
    let events: [Event]
    let odds: [OddsBoard]
    let movements: [MovementEvent]
    let headlines: [Headline]
    let watchlist: [WatchlistItem]
}

struct Event: Decodable, Identifiable {
    let eventId: String
    let leagueKey: String
    let sportTitle: String
    let homeTeam: String
    let awayTeam: String
    let startTime: Date

    var id: String { eventId }
}

struct OddsBoard: Decodable {
    let event: Event
    let bestLines: [BestLine]
    let lastUpdate: Date?
}

struct BestLine: Decodable {
    let market: String
    let outcome: String
    let price: Int
    let book: String
    let point: Double?
}

struct MovementEvent: Decodable, Identifiable {
    let leagueKey: String
    let eventId: String
    let createdAt: Date
    let details: [String: JSONValue]

    var id: String { "\(eventId)-\(createdAt.timeIntervalSince1970)" }
}

struct Headline: Decodable, Identifiable {
    let title: String
    let url: String
    let publishedAt: Date?
    let source: String

    var id: String { url }
}

struct WatchlistItem: Decodable, Identifiable {
    let eventId: String
    let leagueKey: String
    let addedAt: Date
    let notes: String?

    var id: String { eventId }
}
