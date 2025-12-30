import Foundation

@MainActor
final class BetBoardStore: ObservableObject {
    @Published var bundles: [League: ExportBundle] = [:]
    @Published var lastUpdated: Date?
    @Published var errorMessage: String?
    @Published var watchlistIds: [League: Set<String>] = [:]

    private let snapshotStore = SnapshotStore()
    private let watchlistStore = WatchlistStore()

    func loadAll() {
        Task {
            await refresh()
        }
    }

    func refresh() async {
        watchlistIds = League.allCases.reduce(into: [:]) { result, league in
            result[league] = watchlistStore.load(league: league)
        }
        guard let apiKey = try? KeychainHelper.read(), !apiKey.isEmpty else {
            errorMessage = "Add your Odds API key in Settings."
            bundles = [:]
            return
        }

        errorMessage = nil
        let client = OddsApiClient(apiKey: apiKey)
        let leagueKeys = await resolveLeagueKeys(using: client)
        var newBundles: [League: ExportBundle] = [:]

        for league in League.allCases {
            guard let leagueKey = leagueKeys[league] else { continue }
            do {
                let odds = try await client.fetchOdds(
                    leagueKey: leagueKey,
                    markets: ["h2h", "spreads", "totals"],
                    regions: "us"
                )
                let headlines = try await RssClient().fetchHeadlines(for: league)
                let snapshot = snapshotStore.load(league: league)
                let payload = buildBundle(
                    leagueKey: leagueKey,
                    events: odds,
                    headlines: headlines,
                    previousSnapshot: snapshot,
                    watchlistIds: watchlistIds[league] ?? []
                )
                snapshotStore.save(payload.snapshot, league: league)
                newBundles[league] = payload.bundle
            } catch {
                errorMessage = error.localizedDescription
            }
        }

        bundles = newBundles
        lastUpdated = Date()
    }

    func toggleWatchlist(eventId: String, league: League) {
        watchlistStore.toggle(eventId: eventId, league: league)
        watchlistIds[league] = watchlistStore.load(league: league)
    }

    var notableMoveCount: Int {
        bundles.values.reduce(0) { $0 + $1.movements.count }
    }

    private func resolveLeagueKeys(using client: OddsApiClient) async -> [League: String] {
        var mapping: [League: String] = [
            .nfl: "americanfootball_nfl",
            .cfb: "americanfootball_ncaaf",
        ]
        if let cached = UserDefaults.standard.string(forKey: Defaults.ufcKey), !cached.isEmpty {
            mapping[.ufc] = cached
            return mapping
        }
        do {
            let sports = try await client.listSports()
            if let key = discoverUfcKey(from: sports) {
                UserDefaults.standard.setValue(key, forKey: Defaults.ufcKey)
                mapping[.ufc] = key
            } else {
                mapping[.ufc] = "mma_mixed_martial_arts"
            }
        } catch {
            mapping[.ufc] = "mma_mixed_martial_arts"
        }
        return mapping
    }

    private func discoverUfcKey(from sports: [OddsApiSport]) -> String? {
        let candidates = sports.filter { sport in
            let key = sport.key.lowercased()
            let title = sport.title.lowercased()
            let group = sport.group.lowercased()
            return key.contains("ufc") || title.contains("ufc") || key.contains("mma") || group.contains("mma")
        }
        let sorted = candidates.sorted { lhs, rhs in
            if lhs.active != rhs.active { return lhs.active && !rhs.active }
            return lhs.key < rhs.key
        }
        return sorted.first?.key
    }
}

enum Defaults {
    static let refreshInterval = "refreshIntervalSeconds"
    static let defaultBooks = "defaultBooks"
    static let keyValidationStatus = "keyValidationStatus"
    static let keyValidationDate = "keyValidationDate"
    static let ufcKey = "ufcKey"
}
