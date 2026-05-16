<script lang="ts">
	import type { Card as CardType } from '$lib/types';
	let { card, hidden = false }: { card: CardType; hidden?: boolean } = $props();
</script>

<div class="card {hidden ? 'hidden' : ''}">
	{#if hidden}
		<span class="back">?</span>
	{:else}
		<span class="suit" style="color: {card.suit === 'Hearts' || card.suit === 'Diamonds' ? '#ff4444' : '#e0e0e0'}">
			{card.suit === 'Hearts' ? '♥' : card.suit === 'Diamonds' ? '♦' : card.suit === 'Clubs' ? '♣' : '♠'}
		</span>
		<span class="name">{card.name}</span>
	{/if}
</div>

<style>
	.card {
		display: inline-flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		width: 60px;
		height: 84px;
		border: 2px solid #555;
		border-radius: 8px;
		background: #1a1a2e;
		margin: 0 4px;
		font-size: 0.85rem;
	}
	.card.hidden { background: #2a1a4e; border-color: #6a3aae; }
	.back { font-size: 1.5rem; color: #6a3aae; }
	.suit { font-size: 1.2rem; }
	.name { font-weight: 600; font-size: 1rem; }
</style>
