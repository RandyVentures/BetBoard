import Foundation

struct BundlePayload {
    let bundle: ExportBundle
    let snapshot: SnapshotBundle
}

func buildBundle(
    leagueKey: String,
    events: [OddsApiEvent],
    headlines: [Headline],
    previousSnapshot: SnapshotBundle?,
    watchlistIds: Set<String>
) -> BundlePayload {
    let mappedEvents = events.map { apiEvent in
        Event(
            eventId: apiEvent.id,
            leagueKey: leagueKey,
            sportTitle: "",
            homeTeam: apiEvent.homeTeam,
            awayTeam: apiEvent.awayTeam,
            startTime: apiEvent.commenceTime
        )
    }

    let oddsBoards = events.map { buildOddsBoard(from: $0, leagueKey: leagueKey) }
    let snapshot = SnapshotBundle(
        leagueKey: leagueKey,
        createdAt: Date(),
        events: events.map { apiEvent in
            SnapshotEvent(
                eventId: apiEvent.id,
                lines: snapshotLines(from: apiEvent)
            )
        }
    )

    let movements = detectMovements(previous: previousSnapshot, current: snapshot, leagueKey: leagueKey)

    return BundlePayload(
        bundle: ExportBundle(
            leagueKey: leagueKey,
            events: mappedEvents,
            odds: oddsBoards,
            movements: movements,
            headlines: headlines,
            watchlist: mappedEvents
                .filter { watchlistIds.contains($0.eventId) }
                .map {
                    WatchlistItem(
                        eventId: $0.eventId,
                        leagueKey: $0.leagueKey,
                        addedAt: Date(),
                        notes: nil
                    )
                }
        ),
        snapshot: snapshot
    )
}

func buildOddsBoard(from event: OddsApiEvent, leagueKey: String) -> OddsBoard {
    let mappedEvent = Event(
        eventId: event.id,
        leagueKey: leagueKey,
        sportTitle: "",
        homeTeam: event.homeTeam,
        awayTeam: event.awayTeam,
        startTime: event.commenceTime
    )

    var bestLines: [BestLine] = []
    var lastUpdate: Date? = nil

    for bookmaker in event.bookmakers {
        for market in bookmaker.markets {
            lastUpdate = max(lastUpdate ?? market.lastUpdate, market.lastUpdate)
            for outcome in market.outcomes {
                let candidate = BestLine(
                    market: market.key,
                    outcome: outcome.name,
                    price: outcome.price,
                    book: bookmaker.key,
                    point: outcome.point
                )
                if let index = bestLines.firstIndex(where: { $0.market == candidate.market && $0.outcome == candidate.outcome }) {
                    if candidate.price > bestLines[index].price {
                        bestLines[index] = candidate
                    }
                } else {
                    bestLines.append(candidate)
                }
            }
        }
    }

    return OddsBoard(event: mappedEvent, bestLines: bestLines, lastUpdate: lastUpdate)
}

func snapshotLines(from event: OddsApiEvent) -> [SnapshotLine] {
    var lines: [SnapshotLine] = []
    for bookmaker in event.bookmakers {
        for market in bookmaker.markets {
            for outcome in market.outcomes {
                lines.append(
                    SnapshotLine(
                        market: market.key,
                        book: bookmaker.key,
                        outcome: outcome.name,
                        price: Double(outcome.price),
                        point: outcome.point
                    )
                )
            }
        }
    }
    return lines
}

func detectMovements(previous: SnapshotBundle?, current: SnapshotBundle, leagueKey: String) -> [MovementEvent] {
    guard let previous else { return [] }
    var prevIndex: [String: SnapshotLine] = [:]
    for event in previous.events {
        for line in event.lines {
            prevIndex["\(event.eventId)|\(line.market)|\(line.book)|\(line.outcome)"] = line
        }
    }

    var movements: [MovementEvent] = []
    for event in current.events {
        for line in event.lines {
            let key = "\(event.eventId)|\(line.market)|\(line.book)|\(line.outcome)"
            guard let prev = prevIndex[key] else { continue }
            if isNotableMove(market: line.market, prev: prev, curr: line) {
                let details: [String: JSONValue] = [
                    "market": .string(line.market),
                    "book": .string(line.book),
                    "outcome": .string(line.outcome),
                    "previous": .object([
                        "price": .number(prev.price),
                        "point": prev.point.map { .number($0) } ?? .null,
                    ]),
                    "current": .object([
                        "price": .number(line.price),
                        "point": line.point.map { .number($0) } ?? .null,
                    ]),
                    "delta": .number(line.price - prev.price),
                ]
                movements.append(
                    MovementEvent(
                        leagueKey: leagueKey,
                        eventId: event.eventId,
                        createdAt: Date(),
                        details: details
                    )
                )
            }
        }
    }
    return movements
}

func isNotableMove(market: String, prev: SnapshotLine, curr: SnapshotLine) -> Bool {
    if market == "h2h" {
        if abs(curr.price - prev.price) >= 15 { return true }
        if (prev.price < 0 && curr.price > 0) || (prev.price > 0 && curr.price < 0) { return true }
    }
    if market == "spreads" || market == "totals" {
        guard let prevPoint = prev.point, let currPoint = curr.point else { return false }
        return abs(currPoint - prevPoint) >= 1.0
    }
    return false
}
