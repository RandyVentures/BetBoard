import Foundation

struct OddsApiEvent: Decodable {
    let id: String
    let sportTitle: String
    let homeTeam: String
    let awayTeam: String
    let commenceTime: Date
    let bookmakers: [OddsApiBookmaker]
}

struct OddsApiBookmaker: Decodable {
    let key: String
    let markets: [OddsApiMarket]
}

struct OddsApiMarket: Decodable {
    let key: String
    let lastUpdate: Date
    let outcomes: [OddsApiOutcome]
}

struct OddsApiOutcome: Decodable {
    let name: String
    let price: Int
    let point: Double?
}

struct OddsApiSport: Decodable {
    let key: String
    let group: String
    let title: String
    let active: Bool
}
