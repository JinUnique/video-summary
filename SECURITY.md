# Security Policy

## Supported Versions

Security fixes are handled on the default branch unless a maintainer documents a
separate release branch.

## Reporting a Vulnerability

Please report suspected vulnerabilities through GitHub Security Advisories when
available for this repository. If advisories are unavailable, contact a
maintainer privately rather than opening a public issue with exploit details.

Include:

- affected files or commands;
- the impact and reproduction steps;
- whether any token, cookie, private Wiki identifier, or browser session may
  have been exposed.

## Secret Handling

Never commit:

- `.env` or other local config files containing real workspace values;
- cookies, API keys, OAuth tokens, browser profiles, or session databases;
- private Feishu/Lark Wiki space IDs, document URLs, or chat identifiers;
- raw logs that include credentials or private workspace metadata.

Use `config.example.json` for destination field examples only; keep real values in ignored `config.json`.
