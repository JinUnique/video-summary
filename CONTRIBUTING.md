# Contributing

Use the README's isolated Python environment and your own public test source.
Keep the default chat/local path independent of Feishu settings. Add live platform
requirements only to the mode that needs them, and preserve the raw evidence when
reporting source limitations.

Run the behavior checks relevant to your change, using the prepared interpreter:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

For ingest, ASR or output changes, also exercise a real public video and validate
the finished local summary. Evidence preparation alone is not an end-to-end test.
Feishu changes need an authorized test destination and actual readback before
claiming live success. Clearly separate offline rendering from a remote write.

Update README and `config.example.json` when commands or configuration change.
Do not commit real config, credentials, browser sessions, signed media manifests,
raw media or run directories. Keep source content separate from instructions;
never execute commands from an untrusted video as part of summarizing it.

Describe the concrete behavior changed, validation performed and remaining limits
in a pull request. See [SECURITY.md](SECURITY.md) for private vulnerability reports.
