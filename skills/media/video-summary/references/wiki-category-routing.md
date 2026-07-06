# Feishu Wiki Category Routing

Use this reference when `video-summary` delivers a Feishu Wiki document. The goal is to place each new summary under the best existing top-level parent document, which acts as the Wiki category directory. Do not write custom Feishu operation scripts for this routing layer; use `lark-cli` commands directly and keep the decision record as a local artifact or agent-report note.

## Configured Wiki

Configure the target Wiki space before any Feishu delivery:

```text
VIDEO_SUMMARY_WIKI_SPACE_ID=<FEISHU_WIKI_SPACE_ID>
```

Treat `/wiki/space/<id>` as a `space_id`, not a node token. Category directories are the top-level nodes in that space whose `parent_node_token` is empty.

No default space is shipped with the repository. Do not hard-code a personal Wiki URL, space ID, node token, or current category snapshot into the skill. Always discover live nodes at runtime because each user may have different Wiki organization and permissions.

## Runtime Discovery

Before creating a new summary document, list top-level category parents:

```bash
lark-cli wiki nodes list \
  --as user \
  --params '{"space_id":"<SPACE_ID>","page_size":50}' \
  --format json
```

For each top-level node that may be a category, list children to infer the real category profile:

```bash
lark-cli wiki nodes list \
  --as user \
  --params '{"space_id":"<SPACE_ID>","parent_node_token":"<CATEGORY_NODE_TOKEN>","page_size":50}' \
  --format json
```

If any result has `has_more: true`, paginate with `page_token` or use `--page-all` if the current CLI supports it. Only inspect titles, node metadata, and summary-document structure needed to understand the category; do not read unrelated private documents.

## Decision Artifact

Record the routing decision outside the Feishu document body, for example in `wiki_category_decision.json` or the final agent report:

```yaml
wiki_category_decision:
  space_id: "<FEISHU_WIKI_SPACE_ID>"
  primary_type: ai_video_creation_creative_short_script
  secondary_types: [entertainment_film_variety_microdrama]
  candidates:
    - title: Creator Production Analysis
      action: use_existing
      score: 0.86
      evidence:
        - category name matches video/creator analysis
        - child document is a creator-mechanics breakdown
        - summary primary value is reusable production learning
    - title: General Knowledge and Content Analysis
      action: considered
      score: 0.61
      evidence:
        - child documents include AIGC workflow and animation analysis
        - less specific than selected category for creator craft transfer
  selected_parent:
    title: Creator Production Analysis
    node_token: <runtime-discovered-token>
  confidence: high
  reason: The summary's main value is creator/video-production learning, not general knowledge notes.
```

Do not place the full routing audit in the reader-facing summary page unless the user explicitly wants it; include only a short category note in the completion report.

## Selection Strategy

Choose the category by the summary's primary value, not by the first matching keyword.

Scoring signals, in priority order:

1. the user's stated purpose: learning creator craft, investment decision understanding, tutorial reproduction, news awareness, product decision, etc.
2. `video_type_decision.primary_type` and meaningful `secondary_types` from `references/video-type-summary-strategies.md`.
3. Summary title, tags, UP/creator, description, transcript opening, chapter titles, sampled frames.
4. Existing category names and child-document distribution.
5. Avoidance of clutter: prefer a broad existing category over creating a narrow one for a single unusual video.

When multiple directories match, select the one closest to the document's main reusable value:

- Creator/video production technique beats general knowledge.
- Finance/business decision logic beats generic knowledge.
- Product buying decision beats tutorial/knowledge if the output is mainly consumer choice.
- Interview/podcast category only beats topic categories when the speaker contrast itself is the main value.
- Entertainment/story analysis goes to a creator-production category when the value is craft/format/retention learning; it goes to a broader content-analysis category when the value is primarily interpretation of the work itself.

## Current Category Mapping Heuristics

These are runtime heuristics for the current Wiki; refresh after any Wiki reorganization.

| Video type | Preferred existing category | Notes |
|---|---|---|
| `finance_business_investment` | Existing finance/business/knowledge parent | Use for market, company, business model, investment, valuation, industry mechanism, and risk-analysis summaries. |
| `knowledge_course_tutorial` | Existing tutorial/knowledge parent, or the topic-specific parent | Use a finance parent only when the learning object is finance/business. Use a creator-production parent when the tutorial's main value is video/creator production craft. |
| `politics_social_news` | Existing current-affairs/social-observation parent, or a configured fallback category | Do not force into a generic knowledge parent if the value is event awareness and stakeholder/timeline analysis. |
| `entertainment_film_variety_microdrama` | Existing creator-production or content-analysis parent | Use creator-production for story mechanics, retention, production craft, format design; use content-analysis for interpretation of the work itself. |
| `ai_video_creation_creative_short_script` | Existing creator-production/AIGC workflow parent | Use when the output is meant to teach script, prompt, shot, editing, sound, or production transfer. |
| `interview_podcast_dialogue` | Existing interview/podcast parent if speaker contrast is the main value; otherwise route by topic | If the interview is mainly about finance or creator craft, route to that topic parent instead. |
| `product_review_consumption_decision` | Existing product-review/consumer-decision parent | Avoid mixing buying advice into generic knowledge when the output is a decision tree. |
| `vlog_life_travel` | Existing life/travel/VLOG parent, or a configured fallback category | Do not create location-specific directories for one-off travel videos. |
| `mixed_or_unknown` | Best existing category by primary value, else configured fallback category | Preserve uncertainty in the decision artifact. |

