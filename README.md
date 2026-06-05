# ImperioCasino

Multi-game online casino. Blackjack, Roulette, 3D Slots (Threlte/Three.js). SvelteKit + PocketBase.

## Architecture

```
ImperioCasino/
├── src/
│   ├── routes/           # SvelteKit pages
│   │   ├── blackjack/    # Blackjack game
│   │   ├── roulette/     # Roulette game
│   │   ├── slots/        # 3D slot machine (Threlte)
│   │   ├── login/        # Auth
│   │   ├── signup/       # Registration
│   │   └── logout/       # Logout
│   ├── lib/
│   │   ├── components/   # Shared UI components
│   │   ├── server/       # PocketBase client, server utils
│   │   └── types.ts      # Shared types
│   └── app.html
├── pocketbase/           # PocketBase binary + data
├── scripts/              # Setup scripts
└── package.json          # pnpm workspace
```

Single SvelteKit app with PocketBase backend. No separate Flask server.

## Quick Start

```bash
pnpm install
pnpm run pb     # Start PocketBase on :8090
pnpm run dev    # Start SvelteKit on :5173
```

## Requirements

- Node.js 20+
- pnpm 9+
- PocketBase (bundled via `scripts/setup.sh`)

## Stack

| Layer | Tech |
|-------|------|
| Frontend | SvelteKit, Svelte 5 |
| 3D | Threlte, Three.js |
| Backend | PocketBase |
| Auth | PocketBase auth |
| Build | Vite |
| Test | Vitest, Testing Library |

## Scripts

```bash
pnpm run dev        # Dev server
pnpm run build      # Production build
pnpm run check      # Type check
pnpm run test       # Run tests
pnpm run pb         # Start PocketBase
pnpm run setup      # Initial setup (PocketBase download)
```

## License

MIT
