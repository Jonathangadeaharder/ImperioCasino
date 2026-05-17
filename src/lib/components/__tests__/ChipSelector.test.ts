// @vitest-environment jsdom
import { render, screen } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import ChipSelector from '../ChipSelector.svelte';

describe('ChipSelector', () => {
	it('renders all chip values', () => {
		render(ChipSelector, { wager: 0, setWager: vi.fn(), max: 100 });
		expect(screen.getByRole('button', { name: '10' })).toBeInTheDocument();
		expect(screen.getByRole('button', { name: '25' })).toBeInTheDocument();
		expect(screen.getByRole('button', { name: '50' })).toBeInTheDocument();
		expect(screen.getByRole('button', { name: '100' })).toBeInTheDocument();
	});

	it('calls setWager when chip clicked', async () => {
		const setWager = vi.fn();
		const user = userEvent.setup();
		render(ChipSelector, { wager: 0, setWager, max: 100 });
		await user.click(screen.getByRole('button', { name: '25' }));
		expect(setWager).toHaveBeenCalledWith(25);
	});

	it('disables buttons when chip > max', () => {
		render(ChipSelector, { wager: 0, setWager: vi.fn(), max: 30 });
		expect(screen.getByRole('button', { name: '10' })).not.toBeDisabled();
		expect(screen.getByRole('button', { name: '25' })).not.toBeDisabled();
		expect(screen.getByRole('button', { name: '50' })).toBeDisabled();
		expect(screen.getByRole('button', { name: '100' })).toBeDisabled();
	});

	it('disables all buttons when disabled prop is true', () => {
		render(ChipSelector, { wager: 0, setWager: vi.fn(), max: 100, disabled: true });
		const buttons = screen.getAllByRole('button');
		buttons.forEach((btn) => expect(btn).toBeDisabled());
	});
});
