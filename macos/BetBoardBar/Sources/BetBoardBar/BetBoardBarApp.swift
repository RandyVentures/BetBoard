import SwiftUI

@main
struct BetBoardBarApp: App {
    @StateObject private var store = BetBoardStore()

    var body: some Scene {
        MenuBarExtra {
            MenuContentView(store: store)
        } label: {
            StatusItemView(count: store.notableMoveCount)
        }
        .menuBarExtraStyle(.window)

        Settings {
            SettingsView()
        }
    }
}

private struct StatusItemView: View {
    let count: Int

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: "chart.line.uptrend.xyaxis")
            if count > 0 {
                Text("\(count)")
                    .font(.caption2)
                    .fontWeight(.semibold)
            }
        }
    }
}
