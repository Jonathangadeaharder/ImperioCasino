# Security Documentation

## Security Model

ImperioCasino is a SvelteKit application backed by PocketBase (Go binary). This document outlines the security architecture, implemented controls, and remaining considerations.

## Architecture Security

### Stack

| Layer | Tech | Security Notes |
|-------|------|----------------|
| Frontend | SvelteKit, Svelte 5 | SSR by default, no client secrets |
| 3D | Threlte, Three.js | Client-side only, no security impact |
| Backend | PocketBase (Go binary) | Handles auth, DB, API rules |
| Auth | PocketBase auth | Cookie-based, httpOnly by default |
| Build | Vite | No runtime impact |

### Auth Flow

1. `hooks.server.ts` creates a PocketBase instance per request
2. Auth cookie (`pb_auth`) is loaded from request headers
3. If valid, `authRefresh()` revalidates the token server-side
4. `event.locals.user` is set for all downstream server load/action handlers
5. Auth guard in `+layout.server.ts` redirects unauthenticated users to `/login`
6. PocketBase SDK manages cookie lifecycle — no manual JWT handling

### Cookie Security (Implemented)

```typescript
// hooks.server.ts — actual cookie configuration
pb.authStore.exportToCookie({
  httpOnly: true,     // Prevents JavaScript access (XSS protection)
  secure: !dev,       // HTTPS-only in production
  sameSite: "lax",    // CSRF mitigation
  path: "/",          // Available on all routes
});
```

## Implemented Security Controls

### 1. Server-Side Game Logic ✅

**Control:** All game logic (blackjack, roulette, slots) runs in SvelteKit server endpoints under `src/lib/server/games/`. Client sends actions; server validates, executes, and returns results.

**Benefit:** Prevents client-side manipulation of game outcomes, payout calculations, or balance changes.

### 2. PocketBase Auth with httpOnly Cookies ✅

**Control:** Auth tokens stored in httpOnly cookies, not localStorage. Cookie flags: `httpOnly=true`, `sameSite=lax`, `secure=true` in production.

**Benefit:** Mitigates XSS-based token theft and CSRF attacks.

### 3. DB Abstraction Layer ✅

**Control:** Game logic uses `DBAdapter` interface (`src/lib/server/db/adapter.ts`), not direct PocketBase calls. Enables audit logging and validation at the adapter level.

**Benefit:** Single point of control for all data operations; easier to add authorization checks.

### 4. Auth Guard (Layout Server Load) ✅

**Control:** `src/routes/+layout.server.ts` redirects unauthenticated users to `/login` for all non-public paths.

**Benefit:** No game page or balance data accessible without authentication.

### 5. Input Validation in Server Endpoints ✅

**Control:**
- Blackjack: wager > 0 check, balance sufficiency check
- Roulette: non-empty bets check, total bet <= balance check
- Slots: balance >= 1 check before spin

**Benefit:** Prevents negative wagers, overspending, and empty requests.

### 6. PocketBase API Rules ✅

**Control:** `blackjack_games` collection has rules:
- List/View/Create/Update: `user = @request.auth.id` (users can only access their own games)
- Delete: disabled (no rule)

**Benefit:** Row-level security prevents users from reading or modifying other players' game state.

### 7. Dependency Version Pinning ✅

**Control:** All dependencies in `package.json` use caret ranges. `pnpm` lockfile ensures deterministic installs.

**Benefit:** Reduces supply chain attack surface.

## Remaining Security Considerations

### ⚠️ Important: Still To Do

1. **HTTPS Enforcement**
   - **Current State:** `secure: !dev` cookie flag only effective with HTTPS
   - **Risk:** Credentials transmitted in plain text over HTTP
   - **Recommendation:** Configure reverse proxy (Nginx/Caddy) with TLS certificates
   - **Priority:** Critical for production

