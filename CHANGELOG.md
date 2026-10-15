# Changelog

## Unreleased

- Shop screens use one ledger chrome: sample banner, local-data chip, import steps, phone inventory list, and export rows that name the file.
- Forecast provenance says TabPFN with a version, a named fallback, or "Engine not recorded". Missing quantities say "Not set". A real zero stays 0.
- Unknown routes keep the closed-shutter 404, including the chalkboard line "TODAY'S STOCK: One missing page!"

## 0.1.0

First usable local build.

- Marketing site, sample kirana, CSV import, inventory, baseline forecasts, TabPFN adapter, reorder advice, template explanations, and CSV exports.
- TabPFN 9.1.0 is wired for `ModelVersion.V2`. It was not executed in the verification run because the package was not installed in the test environment.
- Docker Compose is defined. Images were not built in that same run.
