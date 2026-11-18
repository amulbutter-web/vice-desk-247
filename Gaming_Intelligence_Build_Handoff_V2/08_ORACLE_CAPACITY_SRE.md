# ORACLE 24/7 OPERATIONS, RESOURCE BUDGET AND 15-STREAM VALIDATION

## Objective and evidence
User wants no phone/laptop powered on, fully supervised cloud service, primarily **free bootstrap** on Oracle, later reinvest for expansion. The Oracle official public Free Tier page at the time of this research states Ampere A1 **1,500 OCPU-hours and 9,000 GB-hours/month** (equivalent to 2 OCPU and 12 GB all month within eligible availability). This is an *allocation*, not a promise of capacity or reservation, free network egress, available inventory, disk layout or model-runtime support. Source: https://www.oracle.com/cloud/free/ and https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm .

**Important distinction**: a 2-OCPU host might keep several compressed streams buffered, but simultaneous 15× full video decode, local ASR, video VLM and 1080p transcode is another workload. Never assert '15 streams free'. The full target stays in PRD and is achievable only on *measured* suitable infrastructure.

## Topology staged plan
- **Pilot A (one VM)**: Ubuntu ARM64, small FastAPI UI/API, SQLite (single-owner pilot) or PostgreSQL, filesystem with reserved media volumes, FFmpeg probe/record and low-concurrency media render, external Gemini or tested inference provider for video judgment, HTTPS reverse proxy, systemd or Compose restart, logs and alerts. No credentials committed. This is an experiment, not guaranteed scale.
- **Pilot B (structured workers)**: Postgres (or sound small durable DB), worker process separate from API, durable job rows, optional Redis only if proven necessary; shared media volume and deterministic work leases. Avoid Redis-as-only-durable-queue unless configured for persistence.
- **Scaled C (15-feed)**: small control host, separate FFmpeg/ASR/render nodes, queue and object storage. Optional GPU workers if measured effective. Autoscaling/backpressure and shutdown behavior tested under realistic load; retain source fair scheduling.

## ARM64 technical preflight (must record)
`uname -m`, OS version, `ffmpeg -version` and enabled filters (libass, crop, zscale and encoders), ffprobe, Python version and package availability for sherpa-onnx, selected ASR, OpenCV, mediapipe, Pillow, relevant PyTorch/onnxruntime, image codecs; model weights fit disk/RAM and run on AArch64. Docker multiarch image check and pinned dependency test. Record measured per-job CPU/RAM, wall time, power/cost and possible OOM. Do not assume Apple Silicon (`mlx`) libraries run on Linux ARM.

## Resource estimation formula (fill with measured values)
For `N=15`, compute: network ingress `Σ input_bitrate_i * 1.1`; rolling-media disk = `Σ bitrate_i * retention_seconds / 8` + overhead; concurrent decode CPU = per-stream decoded frame cost × frame sample rate; render CPU/GPU = mean CPU-seconds per output / desired output completion interval; ASR/VLM concurrency bound = hardware and API token/rate quotas. Include max concurrent active clips, buffer size, retry reserve, pending media and egress to publication endpoints. Treat paid external inference/egress as resource budgets even if OCI is free.

**Illustrative arithmetic only:** If 15 streams average 5 Mbps each, inbound bandwidth ≈75 Mbps before overhead, and one minute retained across them ≈562.5 MB of compressed data. This does not establish availability, decoded RAM footprint or platform permission. Measure actual game bitrates; codec, segmenting and mirrored retention change the result.

## Production bootstrap checklist
1. Create/verify OCI tenancy and eligible Always Free quota; avoid surprise paid shapes; set budgets/alerts and inspect network/storage billing.
2. Provision Linux VM with firewall/default-deny inbound; SSH keys, limited user, security updates, separate data volume as appropriate; disable public control UI until auth and TLS exist.
3. Install Docker/Compose or tested systemd services; select ARM64-compatible dependencies and pin SHAs; make secret refs read-only; do NOT expose local PeakCut default unauthenticated UI.
4. Set up HTTPS domain/reverse proxy if required for Meta media staging; signed expiring media URL, scoped content; never expose an unrestricted source-video bucket.
5. Start Postgres/SQLite with schema migrations and backups, job queue, media lifecycle, retry handler, owner auth, alert bot and dashboard.
6. Backup encrypted DB + configuration + consent/metadata separately from ephemeral raw media; automatic daily snapshots and restore test. GitHub code backup does not back up DB or secrets.
7. Periodic monitoring includes CPU/memory/disk/inodes/bandwidth, queue depth, oldest job age, capture lag, ASR latency, remote API 429/5xx, token validity, quota remaining, missing analytics, duplicates prevented, error budget and financial spend.
8. Add alerts with source/job ID, failing stage, severity, last successful checkpoint, next automated action and operator action; suppress storms with dedupe.
9. Add safe stop (drain jobs, maintain outbox, don't delete or partially publish) and emergency kill switch for all public posting.
10. Preserve logs without leaking bearer tokens, private stream URLs, chat users or full transcripts unnecessarily. Rotate credentials and practice incident restoration.

## Capacity test plan (actual target)
For each load level `N = 1,2,5,15` conduct at least a controlled 60–120 minute test on permissioned or synthetic streams, then a longer soak for stability. These durations are **proposed test designs**, not claims of completion. Include differing codecs/bitrates, simultaneous peaks, 5-minute source disconnect, 50% API 429 period, one full worker restart, disk below watermark, disabled ASR provider and 3 simultaneous publishing operations to a test account.

Measure raw ingest continuity, source loss rate, missed events (gold labels), event-to-preview p50/p95/p99, manual approve-to-confirmed-publish p50/p95, queue age by source, RAM peak, CPU load/steal, disk and network, model API errors, energy/cost, bytes/sec, simultaneous render throughput, and correctness of recovery/duplicates. Do NOT simply report process uptime or '15 streams connected'.

**Pass definition**: required event quality thresholds met with each of the 15 independent sources receiving its fair processing share, no S0 errors, actual configured services surviving crashes and continued operations, budgets not exceeded and owner-signed result summary. If OCI fails capacity, that is a sizing finding; propose compute offload or paid capacity while preserving the final product requirement. Use measured latency budgets per phase, not 'instant' as an unmeasurable slogan.

## Reliability, failure and cost policies
- Lease renewal and restart-safe queue; at-least-once work plus dedupe; publisher remote reconciliation before retry.
- Background cleanup only for terminal-state media older than contract retention and supported by remote status plus backup; stop cleanup if disk pressure threatens unconfirmed media, alert and backpressure.
- API and cloud costs monitored with current provider prices; request financial approval before paid dependencies/egress exceed set cap.
- Provider outages queue or route to quality-equivalent tested model; never silently publish missing QC.
- NTP time sync, log timestamps in UTC, local dashboard displays operator time zone; source time mapping not based solely on wall time.
- Health probe MUST check both API process and effective processing throughput; worker alive but queue stalled is not healthy.

## Runbook examples
`IG publish pending > configured max`: block same intent, query remote container/media status, show owner alert, don't blind retry. `source reconnect`: create discontinuity epoch, preserve pre/post segments if valid, backfill only from authorized source. `bad subtitles`: stop release, mark ASR for recheck, rerender and rerun all QC. `disk nearly full`: disable new bulk upload intake, reduce nonessential buffer retention within rights contract and preserve approved/pending assets, page owner. `cloud VM reclaimed`: restore encrypted backup on alternate host, rehydrate durable queue, reconcile remote posts before restarting publisher.
