import Foundation

struct RssClient {
    func fetchHeadlines(for league: League) async throws -> [Headline] {
        let urlString: String
        switch league {
        case .nfl:
            urlString = "https://www.espn.com/espn/rss/nfl/news"
        case .cfb:
            urlString = "https://www.espn.com/espn/rss/ncf/news"
        case .ufc:
            urlString = "https://www.espn.com/espn/rss/mma/news"
        }
        guard let url = URL(string: urlString) else { return [] }
        let (data, _) = try await URLSession.shared.data(from: url)
        return RSSParser().parse(data: data)
    }
}

final class RSSParser: NSObject, XMLParserDelegate {
    private var items: [Headline] = []
    private var currentElement = ""
    private var currentTitle = ""
    private var currentLink = ""
    private var currentDate = ""
    private var inItem = false

    func parse(data: Data) -> [Headline] {
        let parser = XMLParser(data: data)
        parser.delegate = self
        parser.parse()
        return items
    }

    func parser(_ parser: XMLParser, didStartElement elementName: String, namespaceURI: String?, qualifiedName qName: String?, attributes attributeDict: [String : String] = [:]) {
        currentElement = elementName
        if elementName == "item" {
            inItem = true
            currentTitle = ""
            currentLink = ""
            currentDate = ""
        }
    }

    func parser(_ parser: XMLParser, foundCharacters string: String) {
        guard inItem else { return }
        switch currentElement {
        case "title":
            currentTitle += string
        case "link":
            currentLink += string
        case "pubDate":
            currentDate += string
        default:
            break
        }
    }

    func parser(_ parser: XMLParser, didEndElement elementName: String, namespaceURI: String?, qualifiedName qName: String?) {
        if elementName == "item" {
            inItem = false
            items.append(
                Headline(
                    title: currentTitle.trimmingCharacters(in: .whitespacesAndNewlines),
                    url: currentLink.trimmingCharacters(in: .whitespacesAndNewlines),
                    publishedAt: RSSParser.parseDate(currentDate),
                    source: "ESPN"
                )
            )
        }
        currentElement = ""
    }

    static func parseDate(_ value: String) -> Date? {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.dateFormat = "EEE, dd MMM yyyy HH:mm:ss Z"
        return formatter.date(from: value.trimmingCharacters(in: .whitespacesAndNewlines))
    }
}
