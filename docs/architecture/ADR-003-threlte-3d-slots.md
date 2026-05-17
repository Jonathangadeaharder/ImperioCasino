# ADR-003: Threlte for 3D Slot Engine

**Status:** Accepted

**Context:** The slot game requires 3D rendering with animated reel spins, particle effects, and immersive visuals. The solution must integrate natively with Svelte's reactive system.

**Decision:** Use Threlte (Svelte-native Three.js bindings) for the 3D slot engine. Threlte provides reactive Svelte components that map directly to Three.js objects, enabling declarative 3D scene composition within Svelte templates.

**Consequences:**
- Positive: Native Svelte reactivity for 3D scene properties
- Positive: Svelte component model maps naturally to 3D object hierarchy
- Positive: No imperative Three.js code for scene setup
- Negative: Threlte has a smaller community than raw Three.js
- Negative: Bundle size increases significantly with Three.js

**Alternatives:**
- Raw Three.js: More flexible but imperative, no Svelte integration
- CSS 3D transforms: Limited to simple effects, no complex rendering
- Canvas 2D: Not suitable for immersive slot visuals
