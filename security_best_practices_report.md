# Security Best Practices Report

## Executive Summary

This review covered runtime behavior, static security risks, dependency exposure, and deployment hygiene for `ragbot`.

The repo is in materially better shape after cleanup:

- Hardcoded credentials were removed from code and docs.
- REST endpoints now support API-key protection.
- Twilio webhooks now support signature validation.
- Arbitrary public URL scraping and Twilio media downloads now enforce SSRF checks and size limits.
- Raw exception leakage was reduced on the main API and file-upload paths.
- The service now boots on a low-resource machine without installing `sentence-transformers` or GPU `torch`.
- User metadata persistence was reduced and JSON writes are now atomic with restrictive file permissions.

Validation completed:

- `pytest -q tests`: `6 passed`
- `pip-audit -r requirements.txt`: no known dependency vulnerabilities
- `bandit`: reduced to 2 low-severity findings in the optional Asterisk voice helper
- Runtime boot check: local server started successfully and `/health`, `/upload`, and `/query` worked on `127.0.0.1:8011`

## Remediated In This Pass

### RBP-001
- Severity: Critical
- Location: [main.py](/home/hs-chilu/ragbot/main.py#L51), [main.py](/home/hs-chilu/ragbot/main.py#L161), [main.py](/home/hs-chilu/ragbot/main.py#L196), [main.py](/home/hs-chilu/ragbot/main.py#L219)
- Evidence: REST routes now go through `require_api_key(...)`, which checks `X-API-Key` when `API_KEY` is configured.
- Impact: Previously, unauthenticated callers could write to the knowledge base or trigger outbound scraping.
- Fix: Added optional API-key enforcement and typed request validation on public write/query routes.

### RBP-002
- Severity: High
- Location: [main.py](/home/hs-chilu/ragbot/main.py#L114), [main.py](/home/hs-chilu/ragbot/main.py#L249), [main.py](/home/hs-chilu/ragbot/main.py#L277), [main.py](/home/hs-chilu/ragbot/main.py#L308), [main.py](/home/hs-chilu/ragbot/main.py#L342)
- Evidence: Webhook routes now call `validate_twilio_request(...)` before processing form data.
- Impact: Previously, forged Twilio-style requests could drive bot actions and media fetches.
- Fix: Added Twilio signature validation with optional `PUBLIC_BASE_URL` support for reverse-proxied deployments.

### RBP-003
- Severity: High
- Location: [web_research.py](/home/hs-chilu/ragbot/web_research.py#L25), [security_utils.py](/home/hs-chilu/ragbot/security_utils.py#L18), [whatsapp_bot.py](/home/hs-chilu/ragbot/whatsapp_bot.py#L75)
- Evidence: User-supplied URLs and media URLs are checked with `validate_public_http_url(...)`; private/reserved destinations are rejected.
- Impact: Previously, attackers could coerce the app into fetching arbitrary URLs, including internal services.
- Fix: Added URL allow/deny logic, hostname resolution checks, Twilio host allowlisting, and outbound size limits.

### RBP-004
- Severity: Medium
- Location: [main.py](/home/hs-chilu/ragbot/main.py#L161), [whatsapp_bot.py](/home/hs-chilu/ragbot/whatsapp_bot.py#L87)
- Evidence: Uploads now enforce size limits, content-type restrictions, UTF-8 validation, and filename sanitization.
- Impact: Previously, uploads could cause memory pressure, decode failures, or accept unexpected content with poor validation.
- Fix: Added size caps, content validation, and safer file-name handling.

### RBP-005
- Severity: Medium
- Location: [user_manager.py](/home/hs-chilu/ragbot/user_manager.py#L54), [user_manager.py](/home/hs-chilu/ragbot/user_manager.py#L67)
- Evidence: JSON writes now use atomic temp-file replacement and `0600` permissions; stored user data now keeps only the last 4 digits instead of the full phone number.
- Impact: Previously, local file corruption and unnecessary PII retention were more likely.
- Fix: Added atomic writes, restrictive permissions, and reduced persisted personal data.

### RBP-006
- Severity: Medium
- Location: [requirements.txt](/home/hs-chilu/ragbot/requirements.txt#L1), [rag_system.py](/home/hs-chilu/ragbot/rag_system.py#L16), [embeddings.py](/home/hs-chilu/ragbot/embeddings.py#L12)
- Evidence: `sentence-transformers` was removed from mandatory dependencies and replaced with a lazy embedding provider that falls back to a lightweight hashing backend.
- Impact: The previous dependency path attempted to pull heavyweight GPU `torch` packages, which made the advertised low-resource deployment story unreliable.
- Fix: Added a lazy embedding layer and kept the better model path optional.

### RBP-007
- Severity: Critical
- Location: [install_ec2_asterisk.sh](/home/hs-chilu/ragbot/install_ec2_asterisk.sh#L21), [install_ec2_asterisk.sh](/home/hs-chilu/ragbot/install_ec2_asterisk.sh#L148), [install_ec2_asterisk.sh](/home/hs-chilu/ragbot/install_ec2_asterisk.sh#L185), [quo_client.py](/home/hs-chilu/ragbot/quo_client.py#L498)
- Evidence: Static passwords/API keys were removed and replaced with generated or environment-supplied values.
- Impact: Hardcoded credentials in a public repository create immediate credential leakage and replay risk.
- Fix: Replaced embedded secrets with generated placeholders and environment lookups; scrubbed exposed examples from docs.

## Remaining Findings

### RBP-008
- Severity: Medium
- Location: [main.py](/home/hs-chilu/ragbot/main.py#L51), [.env.example](/home/hs-chilu/ragbot/.env.example#L18)
- Evidence: API-key enforcement is conditional. If `API_KEY` is empty, protected REST routes remain open.
- Impact: A production deployment without `API_KEY` still exposes upload, query, stats, and research routes to unauthenticated callers.
- Fix: Set `API_KEY` in production, or make API-key auth mandatory behind a feature flag.
- Mitigation: Put the app behind an authenticated reverse proxy or private network if API key auth is intentionally disabled.
- False positive notes: This is less important if the service is only bound to localhost or already protected by upstream auth.

### RBP-009
- Severity: Medium
- Location: [install_ec2_asterisk.sh](/home/hs-chilu/ragbot/install_ec2_asterisk.sh#L121), [install_ec2_asterisk.sh](/home/hs-chilu/ragbot/install_ec2_asterisk.sh#L182), [install_ec2_asterisk.sh](/home/hs-chilu/ragbot/install_ec2_asterisk.sh#L194)
- Evidence: The Asterisk installer still binds SIP, AMI, and HTTP listeners to `0.0.0.0`.
- Impact: If the EC2 security group is permissive, telephony and admin interfaces become internet-facing.
- Fix: Bind only to the private interface where possible and narrow the EC2 security-group rules.
- Mitigation: Keep UFW and EC2 security groups locked down to known source IPs.
- False positive notes: Risk is lower if the instance lives on a private subnet or the security group already blocks those ports.

### RBP-010
- Severity: Low
- Location: [voice_agent_v2.py](/home/hs-chilu/ragbot/voice_agent_v2.py#L107), [voice_agent_v2.py](/home/hs-chilu/ragbot/voice_agent_v2.py#L129)
- Evidence: The optional voice helper still invokes `ffmpeg` via `subprocess.run(...)`.
- Impact: This adds local command-execution surface, though the current implementation uses a fixed argument vector and does not use `shell=True`.
- Fix: Keep this path behind trusted operator workflows, validate input paths carefully, and run it under a constrained service account.
- Mitigation: Limit filesystem access and do not expose this helper directly to untrusted users.
- False positive notes: This is an optional helper and was the only remaining Bandit finding after cleanup.

### RBP-011
- Severity: Low
- Location: [user_manager.py](/home/hs-chilu/ragbot/user_manager.py#L54), [user_manager.py](/home/hs-chilu/ragbot/user_manager.py#L125)
- Evidence: Session history and user stats are still stored as plaintext JSON files on local disk, even though permissions were tightened.
- Impact: A local host compromise would still expose conversation history.
- Fix: Move state to an encrypted store or encrypt sensitive fields at rest.
- Mitigation: Keep the application host hardened and backups protected.
- False positive notes: This is acceptable for local/dev use, but not ideal for higher-sensitivity production workloads.
