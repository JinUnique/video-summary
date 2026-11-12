# Serial video queues

When the user requests processing a document or list containing multiple videos,
one controller owns the queue. Read the source first and save its revision,
original link order, current item, accepted results and failures in a local
supervision log. Keep exactly one media/ASR worker active at a time on a local
machine unless the user explicitly requests a different concurrency plan.

A worker receives one exact URL and one run directory. It must preserve the
platform video ID and any Bilibili `p=` target, and must not edit the source queue,
process adjacent links, delete source blocks or publish unrelated content. Use
`metadata/page_target.json` to check part index, cid, title and duration.

Before advancing, the controller independently checks the result: local validation,
the actual summary and its source, multipart target, and, when Feishu delivery is
requested, document readback, category, nonempty diagrams/images and required
content. Finding an old run is not acceptance: verify its source and part, rerun
validation and reread the remote document before reusing it.

Remove a consumed source link only when the current task authorizes queue
consumption and its result has been accepted. For a remote document, re-fetch
the current revision, target the exact URL block, perform the scoped update and
read back absence immediately. A worker failure never authorizes deletion. Keep
failed links, record their stage and next action, then continue only as requested.

Report original item count, accepted deliverables, retained failures, remaining
source links and readback evidence. Producing a candidate or starting an ASR
process is not completion of the queue item.
