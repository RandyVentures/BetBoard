// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "BetBoardBar",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(name: "BetBoardBar", targets: ["BetBoardBar"])
    ],
    targets: [
        .executableTarget(
            name: "BetBoardBar",
            path: "Sources/BetBoardBar"
        )
    ]
)
