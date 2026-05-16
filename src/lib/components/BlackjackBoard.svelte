<script lang="ts">
	import type { Card as CardType, BlackjackState } from '$lib/types';
	import CardComponent from './Card.svelte';

	let { gameState, onAction, playing }: {
		gameState: BlackjackState & { can_double_down?: boolean; can_split?: boolean };
		onAction: (action: string) => void;
		playing: boolean;
	} = $props();

	function handValue(hand: CardType[]): number {
		return hand.reduce((s, c) => s + c.value, 0);
	}
</script>

{#if gameState}
	<div class="board">
		<div class="hand dealer">
			<h3>Dealer ({gameState.dealer_value || '?'})</h3>
			<div class="cards">
				{#each gameState.dealer_hand as card, i}
					<CardComponent card={card} hidden={i === 1 && !gameState.game_over} />
				{/each}
			</div>
		</div>
		<div class="hand player">
			<h3>Your Hand ({handValue(gameState.player_hand)})</h3>
			<div class="cards">
				{#each gameState.player_hand as card}
					<CardComponent card={card} />
				{/each}
			</div>
		</div>
		{#if gameState.split && gameState.player_second_hand}
			<div class="hand player">
				<h3>Second Hand ({handValue(gameState.player_second_hand)})</h3>
				<div class="cards">
					{#each gameState.player_second_hand as card}
						<CardComponent card={card} />
					{/each}
				</div>
			</div>
		{/if}
		{#if playing && !gameState.game_over}
			<div class="actions">
				<button onclick={() => onAction('hit')}>Hit</button>
				<button onclick={() => onAction('stand')}>Stand</button>
				<button onclick={() => onAction('double')} disabled={!gameState.can_double_down}>Double</button>
				<button onclick={() => onAction('split')} disabled={!gameState.can_split}>Split</button>
			</div>
		{/if}
	</div>
{/if}

<style>
	.board { max-width: 600px; margin: 2rem auto; }
	.hand { margin-bottom: 1.5rem; }
	.hand h3 { color: #a0a0c0; margin-bottom: 0.5rem; }
	.cards { display: flex; flex-wrap: wrap; gap: 4px; }
	.actions { display: flex; gap: 0.5rem; margin-top: 1rem; }
	.actions button {
		padding: 0.6rem 1.2rem;
		border: 1px solid #555;
		border-radius: 4px;
		background: #2a2a4e;
		color: #e0e0e0;
		cursor: pointer;
		font-weight: 600;
	}
	.actions button:disabled { opacity: 0.4; cursor: not-allowed; }
	.actions button:hover:not(:disabled) { background: #3a3a5e; }
</style>
