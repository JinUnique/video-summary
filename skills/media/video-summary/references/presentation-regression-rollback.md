# Presentation Regression Rollback

Use this when the user rejects a video-summary delivery because the new artifact is not actually better than the previous version, especially when native diagrams, frame evidence, or document structure regressed.

## Durable Pattern

1. Treat the user's quality correction as an instruction to restore the known-good artifact shape, not as a prompt to keep polishing the rejected version.
2. Locate both versions from chat/session evidence and delivery records: the current rejected document and the earlier accepted/better document.
3. Read back both documents and compare presentation-critical counts before changing anything:
   - native Feishu whiteboards / diagrams;
   - inserted frame evidence images;
   - callout/highlight blocks;
   - chapter heading count and expected keywords such as `摘要` and `图解`.
4. If the rejected version used Markdown fallback and lost native diagrams, do not treat it as the official Feishu deliverable. Keep or restore the rich XML/native-whiteboard version as the official output.
5. For skill rollback, sync the full live skill directory back to the canonical source/known-good version, not only `SKILL.md`; extra reference files and drifted references can keep the bad behavior alive.
6. Verify live skill readback and source/live directory parity before reporting completion.
7. Do not delete the rejected Feishu document unless the user explicitly asks for deletion or archiving; external document deletion/cleanup is a separate high-risk action.

## Report Shape

- State which document is now official.
- Report diagram/image counts from readback.
- State what was rolled back in the live skill and how it was verified.
- If a rejected document remains in Wiki, call it out as retained intentionally and ask for explicit cleanup instruction if needed.
