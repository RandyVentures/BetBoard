# BetBoardBar (macOS Menu Bar)

SwiftUI menu bar app that pulls odds + headlines directly from The Odds API and ESPN RSS.

## Run (SwiftPM)

```bash
cd macos/BetBoardBar
swift run
```

## Build a .app bundle

```bash
cd macos/BetBoardBar
./scripts/package_app.sh
```

The app bundle will be created at `macos/BetBoardBar/dist/BetBoard.app`.

## Settings

Use the Settings window to enter your Odds API key and refresh interval.

## Install a release build

1) Download the latest `BetBoard-<version>.zip` from GitHub Releases.
2) Unzip and drag `BetBoard.app` into `/Applications`.
3) If macOS blocks the app, run:

```bash
xattr -dr com.apple.quarantine /Applications/BetBoard.app
```

## Data Sources

- The Odds API (odds + lines)
- ESPN RSS (headlines)

Movement detection uses the last snapshot stored in Application Support.
