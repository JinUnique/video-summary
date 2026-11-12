# Wiki category routing

For requested Feishu delivery, load the user's destination and preferences from
[private configuration](private-configuration.md), verify its space and parent,
then discover the parent's current category children. Paginate the CLI results;
a Wiki space ID is not a node token. Do not reuse node tokens from examples.

Choose by the user's purpose, primary video type, useful secondary types, source
metadata/transcript, and the actual category names and child distribution. Apply
the user's `category_rules` only after this discovery. Purpose matters: a joke
bank meant for retelling uses `qa_list`, even when the broad video type is
entertainment; a creator-craft lesson may belong with video production rather
than general knowledge. Topic-based interviews need not all become podcasts.

Record `doc/wiki_category_decision.json` with the selected parent, considered
categories, purpose, type and supporting evidence. Keep this internal record out
of the reader-facing document. Check for an existing summary of the same source
and multipart target before creating a duplicate. Existing documents are updated
in place when requested, preserving their link and media resources.

If no existing category fits, follow the current user's creation preference and
task scope. Normalize punctuation, spacing and common suffixes to check near
duplicates first. A new category must be broad enough for future videos; never
create a directory named after one video, creator, product or event merely to
finish this run. A preference does not authorize unrelated reorganization.

Use current lark-cli help and its document/Wiki tools. On permission or identity
failure, keep the local summary and report the exact read/write stage; do not
switch identities, change the destination, or drop the document at Wiki root.