## Creating A New Category Parent

Do not create new Wiki categories by default. Create a broad reusable top-level category only when the user has explicitly authorized category creation for the current run or has documented that policy in local configuration. This authorization never covers arbitrary Wiki reorganization, deleting/moving/renaming existing nodes, or creating narrow one-off directories.

Create a new top-level category only when all are true:

- No existing category has a clear score advantage.
- The run is a real video-summary delivery under the configured/requested Wiki, not a speculative catalog cleanup.
- The candidate category is broad enough for future videos, not a single creator, single title, single episode, single product, or single event.
- The category name is concise and user-facing.
- A normalized duplicate/near-duplicate check found no close existing directory.

Recommended broad category names:

- `Current Affairs and Society`
- `Product Reviews and Buying Decisions`
- `Interviews and Podcasts`
- `Travel and Life Vlogs`
- `Uncategorized`

Before creation, check for near duplicates by normalizing Chinese/English punctuation, spaces, case, and generic suffixes such as `类`、`内容`、`分析`、`合集`.

Create the category with `lark-cli`, not a wrapper script:

```bash
lark-cli wiki +node-create \
  --as user \
  --space-id <SPACE_ID> \
  --title "Uncategorized"
```

For shortcut dry-runs such as `wiki +node-create` and `docs +create`, do not append `--format` unless `--help` for that exact shortcut shows it. In the current CLI, `wiki nodes list` supports `--format json`, but these create shortcuts print their dry-run request without a `--format` flag.

If this fails because of permission or scope, keep the local summary artifact, report the exact failure category, and do not fall back to creating the summary at Wiki root unless the user explicitly approves.

## Creating The Summary Under A Category

After selecting or creating the category parent, render XML and create the summary document under that parent node:

```bash
python3 scripts/render_feishu_summary_doc.py \
  --assets runs/<run-id>/doc/summary_assets.json \
  --output runs/<run-id>/doc/feishu_summary.xml

lark-cli docs +create \
  --api-version v2 \
  --parent-token <CATEGORY_PARENT_NODE_TOKEN> \
  --content @runs/<run-id>/doc/feishu_summary.xml
```

Then continue the existing writeback flow: update blank whiteboards, insert media as needed, and read back with `lark-cli docs +fetch`.

Prefer `--parent-token <CATEGORY_PARENT_NODE_TOKEN>` for categorized delivery. Use root-level creation only when intentionally creating a top-level category or when the user explicitly wants a root-level document.

## Fallback Rules

- **Cannot classify but Wiki is writable:** use or create `Uncategorized`, then report the uncertainty and evidence gap.
- **No top-level categories exist:** create `Uncategorized` first unless the user requested a specific category name.
- **No suitable category but the topic is clearly broad and recurring:** create a concise broad category, then create the summary as its child.
- **Multiple close candidates:** choose the closest primary value and record the runner-up with reason.
- **Feishu API/CLI fails after local summary is ready:** preserve local artifacts, do not lose the generated summary, and report the failed command category, return code, and non-secret error summary.
- **Repeated create failure:** do not keep retrying; switch to offline/local delivery and ask the user whether to repair Feishu auth/scope.

## Verification Checklist

After delivery or dry-run validation:

- [ ] Top-level categories were listed from the current Wiki, not assumed from memory.
- [ ] Existing child distribution was checked for candidate categories.
- [ ] `wiki_category_decision` records selected parent, candidate evidence, confidence, and fallback/new-category reason if any.
- [ ] No duplicate or near-duplicate category was created.
- [ ] The final document's node is listed under the selected parent via `wiki nodes list`.
- [ ] The delivered document is read back via `docs +fetch`.
- [ ] `scripts/validate_feishu_presentation_contract.py` passes on the fetched XML/JSON or generated `doc/feishu_summary.xml`.
- [ ] If a new category was created, it is broad enough for reuse and its first child is the intended summary.
- [ ] If actual write was not run, `docs +create --dry-run` or `wiki +node-create --dry-run` proves the intended lark-cli request shape.
