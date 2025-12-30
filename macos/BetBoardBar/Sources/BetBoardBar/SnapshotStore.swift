import Foundation

struct SnapshotLine: Codable {
    let market: String
    let book: String
    let outcome: String
    let price: Double
    let point: Double?
}

struct SnapshotEvent: Codable {
    let eventId: String
    let lines: [SnapshotLine]
}

struct SnapshotBundle: Codable {
    let leagueKey: String
    let createdAt: Date
    let events: [SnapshotEvent]
}

struct SnapshotStore {
    func load(league: League) -> SnapshotBundle? {
        let url = snapshotURL(for: league)
        guard FileManager.default.fileExists(atPath: url.path) else { return nil }
        do {
            let data = try Data(contentsOf: url)
            let decoder = JSONDecoder()
            decoder.dateDecodingStrategy = .iso8601
            return try decoder.decode(SnapshotBundle.self, from: data)
        } catch {
            return nil
        }
    }

    func save(_ snapshot: SnapshotBundle, league: League) {
        let url = snapshotURL(for: league)
        do {
            let data = try JSONEncoder.iso8601.encode(snapshot)
            try data.write(to: url, options: .atomic)
        } catch {
            return
        }
    }

    private func snapshotURL(for league: League) -> URL {
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        let dir = base.appendingPathComponent("BetBoard", isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir.appendingPathComponent("snapshot_\(league.rawValue).json")
    }
}

extension JSONEncoder {
    static var iso8601: JSONEncoder {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        return encoder
    }
}
