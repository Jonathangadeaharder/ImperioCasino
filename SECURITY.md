# Security Documentation

## Security Model

ImperioCasino is a SvelteKit application backed by PGlite (embedded Postgres in WASM) with Drizzle ORM. This document outlines the security architecture, implemented controls, and remaining considerations.

## Architecture Security

### Stack

| Layer | Tech | Security Notes |
|-------|------|----------------|
| Frontend | SvelteKit, Svelte 5 | SSR by default, no client secrets |
| 3D | Threlte, Three.js | Client-side only, no security impact |
| Database | PGlite (embedded Postgres WASM) | In-process, no network exposure |
| ORM | Drizzle ORM | Parameterized queries, no raw SQL |
| Auth | bcryptjs + hashed session tokens | 12 salt rounds, sha256 token hashing |
| Build | Vite | No runtime impact |

### Auth Flow

1. `hooks.server.ts` calls `ensureDb()` (PGlite boots in-process on first request)
2. A `DrizzleAdapter` is attached to `event.locals.db`
3. `event.locals.auth()` reads the `imperio_session` cookie
4. The session token is sha256-hashed and looked up in the `session` table
5. If valid and unexpired, the `user` row is loaded into `event.locals.user`
6. Protected routes redirect unauthenticated users to `/login`
7. Cookies are httpOnly, sameSite=lax, secure in production

### Cookie Security (Implemented)

```typescript
// auth-service.ts — actual cookie configuration
event.cookies.set(COOKIE_NAME, token, {
  httpOnly: true,                            // Prevents JS access (XSS protection)
  secure: process.env.NODE_ENV === "production", // HTTPS-only in production
  sameSite: "lax",                           // CSRF mitigation
  path: "/",                                 // Available on all routes
});
```

### Password Storage

- Passwords hashed with bcrypt (12 salt rounds) via `bcryptjs`
- Never stored in plaintext
- Sign-in uses constant-time `bcrypt.compare`
- A dummy bcrypt hash is compared on missing-user lookups to resist timing attacks

### Session Tokens

- 32-byte cryptographically random tokens (`crypto.randomBytes`)
- Stored sha256-hashed in the `session` table; the plaintext token never touches the DB
- 7-day expiry, checked on every authenticated request
- Deleted server-side on sign-out

## Implemented Security Controls

### 1. Server-Side Game Logic

All game logic (blackjack, roulette, slots) runs in SvelteKit server endpoints under `src/lib/server/games/`. Client sends actions; server validates, executes, and returns results. Prevents client-side manipulation of game outcomes, payout calculations, or balance changes.

### 2. bcrypt Password Hashing with httpOnly Cookies

Passwords hashed with bcrypt (12 salt rounds). Session tokens stored in httpOnly cookies with `secure` and `sameSite=lax` flags. Mitigates XSS-based token theft and CSRF attacks.

### 3. DB Abstraction Layer

Game logic uses the `DBAdapter` interface (`src/lib/server/db/adapter.ts`), not direct Drizzle calls. Single point of control for all data operations; enables audit logging and authorization checks.

### 4. Auth Guard (Hooks)

`src/hooks.server.ts` redirects unauthenticated users to `/login` for all non-public paths. No game page or balance data accessible without authentication.

### 5. Input Validation in Server Endpoints

- Blackjack: wager > 0 check, balance sufficiency check
- Roulette: non-empty bets check, total bet <= balance check
- Slots: balance >= 1 check before spin

### 6. Parameterized Queries

All database access goes through Drizzle ORM, which uses parameterized queries. No string-interpolated SQL, eliminating SQL injection risk.

### 7. Timing-Attack Resistance

Sign-in compares against a dummy bcrypt hash when the email is not found, so the response time does not reveal whether an account exists.

### 8. Security Headers

`hooks.server.ts` sets `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, and a restrictive `Permissions-Policy`.

## Remaining Security Considerations

### Important: Still To Do

1. **HTTPS Enforcement**
   - **Current State:** `secure` cookie flag only effective with HTTPS
   - **Risk:** Credentials transmitted in plain text over HTTP
   - **Recommendation:** Configure reverse proxy (Nginx/Caddy) with TLS certificates
   - **Priority:** Critical for production

2. **Rate Limiting**
   - **Current State:** No rate limiting on game or auth endpoints
   - **Risk:** Brute-force login, automated play of spin/action endpoints
   - **Recommendation:** Add rate limiting middleware
   - **Priority:** High

3. **CSRF Protection**
   - **Current State:** `sameSite=lax` provides partial CSRF protection
   - **Risk:** POST requests from top-level navigations are allowed
   - **Recommendation:** Enable SvelteKit CSRF protection (origin header check)
   - **Priority:** Medium

4. **Audit Logging**
   - **Current State:** No audit trail for game actions or balance changes
   - **Risk:** Cannot investigate disputes or detect suspicious patterns
   - **Recommendation:** Log all game actions with timestamp, user, and result
   - **Priority:** Medium

5. **Content Security Policy (CSP)**
   - **Current State:** No CSP header configured
   - **Risk:** XSS could load external scripts
   - **Recommendation:** Add a CSP header in `hooks.server.ts`
   - **Priority:** Medium

## Configuration

### Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `PGLITE_DATA_DIR` | PGlite data directory (`memory` for ephemeral, path for persistent) | No (defaults to `.pglite`) |

See `.env.example` for template.

## Deployment Checklist

### Before Deploying to Production:

- [ ] Configure HTTPS/TLS certificates (reverse proxy)
- [ ] Set `PGLITE_DATA_DIR` to a persistent path with backups
- [ ] Add rate limiting to game and auth endpoints
- [ ] Enable SvelteKit CSRF protection
- [ ] Add a Content Security Policy header
- [ ] Review and test all authentication flows
- [ ] Run dependency audit: `pnpm audit`
- [ ] Set up monitoring and alerting
- [ ] Implement audit logging for game actions
- [ ] Configure PGlite data backups

## Security Testing

### Recommended Tools

1. **Dependency Auditing:**
   ```bash
   pnpm audit
   ```

2. **Static Analysis:**
   ```bash
   pnpm dlx @biomejs/biome check
   ```

3. **Type Checking:**
   ```bash
   pnpm run check
   ```

4. **OWASP ZAP** or **Burp Suite** for penetration testing

## Reporting Security Issues

If you discover a security vulnerability, please email security@imperiocasino.com (DO NOT create a public issue).

---

**Last Updated:** 2026-07-17
**Status:** SvelteKit + PGlite + Drizzle — Ready for staging deployment (NOT production without HTTPS + rate limiting)
