import '@testing-library/jest-dom/vitest';
import { vi } from 'vitest';

vi.mock('$app/environment', () => ({
	browser: false,
	dev: true,
	prerender: false,
	building: false
}));

vi.mock('$app/stores', () => {
	const storeData: { value: Record<string, any> } = { value: {} };
	return {
		get page() {
			return {
				subscribe: vi.fn((cb: (v: any) => void) => {
					cb({ data: storeData.value, url: new URL('http://localhost:5173') });
					return () => {};
				}),
				get data() { return storeData.value; },
				set data(v) { storeData.value = v; }
			};
		}
	};
});

vi.mock('$env/dynamic/private', () => ({
	env: { POCKETBASE_URL: 'http://127.0.0.1:8090' }
}));

globalThis.fetch = vi.fn(() => {
	throw new Error('Network Request Blocked: Unit test attempted HTTP call');
});
