// @vitest-environment jsdom
import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import Card from '../Card.svelte';

describe('Card', () => {
	const card = { suit: 'Hearts' as const, name: 'A', value: 11 };

	it('renders card face when not hidden', () => {
		render(Card, { card });
		expect(screen.getByText('♥')).toBeInTheDocument();
		expect(screen.getByText('A')).toBeInTheDocument();
	});

	it('renders back when hidden', () => {
		render(Card, { card, hidden: true });
		expect(screen.getByText('?')).toBeInTheDocument();
		expect(screen.queryByText('♥')).not.toBeInTheDocument();
	});

	it('renders black suit color', () => {
		const club = { suit: 'Clubs' as const, name: 'K', value: 10 };
		render(Card, { card: club });
		expect(screen.getByText('♣')).toBeInTheDocument();
		expect(screen.getByText('K')).toBeInTheDocument();
	});
});
