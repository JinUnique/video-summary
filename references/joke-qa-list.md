# Joke and riddle Q&A collections

Use `qa_list` when the user wants questions they can search, remember, or retell.
For one video, write a title, compact source line, and numbered pairs in source
order. Each question is a bold paragraph and its answer is a separate paragraph.
Do not put Q and A inside one list item when delivering to Feishu: readback can
flatten it into one block.

For a requested series, consolidate into one document with a compact episode index,
episode headings, separate source links and dates, and `01.01` style numbering.
Verify each episode independently. Expand an existing document in place when
requested, preserving its link. Do not move unrelated existing documents.

Retain the setup, clue, punchline and wordplay. Light paraphrasing can improve
retellability; identify it in the source note. Flag an unrecoverable answer instead
of guessing. No extra plot analysis, lessons, explanations, diagrams or screenshots
unless the user requests them. Ordinary full-summary presentation requirements do
not apply to this profile.

The existing XML renderer accepts `presentation_profile: "qa_list"`,
`document_title`, `source_url`, and `qa_items` containing `question`, `answer`, and
optional `start_seconds`. A series uses `qa_groups`; each group has `title`,
`source_url`, `published_date` and `qa_items`. The renderer supplies the index and
episode numbering. Read back complete pairs, separate paragraph blocks, sources,
episode count and item count. Use the presentation validator's `qa_list` profile.

For Feishu, select an existing relevant category under the configured parent.
The example category profile is a suggestion only and carries no real destination.
