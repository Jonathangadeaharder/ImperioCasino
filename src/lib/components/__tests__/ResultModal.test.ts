// @vitest-environment jsdom
import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import ResultModal from '../ResultModal.svelte';

describe('ResultModal', () => {
	it('renders nothing when show is false', () => {
		const { container } = render(ResultModal, { show: false, message: null, payout: 0 });
		expect(container.textContent?.trim()).toBe('');
	});

	it('renders win message when payout > 0', () => {
		render(ResultModal, { show: true, message: 'You win!', payout: 50 });
		expect(screen.getByText('You win!')).toBeInTheDocument();
		expect(screen.getByText('You won 50 coins!')).toBeInTheDocument();
	});

	it('renders lose message when payout is 0', () => {
		render(ResultModal, { show: true, message: 'You lose', payout: 0 });
		expect(screen.getByText('You lose')).toBeInTheDocument();
		expect(screen.getByText('Better luck next time.')).toBeInTheDocument();
	});

	it('renders Play Again link', () => {
		render(ResultModal, { show: true, message: 'You win!', payout: 50 });
		const link = screen.getByRole('link', { name: 'Play Again' });
		expect(link).toBeInTheDocument();
		expect(link).toHaveAttribute('href', '/blackjack');
	});
});
