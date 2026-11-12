# Configuration outside the repository

The distribution contains no personal destination. Chat/offline preflight never
loads Feishu settings. When the user requests Feishu delivery, resolve configuration
in this order:

1. The path passed with `--config`.
2. The path in `VIDEO_SUMMARY_CONFIG`.
3. `$XDG_CONFIG_HOME/video-summary/config.json`, or
   `~/.config/video-summary/config.json` when XDG_CONFIG_HOME is not set.

An absent default is normal for a new installation. Do not guess a workspace or
borrow another person's identity. Use `config.example.json` as the blank template.
The chosen parent must be verified live before any write; preflight performs
read-only access and does not create or modify a document.

Supported preference fields:

- `feishu.space_id`, `feishu.parent_node_token`, `feishu.identity`: the user's own
  destination and intended identity. Current-request overrides take precedence.
- `category_profiles`: map a category title to `qa_list` or an object containing
  `profile` and optional `topics`. These are assistant instructions, not a router
  that assigns an existing node without reading the current category list.
- `category_rules`: ordered assistant routing preferences; a rule can contain
  `primary_types`, `intent_keywords`, `preferred_categories`, and `notes`.
  An explicit destination or purpose in the current request wins.
- `category_creation.allow_broad_categories_for_requested_delivery`: defaults to
  false. A true user preference covers broad, reusable categories only within a
  requested summary delivery; it grants no general reorganize/move/delete access.

Do not store API keys, OAuth tokens, cookies or copied browser profiles in this
configuration. The CLI manages its own secure authorization. Real destination IDs
and private rules belong only in the user's config, not a repository or installed
skill. A useful report records configuration source and live-read outcome without
printing resource identifiers.
