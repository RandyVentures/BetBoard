import Foundation

final class WatchlistStore {
    private func key(for league: League) -> String {
        "watchlist_event_ids_\(league.rawValue)"
    }

    func load(league: League) -> Set<String> {
        let ids = UserDefaults.standard.stringArray(forKey: key(for: league)) ?? []
        return Set(ids)
    }

    func toggle(eventId: String, league: League) {
        var current = load(league: league)
        if current.contains(eventId) {
            current.remove(eventId)
        } else {
            current.insert(eventId)
        }
        UserDefaults.standard.set(Array(current), forKey: key(for: league))
    }
}
