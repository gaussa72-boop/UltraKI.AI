# Quantum Payments & Credits

Shared prepaid-credit contract. Credits are granted only after verified idempotent payment events. Stripe/crypto are provider adapters; never store crypto private keys or custody funds. Production state must use a transactional persistent ledger. Reserve credits before paid generation and release on failure. Store secrets only in deployment secret management.
