# Portable runtime

Use Python 3.10–3.12 (3.12 was exercised), ffmpeg/ffprobe, and a fresh virtual
environment installed from the repository's `requirements.txt`. Read the README
quick start in the downloaded repository. Do not use system Python for packages.
All paths in examples are relative to the repository root; installed skills carry
their own `runtime/`, `references/`, requirements and license.

Find the actual installed skill directory from its SKILL.md location. Scripts are
under that directory's `runtime/scripts/`; the Python interpreter must be the
user's prepared venv, not a guessed fixed path. Use absolute run/output paths
when invoking the script from another directory. Installing a skill copies code
only; it does not install Python packages, models, ffmpeg, or another assistant.

For an established local installation, check whether
`~/.local/share/video-summary/venv/bin/python` exists before creating another
environment. The same shared environment can serve a research checkout and an
installed skill. A local `~/.local/share/video-summary/models/faster-whisper-base`
can be passed as `--model` to reuse downloaded weights. These are portable user
directory conventions, not bindings to any particular machine or account.
For a deliberate global/custom installation, the installer supports `--target`
with the exact assistant skill directory; it refuses an existing directory.

`prepare_video.py` uses public API metadata and public audio/video, downloads the
named ASR model on first use, normalizes audio, checks ASR coverage, selects initial
frames, and validates evidence. It saves a checkpoint before each expensive stage.
After `evidence_ready`, the assistant still has to classify, inspect, write, and
read back the actual summary.

Default ASR: faster-whisper 1.2.1, model `base`, CPU int8. Cold model download needs
access to Hugging Face and may take minutes. Choose a larger model for difficult
speech, with the user's hardware/time constraints in mind. The PyAV 16.1.0 pin
avoids an incompatible API change. Coverage checks catch a missing tail, not every
ASR hallucination or mistranscribed word. A tiny test or this machine's successful
run does not guarantee source availability or accuracy on another video.

No Lark CLI is invoked by offline preflight. Feishu settings are loaded only for
Feishu delivery, using the precedence in `private-configuration.md`. There is no
automatic account, group, workspace, or assistant-profile binding.
