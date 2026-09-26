# Stage 19.23.3h: story quest item drop notification

The canonical drop producer now returns the configured drop message only for a real bounded grant. The combat consumer sends that message once. A separate scoped helper supports a dry-run and exact quest-4 item reset for manual retesting without resetting the character. Manual verification is required.
