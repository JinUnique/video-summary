# Current lark-cli Writeback Quirks for Video Summary

Session source: completed Bilibili video-summary delivery with `lark-cli 1.0.44`, plus live `lark-cli` v2/XML help observed during the presentation-regression fix.

Use this reference when loaded Feishu skill examples, memory snippets, and live `lark-cli --help` disagree. The live CLI help and a bounded dry-run win.

## Command Shape Rule

Before Feishu writeback, check the installed shortcut help and read the version-matched embedded docs skill references that the CLI points to:

```bash
lark-cli docs +create --help
lark-cli docs +update --help
lark-cli docs +media-insert --help
lark-cli docs +whiteboard-update --help
lark-cli wiki nodes list --help
lark-cli wiki +node-create --help
lark-cli skills read lark-doc references/lark-doc-create.md
lark-cli skills read lark-doc references/lark-doc-xml.md
lark-cli skills read lark-doc references/lark-doc-update.md
```

Use `scripts/video_summary_preflight.py --entry <terminal|feishu> --delivery feishu --live-feishu-read` to record this as a run artifact.

## Create With Category Parent and Blank Whiteboards

Render rich XML locally first, then create the summary under the selected category parent, not the Wiki root:

```bash
python3 scripts/render_feishu_summary_doc.py \
  --assets runs/<run-id>/doc/summary_assets.json \
  --output runs/<run-id>/doc/feishu_summary.xml

LARK_CLI_NO_PROXY=1 lark-cli docs +create \
  --api-version v2 \
  --parent-token <CATEGORY_PARENT_NODE_TOKEN> \
  --content @runs/<run-id>/doc/feishu_summary.xml
```

Do not use the old `--wiki-node` / `--title` / `--markdown` create shape for generated reader-facing summaries. That Markdown import path can duplicate the title, collapse metadata quotes, and lose callout richness. Only use `--doc-format markdown --content @file.md` when the user explicitly provides Markdown to import.

If `feishu_summary.xml` contains blank whiteboards:

```markdown
<whiteboard type="blank"></whiteboard>
```

The create result returns `data.document.new_blocks` in document order. Persist both `block_id` and `block_token` mapping to `feishu/whiteboard_update_plan.json` before updating any board.

## Update Whiteboards

For current `lark-cli`, either `docs +whiteboard-update` or `whiteboard +update` can update a blank board token. `--source @...` is resolved from the command cwd, so when diagram files live under a run directory, pass the full run-relative path from repo root:

```bash
LARK_CLI_NO_PROXY=1 lark-cli docs +whiteboard-update \
  --whiteboard-token <BOARD_TOKEN> \
  --input_format mermaid \
  --source @runs/<run-id>/diagrams/c01.mmd \
  --overwrite \
  --idempotent-token <10+chars>
```

Keep the same principles: stdin/file source, explicit format, overwrite only newly created boards, and idempotent token. If the CLI reports `--source: cannot read file "diagrams/..."`, do not retry blindly; switch to `@runs/<run-id>/diagrams/...` or change cwd to the run directory.

## Insert Local Evidence Frames

`docs +media-insert --file` can target a text selection and should receive a relative file path from the image directory in this environment:

```bash
cd runs/<run-id>/frames/evidence
LARK_CLI_NO_PROXY=1 lark-cli docs +media-insert \
  --doc <DOC_ID> \
  --file ./c01_frame.jpg \
  --type image \
  --align center \
  --width 720 \
  --caption "视频时间戳｜...｜00:00" \
  --selection-with-ellipsis "【证据帧锚点：c01_frame】"
```

Record the cwd, relative file, exit code, stdout, and stderr for each insert in `feishu/media_insert_results.json`.

If an image lands at the document end, fetch block IDs with `docs +fetch --api-version v2 --detail with-ids --scope keyword` around the caption/anchor, then move it with `docs +update --command block_move_after --block-id <chapter_or_anchor_block_id> --src-block-ids <image_block_id>`. Do not rebuild the entire document after images/whiteboards exist unless the user explicitly approves losing those resource blocks.

## Remove Anchor Placeholders

After inserting all images, remove visible anchor lines with `str_replace` or exact block deletion:

```bash
LARK_CLI_NO_PROXY=1 lark-cli docs +update \
  --api-version v2 \
  --doc <DOC_ID> \
  --command str_replace \
  --pattern "【证据帧锚点：c01_frame】" \
  --content ""
```

Do not use the old `--mode delete_range` or `replace_all --markdown ''` examples. Current update shortcuts use `--command` and XML by default; Markdown mode is only for user-provided Markdown or explicit Markdown imports.

## Readback Verification

After delivery, verify both placement and content:

1. `wiki nodes list` for the selected category parent includes the new doc title or doc id. Current CLI uses `--params`, not top-level `--space-id` flags:

   ```bash
   LARK_CLI_NO_PROXY=1 lark-cli wiki nodes list \
     --params '{"space_id":"<FEISHU_WIKI_SPACE_ID>","parent_node_token":"<CATEGORY_PARENT_NODE_TOKEN>","page_size":50}' \
     --format json
   ```

   If an older helper returns `unknown flag "--space-id"`, this is a command-shape drift, not a missing document; rerun with `--params` before failing readback.
2. `docs +fetch --api-version v2 --doc <DOC_ID> --doc-format xml --detail full --format json` contains title/metadata/summary, all chapter headings, expected whiteboard markers/tokens, expected image markers/tokens, and zero leftover anchor text.
3. For presentation-contract validation, prefer a fresh `docs +fetch --detail simple` artifact after full readback succeeds. Full/with-ids fetches include Feishu-generated block IDs; those random IDs can contain substrings such as `QA` and trigger false positive reader-facing quality-term leaks. Preserve the full fetch as `fetch_result_full_with_ids.json` for block/media audit, but feed the validator the simple XML fetch unless the validator explicitly ignores attributes. If even simple fetch includes resource tokens such as `<whiteboard token="...">` that accidentally contain blocked QA/report substrings, keep the live fetch for readback evidence and pass the locally rendered reader-facing XML through `--presentation-input runs/<run-id>/doc/feishu_summary.xml` for `validate_video_summary_run.py`.
4. `scripts/validate_feishu_presentation_contract.py` passes on the fetched JSON or rendered XML.
5. Persist `readback_verification.json`, `delivery_record.json`, and the presentation-contract report under `runs/<run-id>/feishu/`.

Minimum readback record:

```json
{
  "wiki_child_list_mentions_doc": true,
  "has_title": true,
  "chapter_heading_count": 7,
  "whiteboard_token_count": 8,
  "image_token_count_approx": 7,
  "anchor_leftover_count": 0,
  "ok": true
}
```

## ASR Retry Linkage

If Feishu writeback succeeds only after ASR retry, preserve both transcript validations. `delivery_record.json` should point to the accepted ASR attempt and include non-null media/transcript quality fields so a future audit can see why the no-VAD transcript became canonical.
