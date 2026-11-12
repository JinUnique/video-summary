# Optional Feishu/Lark Wiki delivery

Requires the official [lark-cli](https://github.com/larksuite/cli), the user's own
configured application/identity, document and Wiki permissions, and access to the
chosen Wiki space and parent. Installing Python dependencies does not provide any
of these. Follow the current official CLI setup and authorization instructions;
never copy another person's profile or credentials.

Copy `config.example.json` to ignored `config.json`, then fill the user's own
`feishu.space_id` and `feishu.parent_node_token`. `identity` defaults to `user`;
choose `bot` only for a destination the user intends the application to own/access.
Do not silently switch identities after an error. IDs identify a destination;
they are not access credentials and do not grant permission.

For an installed skill, keep persistent settings outside the skill and repository
at the user configuration location. See [private configuration](private-configuration.md)
for explicit-config/environment/default-path precedence and category preferences.

Use the README's Feishu preflight with live read enabled. It verifies the exact
space/parent with the selected identity and performs no writes. A successful help
command or CLI installation alone proves no document access. Missing settings or
permissions must stop before a write. Preflight failure is not a reason to fall
back to a different person's identity.

After the user requests this deliverable:

1. Discover existing categories below the configured parent using current CLI
   help and pagination. Record the decision locally in `doc/wiki_category_decision.json`.
   A category is an organizational choice, not the video-type decision itself.
2. Prepare `doc/summary_assets.json` and render with
   `runtime/scripts/render_feishu_summary_doc.py`. Preserve the existing schema
   used by the renderer: metadata, summary, navigation/chapters, evidence frames,
   diagrams and optionally `creator_learning`; Q&A mode has its own schema.
   Use [presentation](feishu-video-doc-presentation.md) and
   [native diagrams](feishu-native-diagram-workflow.md) when appropriate.
3. Inspect current `lark-cli docs +create --help`, `docs +update --help`,
   `docs +media-insert --help` and Wiki help before choosing flags. Local XML
   placeholders are not finished diagrams. Create only under the verified parent,
   fill each native board, insert frames and remove visible anchors.
4. For an existing document, fetch first, respect revision/concurrency guards,
   update in place and preserve its node/link. Never rebuild media-bearing content
   merely to revise text. Do not guess at the outcome of an uncertain write or
   retry it blindly.
5. Fetch the final document; verify title, summary callout, source links,
   timestamp navigation, complete diagrams and actual images. Q&A mode checks
   separate Q/A blocks and counts instead. Save the real delivery record and
   readback results under `feishu/`, then run the canonical run/presentation
   validators. A create receipt alone is not acceptance.

For ordinary summaries, use a native summary callout near the top, content-facing
chapter titles and diagrams that explain source content. Keep transcript coverage,
routing decisions, validation details and tool logs out of the reader-facing page.
Only insert third-party media within the user's authorized use and applicable rights.

The local staging exercise checks blank-config rejection and XML rendering only.
It does not claim a live Feishu write using a stranger's new account was tested.
