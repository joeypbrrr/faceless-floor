# Faceless Floor

A 3D Wall Street–style "exchange" where 50 research agents look for viral, **faceless** social pages to learn from.

- **Live research:** https://joeypbrrr.github.io/faceless-floor/ (driven by `data/live.json`, updated hourly)
- **Sample preview:** https://joeypbrrr.github.io/faceless-floor/preview/ (placeholder data only)

## How it runs
- One supervised runner: `scripts/hourly-loop.sh`. It holds a `flock` lock so only one instance can run, and starts one cycle per hour through `scripts/run-once.sh --push`.
- `research/pipeline.py` runs all 50 agent tasks in order, writes `data/live.json`, and the runner commits and pushes once per cycle.
- Discovery terms and sources are in `config/discovery.json`; [DISCOVERY.md](DISCOVERY.md) explains each choice. Manual faceless reviews are in `config/reviews.json`.
- The face models aren't in git. Download them into `research/models/` from opencv_zoo: `face_detection_yunet_2023mar.onnx` and `face_recognition_sface_2021dec.onnx`.

## Rules
- Research only: no posting, no social accounts, no messages.
- Only public, unauthenticated sources. No logins, keys or bot-check bypass. Blocked sources are logged and shown on the site.
- Faceless = no real human recurs on camera. AI-generated content (AI voice, images, video, avatars) counts as faceless; see [DISCOVERY.md](DISCOVERY.md#faceless-check). One-off re-score of the first cycle under this rule: `research/rescore/`.
- Numbers are never estimated. Unknown stays unknown, and the Top 10 only lists pages that pass every check.
- Replication copies formats and hooks only, never anyone's content.
