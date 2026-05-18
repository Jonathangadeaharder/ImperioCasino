import { sveltekit } from '@sveltejs/kit/vite';
import { svelteTesting } from '@testing-library/svelte/vite';
import { defineConfig } from 'vitest/config';

export default defineConfig({
	plugins: [sveltekit(), svelteTesting()],
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}'],
		setupFiles: ['./vitest.setup.ts'],
		environment: 'jsdom',
		coverage: {
			provider: 'v8',
			reporter: ['text', 'html', 'clover'],
			thresholds: { branches: 80, lines: 80, functions: 90, statements: 90 },
			include: ['src/**/*.ts'],
			exclude: ['**/adapter.ts', '**/types.ts', '**/+layout.server.ts']
		}
	}
});
