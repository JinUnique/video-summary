# Serial Queue Supervision for Video Summary Docs

Use this reference when the user provides a Feishu/Lark document that contains multiple video links and asks the main controller to supervise sub-agents processing every link.

## Controller Contract

the main controller remains the controller. Worker output is candidate evidence until independently read back.

1. Read the source document first and extract video links in original order.
2. Create a local supervision log with source doc URL/token, source revision, ordered queue, current item, completed items, removed links, and failures.
3. Dispatch exactly one Hermes child agent for exactly one video link at a time.
4. The child agent must load `video-summary` and complete the full Feishu-lane workflow for that single link.
5. The child agent must not edit the source queue document, delete links, publish externally, or process adjacent links.
6. The controller verifies the worker result before moving on: final validation JSON, Feishu readback, wiki/category placement, required counts/keywords, and any platform-specific evidence such as Bilibili `p=` target.
7. Only after acceptance, delete the corresponding source-document link/block and immediately read back the source document.
8. If validation fails, keep the source link in place and log failure reason plus next action.
9. Continue until the original queue is exhausted; final report must include totals, products, failures, source-document state, and residual risks.

## Feishu Source Document Pattern

For a Wiki/Doc source document, prefer this two-read pattern:

- `docs +fetch --doc-format markdown --detail simple` for human-readable link extraction.
- `docs +fetch --doc-format xml --detail full` for block IDs used by exact deletion.

Do not use `--detail full` with `--doc-format markdown`; current `lark-cli docs +fetch` rejects that combination.

For exact deletion:

1. Re-fetch XML immediately before deletion, because previous deletions change document revision and list structure.
2. Locate the exact `<li id="...">...</li>` whose text equals the original URL after HTML unescape.
3. Delete only that block with `docs +update --command block_delete --block-id <id>`.
4. Re-fetch markdown and assert the exact URL is absent.
5. Count remaining video URLs and write the result into the supervision log.

## Bilibili Multi-Part Guard

When multiple queue entries share a BV but differ by `p=`, treat them as distinct items.

Child-agent brief must explicitly state:

- preserve and target the exact `p=<n>` parameter;
- return target `p`, `cid`, `part/title`, duration, and proof it is not default P1 or a previous item;
- include this evidence in readback/final validation whenever possible.

The controller should read `metadata/page_target.json` or equivalent before accepting the item.

## Acceptance Evidence

Minimum acceptance for each successful queue item:

- original video URL;
- Feishu deliverable URL/doc token;
- run directory;
- final validation path with `ok=true`;
- Feishu readback summary: title, chapter count, whiteboard count, image/frame count or intentionally zero, anchor count, required keyword hits;
- Bilibili multi-part evidence when applicable;
- source-link deletion readback result.

## Failure Handling

A failed or incomplete child-agent run never authorizes source-link deletion. Record:

- failure step;
- whether local media/transcript/Feishu writeback exists;
- specific blocker or validation miss;
- recommended retry path.

Continue to the next queued link only after the failed item is logged and confirmed retained in the source document.
