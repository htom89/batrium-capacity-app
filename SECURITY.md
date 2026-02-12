# Security & Privacy Notes

- Never commit Home Assistant long-lived tokens.
- This app stores token only in browser localStorage on the machine where it runs.
- Revoke HA token after testing if no longer needed.
- Do not expose this app to the public internet without authentication/reverse-proxy controls.
