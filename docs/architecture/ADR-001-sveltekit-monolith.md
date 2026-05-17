# ADR-001: SvelteKit Monolith with PocketBase Backend

**Status:** Accepted

**Context:** The existing casino platform uses Flask + React/jQuery with a separate backend. This is complex to deploy and maintain. A modernized stack should reduce boilerplate, improve developer experience, and support 3D rendering for slot games.

**Decision:** Use a single SvelteKit application (Svelte 5) backed by PocketBase (Go binary) for authentication and database. SvelteKit handles both frontend and server endpoints, eliminating the Flask API layer. PocketBase runs as a sidecar process.

**Consequences:**
- Positive: Single framework for client and server code
- Positive: PocketBase provides auth, real-time, and admin UI out of the box
- Positive: SvelteKit's file-based routing maps naturally to game pages
- Negative: PocketBase is not as scalable as Supabase for production
- Negative: Go binary must be distributed alongside the app

**Alternatives:**
- Flask + React: Existing stack, more moving parts
- Next.js + Supabase: Similar architecture but heavier dependency
