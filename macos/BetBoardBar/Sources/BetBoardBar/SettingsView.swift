import SwiftUI

struct SettingsView: View {
    @AppStorage(Defaults.refreshInterval) private var refreshInterval = 300
    @AppStorage(Defaults.defaultBooks) private var defaultBooks = ""
    @AppStorage(Defaults.keyValidationStatus) private var keyValidationStatus = ""
    @AppStorage(Defaults.keyValidationDate) private var keyValidationDate = ""
    @State private var apiKey: String = ""
    @State private var keyStatus: String = ""

    var body: some View {
        Form {
            Section("Odds API Key") {
                SecureField("API Key", text: $apiKey)
                HStack {
                    Button("Save Key") { saveKey() }
                    Button("Validate Key") { validateKey() }
                    Button("Clear Key") { clearKey() }
                    Spacer()
                    Text(keyStatus)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                if !keyValidationStatus.isEmpty {
                    Text(validationLine())
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Link("Get a key from The Odds API", destination: URL(string: "https://the-odds-api.com")!)
            }

            Section("Refresh") {
                Stepper(value: $refreshInterval, in: 60...3600, step: 60) {
                    Text("Refresh every \(refreshInterval) seconds")
                }
            }

            Section("Books") {
                TextField("Default books (comma-separated)", text: $defaultBooks)
            }

            Section("Notes") {
                Text("Data is fetched directly from The Odds API and ESPN RSS.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(20)
        .frame(width: 520)
        .onAppear { loadKey() }
    }

    private func loadKey() {
        do {
            apiKey = try KeychainHelper.read() ?? ""
            keyStatus = apiKey.isEmpty ? "No key saved" : "Key loaded"
        } catch {
            keyStatus = error.localizedDescription
        }
    }

    private func saveKey() {
        do {
            try KeychainHelper.save(apiKey)
            keyStatus = "Saved"
            keyValidationStatus = ""
            keyValidationDate = ""
        } catch {
            keyStatus = error.localizedDescription
        }
    }

    private func clearKey() {
        do {
            try KeychainHelper.delete()
            apiKey = ""
            keyStatus = "Cleared"
            keyValidationStatus = ""
            keyValidationDate = ""
        } catch {
            keyStatus = error.localizedDescription
        }
    }

    private func validateKey() {
        let key = apiKey.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !key.isEmpty else {
            keyStatus = "Enter a key first"
            return
        }
        keyStatus = "Validating..."
        Task {
            do {
                let ok = try await validateOddsApiKey(key)
                let now = ISO8601DateFormatter().string(from: Date())
                await MainActor.run {
                    keyValidationDate = now
                    keyValidationStatus = ok ? "ok" : "invalid"
                    keyStatus = ok ? "Key valid" : "Key invalid"
                }
            } catch {
                await MainActor.run {
                    keyStatus = error.localizedDescription
                }
            }
        }
    }

    private func validationLine() -> String {
        let label = keyValidationStatus == "ok" ? "Key: OK" : "Key: Invalid"
        if let date = ISO8601DateFormatter().date(from: keyValidationDate) {
            let formatter = DateFormatter()
            formatter.dateFormat = "MMM d h:mm a"
            return "\(label) (\(formatter.string(from: date)))"
        }
        return label
    }
}

private func validateOddsApiKey(_ key: String) async throws -> Bool {
    var components = URLComponents(string: "https://api.the-odds-api.com/v4/sports")
    components?.queryItems = [URLQueryItem(name: "apiKey", value: key)]
    guard let url = components?.url else {
        throw URLError(.badURL)
    }
    let (data, response) = try await URLSession.shared.data(from: url)
    guard let http = response as? HTTPURLResponse else {
        throw URLError(.badServerResponse)
    }
    if http.statusCode == 401 || http.statusCode == 403 {
        return false
    }
    guard (200...299).contains(http.statusCode) else {
        throw URLError(.badServerResponse)
    }
    let json = try JSONSerialization.jsonObject(with: data) as? [Any]
    return json != nil
}
