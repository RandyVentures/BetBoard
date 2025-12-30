import Foundation

struct OddsApiClient {
    let apiKey: String
    let baseURL = URL(string: "https://api.the-odds-api.com/v4")!

    func listSports() async throws -> [OddsApiSport] {
        let url = baseURL.appendingPathComponent("sports")
        let request = try buildRequest(url: url, query: ["apiKey": apiKey])
        let (data, response) = try await URLSession.shared.data(for: request)
        try validate(response)
        let decoder = decoderWithISO8601()
        return try decoder.decode([OddsApiSport].self, from: data)
    }

    func fetchOdds(leagueKey: String, markets: [String], regions: String) async throws -> [OddsApiEvent] {
        let url = baseURL.appendingPathComponent("sports/\(leagueKey)/odds")
        let query: [String: String] = [
            "apiKey": apiKey,
            "regions": regions,
            "markets": markets.joined(separator: ","),
            "oddsFormat": "american",
        ]
        let request = try buildRequest(url: url, query: query)
        let (data, response) = try await URLSession.shared.data(for: request)
        try validate(response)
        let decoder = decoderWithISO8601()
        return try decoder.decode([OddsApiEvent].self, from: data)
    }

    private func buildRequest(url: URL, query: [String: String]) throws -> URLRequest {
        var components = URLComponents(url: url, resolvingAgainstBaseURL: false)
        components?.queryItems = query.map { URLQueryItem(name: $0.key, value: $0.value) }
        guard let fullURL = components?.url else {
            throw URLError(.badURL)
        }
        return URLRequest(url: fullURL, cachePolicy: .reloadIgnoringLocalCacheData, timeoutInterval: 20)
    }

    private func validate(_ response: URLResponse) throws {
        guard let http = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }
        guard (200...299).contains(http.statusCode) else {
            if http.statusCode == 401 || http.statusCode == 403 {
                throw OddsApiError.invalidKey
            }
            throw URLError(.badServerResponse)
        }
    }

    private func decoderWithISO8601() -> JSONDecoder {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let value = try container.decode(String.self)
            if let date = formatter.date(from: value) {
                return date
            }
            let alt = ISO8601DateFormatter()
            alt.formatOptions = [.withInternetDateTime]
            if let date = alt.date(from: value) {
                return date
            }
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Invalid date")
        }
        return decoder
    }
}

enum OddsApiError: LocalizedError {
    case invalidKey

    var errorDescription: String? {
        switch self {
        case .invalidKey:
            return "Odds API key invalid"
        }
    }
}
