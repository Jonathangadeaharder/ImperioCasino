// @vitest-environment jsdom
import { vi } from 'vitest';

// Mock @threlte/core before any imports
vi.mock('@threlte/core', () => {
	function createProxyComponent(tag: string) {
		return function ThrelteNode(
			{ children, ..._props }: { children?: any; [key: string]: any }
		) {
			return `<${tag}>${children ?? ''}</${tag}>`;
		};
	}

	const T = new Proxy(
		{},
		{
			get(_, tag: string) {
				return createProxyComponent(tag);
			}
		}
	);

	return {
		T,
		useTask: vi.fn()
	};
});

import { describe, it, expect } from 'vitest';

// Use dynamic imports to avoid Svelte compilation issues with Threlte
// These are smoke tests verifying components render without errors
describe('Threlte 3D Components', () => {
	it('Reel can be imported without error', async () => {
		const mod = await import('../Reel.svelte');
		expect(mod.default).toBeDefined();
	});

	it('SlotCasing can be imported without error', async () => {
		const mod = await import('../SlotCasing.svelte');
		expect(mod.default).toBeDefined();
	});

	it('SlotLights can be imported without error', async () => {
		const mod = await import('../SlotLights.svelte');
		expect(mod.default).toBeDefined();
	});

	it('SlotMachine can be imported without error', async () => {
		const mod = await import('../SlotMachine.svelte');
		expect(mod.default).toBeDefined();
	});
});
