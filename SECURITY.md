# Security policy

DukaanDost is a local-first tool. A deployment on a shared server needs the operator to protect that server. This repository does not add accounts in the first version.

## Reporting

Open a private security report to the maintainers. Do not attach real customer billing files.

## What we expect from the app

- Upload size is capped.
- CSV parsing does not keep the raw file.
- Errors returned to the browser do not include stack traces or filesystem paths.
- The explanation model cannot run SQL or shell commands.
- Sales rows are not sent to a cloud LLM by default.

See `docs/SECURITY_AND_PRIVACY.md`.
