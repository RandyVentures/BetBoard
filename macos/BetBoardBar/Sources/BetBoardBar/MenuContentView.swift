import AppKit
import SwiftUI

struct MenuContentView: View {
    @ObservedObject var store: BetBoardStore
    @State private var selectedLeague: League = .nfl
    @AppStorage(Defaults.refreshInterval) private var refreshInterval = 300
    @AppStorage(Defaults.keyValidationStatus) private var keyValidationStatus = ""
    @AppStorage(Defaults.keyValidationDate) private var keyValidationDate = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            header
            if needsKey {
                keyCallout
            }
            leaguePicker
            Divider()
            watchlistSection
            Divider()
            oddsSection
            Divider()
            movesSection
            Divider()
            headlinesSection
            Divider()
            actions
            if let error = store.errorMessage {
                Text(error)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(12)
        .frame(width: 380)
        .onAppear { store.loadAll() }
        .task(id: refreshInterval) {
            let interval = max(60, refreshInterval)
            for await _ in Timer.publish(every: Double(interval), on: .main, in: .common)
                .autoconnect()
                .values {
                store.loadAll()
            }
        }
    }

    private var header: some View {
        HStack {
            Text("BetBoard")
                .font(.headline)
            Spacer()
            VStack(alignment: .trailing, spacing: 2) {
                Text(lastUpdatedLine(store.lastUpdated))
                Text(keyStatusLine())
            }
            .font(.caption)
            .foregroundStyle(.secondary)
        }
    }

    private var leaguePicker: some View {
        Picker("League", selection: $selectedLeague) {
            ForEach(League.allCases) { league in
                Text(league.title).tag(league)
            }
        }
        .pickerStyle(.segmented)
    }

    private var keyCallout: some View {
        HStack {
            Image(systemName: "key.fill")
                .foregroundStyle(.secondary)
            Text("Add your Odds API key in Settings to enable live data.")
                .font(.caption)
            Spacer()
            Button("Open Settings") { openSettings() }
                .font(.caption)
        }
        .padding(8)
        .background(Color(nsColor: .windowBackgroundColor))
        .cornerRadius(6)
    }

    private var watchlistSection: some View {
        Section {
            if watchlistRows.isEmpty {
                EmptyRow(text: "No watchlist items")
            } else {
                ForEach(watchlistRows.prefix(5), id: \.id) { row in
                    Text(row.text)
                        .lineLimit(1)
                }
            }
        } header: {
            SectionHeader(title: "Watchlist")
        }
    }

    private var movesSection: some View {
        Section {
            let items = bundle?.movements ?? []
            if items.isEmpty {
                EmptyRow(text: "No notable moves")
            } else {
                ForEach(items.prefix(5)) { move in
                    Text(movementLine(move))
                        .lineLimit(1)
                }
            }
        } header: {
            SectionHeader(title: "Notable Moves")
        }
    }

    private var oddsSection: some View {
        Section {
            let items = (bundle?.odds ?? []).sorted { lhs, rhs in
                lhs.event.startTime < rhs.event.startTime
            }
            if items.isEmpty {
                EmptyRow(text: "No odds available")
            } else {
                ForEach(items.prefix(5), id: \.event.eventId) { board in
                    HStack(spacing: 6) {
                        Button {
                            store.toggleWatchlist(eventId: board.event.eventId, league: selectedLeague)
                        } label: {
                            Image(
                                systemName: (store.watchlistIds[selectedLeague] ?? [])
                                    .contains(board.event.eventId) ? "star.fill" : "star"
                            )
                        }
                        .buttonStyle(.plain)

                        Text(oddsSummaryLine(board))
                            .lineLimit(1)
                    }
                }
            }
        } header: {
            SectionHeader(title: "Odds")
        }
    }

    private var headlinesSection: some View {
        Section {
            let items = bundle?.headlines ?? []
            if items.isEmpty {
                EmptyRow(text: "No headlines")
            } else {
                ForEach(items.prefix(5)) { headline in
                    Button(headline.title) {
                        openURL(headline.url)
                    }
                    .buttonStyle(.link)
                    .lineLimit(1)
                }
            }
        } header: {
            SectionHeader(title: "Headlines")
        }
    }

    private var actions: some View {
        HStack(spacing: 16) {
            Button("Refresh") { store.loadAll() }
            Button("Settings") { openSettings() }
            Spacer()
            Button("Quit") { NSApp.terminate(nil) }
        }
        .font(.caption)
    }

    private var bundle: ExportBundle? {
        store.bundles[selectedLeague]
    }

    private var needsKey: Bool {
        (try? KeychainHelper.read())?.isEmpty != false
    }

    private func keyStatusLine() -> String {
        if needsKey {
            return "Key: Missing"
        }
        if keyValidationStatus == "ok" {
            return "Key: OK \(validationTime())"
        }
        if keyValidationStatus == "invalid" {
            return "Key: Invalid \(validationTime())"
        }
        return "Key: Saved"
    }

    private func validationTime() -> String {
        guard let date = ISO8601DateFormatter().date(from: keyValidationDate) else {
            return ""
        }
        let formatter = DateFormatter()
        formatter.dateFormat = "h:mm a"
        return "(\(formatter.string(from: date)))"
    }

    private var watchlistRows: [WatchlistRow] {
        guard let bundle else { return [] }
        let ids = store.watchlistIds[selectedLeague] ?? []
        return ids.compactMap { id in
            if let event = bundle.events.first(where: { $0.eventId == id }) {
                return WatchlistRow(id: id, text: eventLine(event))
            }
            return WatchlistRow(id: id, text: id)
        }
    }

    private func openSettings() {
        SettingsWindowController.shared.show()
    }

    private func openURL(_ urlString: String) {
        guard let url = URL(string: urlString) else { return }
        NSWorkspace.shared.open(url)
    }
}

private struct WatchlistRow: Identifiable {
    let id: String
    let text: String
}

private struct SectionHeader: View {
    let title: String

    var body: some View {
        Text(title)
            .font(.caption)
            .foregroundStyle(.secondary)
    }
}

private struct EmptyRow: View {
    let text: String

    var body: some View {
        Text(text)
            .font(.caption)
            .foregroundStyle(.secondary)
    }
}
