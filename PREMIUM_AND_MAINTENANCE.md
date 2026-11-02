# Premium plans and maintenance notice

This repository's application may present the following subscription options. These terms are informational until the application's payment and entitlement backend is implemented and verified.

- **Single-site Premium:** €10 per month for one website.
- **Lifetime Premium:** €150 one-time for lifetime access across the other participating websites and web services.
- **Payment method:** Bitcoin. Payment must be verified server-side before Premium access is granted.
- **Payment destination:** `bc1qs0quxgqq26kawsq8al0kcxx3690jnp3a3zflce`

## Maintenance notice

> **Wartungsarbeiten**  
> Einige Bereiche dieser Webseite befinden sich derzeit in Wartung. Wir arbeiten daran, alle Funktionen schnellstmöglich bereitzustellen.  
> Vielen Dank für deine Geduld und dein Verständnis.

## Implementation requirements

Registration and sign-in must be handled by the application's existing authentication system. Premium status must be stored and checked server-side; never trust a client-side flag or a submitted transaction ID alone. Verify the Bitcoin transaction and its confirmation policy before granting paid access. Do not expose private credentials in client code. The maintenance notice should be scoped to affected areas and must not disable registration, account access, or payment support unless intentionally configured.

This file documents the shared product requirements; it does not itself enable registration, process payments, or activate subscriptions.
