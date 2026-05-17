// @vitest-environment jsdom
import { render, screen } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import BlackjackBoard from '../BlackjackBoard.svelte';
import type { BlackjackState } from '$lib/types';

function makeState(overrides: Partial<BlackjackState> = {}): BlackjackState {
	return {
		id: 'test',
		user_id: 'u1',
		deck: [],
		dealer_hand: [{ suit: 'Hearts', name: 'K', value: 10 }],
		player_hand: [
			{ suit: 'Spades', name: 'A', value: 11 },
			{ suit: 'Diamonds', name: '7', value: 7 }
		],
		player_second_hand: null,
		player_coins: 100,
		current_wager: 25,
		game_over: false,
		message: null,
		player_stood: false,
		double_down: false,
		split: false,
		current_hand: 'first',
		dealer_value: 10,
		...overrides
	};
}

describe('BlackjackBoard', () => {
	it('renders nothing when gameState is null', () => {
		const { container } = render(BlackjackBoard, {
			gameState: null,
			onAction: vi.fn(),
			playing: false
		});
		expect(container.textContent?.trim()).toBe('');
	});

	it('renders dealer and player hands', () => {
		const state = makeState();
		render(BlackjackBoard, { gameState: state, onAction: vi.fn(), playing: false });
		expect(screen.getByText(/Dealer/)).toBeInTheDocument();
		expect(screen.getByText(/Your Hand/)).toBeInTheDocument();
		expect(screen.getByText('A')).toBeInTheDocument();
		expect(screen.getByText('7')).toBeInTheDocument();
	});

	it('shows action buttons when playing and not game_over', () => {
		const state = makeState();
		render(BlackjackBoard, { gameState: state, onAction: vi.fn(), playing: true });
		expect(screen.getByRole('button', { name: 'Hit' })).toBeInTheDocument();
		expect(screen.getByRole('button', { name: 'Stand' })).toBeInTheDocument();
	});

	it('hides action buttons when game is over', () => {
		const state = makeState({ game_over: true });
		render(BlackjackBoard, { gameState: state, onAction: vi.fn(), playing: true });
		expect(screen.queryByRole('button', { name: 'Hit' })).not.toBeInTheDocument();
	});

	it('hides action buttons when not playing', () => {
		const state = makeState();
		render(BlackjackBoard, { gameState: state, onAction: vi.fn(), playing: false });
		expect(screen.queryByRole('button', { name: 'Hit' })).not.toBeInTheDocument();
	});

	it('disables double button when double_down is false', () => {
		const state = makeState({ double_down: false });
		render(BlackjackBoard, { gameState: state, onAction: vi.fn(), playing: true });
		expect(screen.getByRole('button', { name: 'Double' })).toBeDisabled();
	});

	it('enables double button when double_down is true', () => {
		const state = makeState({ double_down: true });
		render(BlackjackBoard, { gameState: state, onAction: vi.fn(), playing: true });
		expect(screen.getByRole('button', { name: 'Double' })).not.toBeDisabled();
	});

	it('disables split button when split is false', () => {
		const state = makeState({ split: false });
		render(BlackjackBoard, { gameState: state, onAction: vi.fn(), playing: true });
		expect(screen.getByRole('button', { name: 'Split' })).toBeDisabled();
	});

	it('calls onAction with correct action on button click', async () => {
		const onAction = vi.fn();
		const user = userEvent.setup();
		const state = makeState();
		render(BlackjackBoard, { gameState: state, onAction, playing: true });
		await user.click(screen.getByRole('button', { name: 'Hit' }));
		expect(onAction).toHaveBeenCalledWith('hit');
		await user.click(screen.getByRole('button', { name: 'Stand' }));
		expect(onAction).toHaveBeenCalledWith('stand');
	});

	it('shows second hand when split and player_second_hand exists', () => {
		const state = makeState({
			split: true,
			player_second_hand: [{ suit: 'Clubs', name: '5', value: 5 }]
		});
		render(BlackjackBoard, { gameState: state, onAction: vi.fn(), playing: true });
		expect(screen.getByText('Second Hand', { exact: false })).toBeInTheDocument();
		expect(screen.getByText('5')).toBeInTheDocument();
	});
});
