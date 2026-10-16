# Stage 21.3.3 — ROM V2 configuration and secrets

- **Status:** `IMPLEMENTED`
- **Canonical owner:** `rom_v2.settings.V2Settings`
- **Secret wrapper:** `rom_v2.settings.SecretValue`
- **Source:** process environment only

## Configuration boundary

`V2Settings.from_environment()` validates application name, environment, log level, runtime paths, and the required bot token. Domain and application code do not read `.env` or `os.environ` directly.

## Secret policy

Secrets are wrapped by `SecretValue`. String and repr output are always redacted. The protected value may be revealed only at an external adapter boundary. Safe summaries omit secret values and secret metadata.

## Git policy

Local `.env` variants are ignored. `.env.example` remains trackable and contains only blank placeholders.

## Automated evidence

- Tracked text files scanned: **1372**.
- High-confidence secret findings: **0**.
- Local dotenv files ignored: **True**.
- Blank example trackable: **True**.

## Next roadmap stage

Stage 21.3.4 — Dependency container.
