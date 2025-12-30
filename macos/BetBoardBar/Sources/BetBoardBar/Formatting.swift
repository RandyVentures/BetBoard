import Foundation

enum Formatter {
    static let eventTime: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "MMM d h:mm a"
        return formatter
    }()

    static let timeOnly: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "h:mm a"
        return formatter
    }()
}

func eventLine(_ event: Event) -> String {
    let time = Formatter.timeOnly.string(from: event.startTime)
    return "\(event.awayTeam) @ \(event.homeTeam) — \(time)"
}

func movementLine(_ movement: MovementEvent) -> String {
    let details = movement.details
    let market = details["market"]?.stringValue ?? ""
    let outcome = details["outcome"]?.stringValue ?? ""
    let book = details["book"]?.stringValue ?? ""

    let previous = details["previous"]?.objectValue
    let current = details["current"]?.objectValue

    let prevPrice = previous?["price"]?.numberValue
    let currPrice = current?["price"]?.numberValue
    let prevPoint = previous?["point"]?.numberValue
    let currPoint = current?["point"]?.numberValue

    if market == "spreads" || market == "totals" {
        let prevText = prevPoint.map { String(format: "%+.1f", $0) } ?? "?"
        let currText = currPoint.map { String(format: "%+.1f", $0) } ?? "?"
        return "\(market.uppercased()) \(prevText) → \(currText) (\(book))"
    }

    if let prevPrice, let currPrice {
        return "\(market.uppercased()) \(outcome) \(Int(prevPrice)) → \(Int(currPrice)) (\(book))"
    }

    return "\(market.uppercased()) \(outcome) (\(book))"
}

func lastUpdatedLine(_ date: Date?) -> String {
    guard let date else { return "Not updated" }
    return "Updated \(Formatter.eventTime.string(from: date))"
}

func oddsSummaryLine(_ board: OddsBoard) -> String {
    let event = board.event
    let ml = moneylineText(board: board)
    let spread = spreadText(board: board)
    let total = totalText(board: board)
    let parts = [ml, spread, total].filter { !$0.isEmpty }
    return "\(event.awayTeam) @ \(event.homeTeam) — \(parts.joined(separator: " | "))"
}

private func moneylineText(board: OddsBoard) -> String {
    let lines = board.bestLines.filter { $0.market == "h2h" }
    guard !lines.isEmpty else { return "" }
    let away = lines.first(where: { $0.outcome == board.event.awayTeam }) ?? lines.first
    let home = lines.first(where: { $0.outcome == board.event.homeTeam }) ?? lines.dropFirst().first
    let awayPrice = away.map { formatPrice($0.price) } ?? "?"
    let homePrice = home.map { formatPrice($0.price) } ?? "?"
    return "ML \(awayPrice)/\(homePrice)"
}

private func spreadText(board: OddsBoard) -> String {
    let lines = board.bestLines.filter { $0.market == "spreads" }
    guard let line = lines.first else { return "" }
    let point = line.point.map { String(format: "%+.1f", $0) } ?? "?"
    return "Spr \(point)"
}

private func totalText(board: OddsBoard) -> String {
    let lines = board.bestLines.filter { $0.market == "totals" }
    guard let line = lines.first(where: { $0.outcome.lowercased() == "over" }) ?? lines.first else {
        return ""
    }
    let point = line.point.map { String(format: "%.1f", $0) } ?? "?"
    return "Tot \(point)"
}

private func formatPrice(_ price: Int) -> String {
    if price > 0 {
        return "+\(price)"
    }
    return "\(price)"
}