2. **Rate Limiting**
   - **Current State:** No rate limiting on game endpoints
   - **Risk:** Abuse of spin/action endpoints for automated play
   - **Recommendation:** Add rate limiting middleware or PocketBase hooks
   - **Priority:** High

3. **CORS Configuration**
   - **Current State:** PocketBase default CORS (allows all origins in dev)
   - **Risk:** Cross-origin requests from malicious sites
   - **Recommendation:** Configure PocketBase CORS origins for production
   - **Priority:** Medium

4. **CSRF Protection**
   - **Current State:** `sameSite=lax` provides partial CSRF protection
   - **Risk:** POST requests from top-level navigations are allowed
   - **Recommendation:** Add SvelteKit CSRF protection (origin header check) or anti-CSRF token
   - **Priority:** Medium

5. **Audit Logging**
   - **Current State:** No audit trail for game actions or balance changes
   - **Risk:** Cannot investigate disputes or detect suspicious patterns
   - **Recommendation:** Log all game actions (spin, hit, stand) with timestamp, user, and result to PocketBase
   - **Priority:** Medium

6. **Content Security Policy (CSP)**
   - **Current State:** No CSP headers configured
   - **Risk:** XSS could load external scripts
   - **Recommendation:** Add CSP headers in `hooks.server.ts` via `resolve` response headers
   - **Priority:** Medium

7. **PocketBase Admin Access**
   - **Current State:** Default admin credentials set by `scripts/setup.sh` (`admin@imperiocasino.com` / `changeme123!`)
   - **Risk:** Default credentials are publicly visible in the repo
   - **Recommendation:** Change admin credentials immediately after first setup; use strong password
   - **Priority:** Critical

## Configuration

### Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `PUBLIC_POCKETBASE_URL` | PocketBase server URL | Yes (defaults to `http://127.0.0.1:8090` in code) |

See `.env.example` for template.

## Deployment Checklist

### Before Deploying to Production:

- [ ] Change PocketBase admin credentials from defaults
- [ ] Configure HTTPS/TLS certificates (reverse proxy)
- [ ] Set `PUBLIC_POCKETBASE_URL` to HTTPS endpoint
- [ ] Configure PocketBase CORS origins for production domains
- [ ] Add rate limiting to game endpoints
- [ ] Enable SvelteKit CSRF protection
- [ ] Add Content Security Policy headers
- [ ] Set up PocketBase database backups
- [ ] Review and test all authentication flows
- [ ] Run dependency audit: `pnpm audit`
- [ ] Set up monitoring and alerting
- [ ] Implement audit logging for game actions

### Production PocketBase Configuration

1. Change admin password from default
2. Configure email SMTP for password resets
3. Set production CORS origins
4. Enable HTTPS via reverse proxy
5. Set up regular `pb_data` backups

## Security Testing

### Recommended Tools

1. **Dependency Auditing:**
   ```bash
   pnpm audit
   ```

2. **Static Analysis:**
   ```bash
   pnpm dlx biome check
   ```

3. **Type Checking:**
   ```bash
   pnpm run check
   ```

4. **OWASP ZAP** or **Burp Suite** for penetration testing

### Regular Security Practices

1. **Keep dependencies updated:**
   ```bash
   pnpm outdated
   pnpm update
   ```

2. **Monitor PocketBase logs for suspicious activity**

3. **Regular security audits**

4. **Backup PocketBase data regularly**

5. **Test disaster recovery procedures**

## Reporting Security Issues

If you discover a security vulnerability, please email security@imperiocasino.com (DO NOT create a public issue).

## Compliance

This application implements security controls that align with:
- OWASP Top 10 Web Application Security Risks
- Basic GDPR requirements (password protection via PocketBase)
- PCI DSS recommendations (for future payment integration)

---

**Last Updated:** 2026-06-05
**Security Audit Version:** 2.0
**Status:** SvelteKit + PocketBase — Ready for staging deployment (NOT production without HTTPS + rate limiting)
