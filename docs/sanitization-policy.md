# Sanitization Policy

Auto-evoloop public examples must be synthetic.

Do not commit:

- real user, customer, employee, patient, debtor, contract, payment, health, financial, or support conversation data,
- trace exports, logs, screenshots, case reports, or feedback exports from private systems,
- `.env` files, credentials, cookies, sessions, tokens, private keys, or API keys,
- internal endpoints, private package indexes, private repository names, database URLs, or cache URLs,
- business-specific prompts or evaluation datasets.

If you are unsure whether data is safe, do not commit it. Replace it with a small fictional fixture that demonstrates the same shape and behavior.

The `evoloop trace clean` command is a convenience helper, not a privacy guarantee. It redacts common sensitive key names and should be followed by human review before any trace-like artifact is shared publicly.

Allowed examples:

- fictional subscription support requests,
- fake session ids such as `synthetic-session-001`,
- local rule-based scoring fixtures,
- trace JSON created by hand for documentation or tests.
