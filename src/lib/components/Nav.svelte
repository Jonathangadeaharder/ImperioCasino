<script lang="ts">
	import { page } from '$app/stores';
	import CoinBalance from './CoinBalance.svelte';
	let user = $derived($page.data.user);
</script>

<nav>
	<a href="/">ImperioCasino</a>
	<div class="links">
		<a href="/blackjack">Blackjack</a>
		<a href="/roulette">Roulette</a>
		<a href="/slots">Slots</a>
	</div>
	{#if user}
		<CoinBalance />
		<a href="/logout">Logout</a>
	{/if}
</nav>

<style>
	nav {
		display: flex;
		align-items: center;
		gap: 1.5rem;
		padding: 0.75rem 1.5rem;
		background: #1a1a2e;
		border-bottom: 1px solid #2a2a4e;
	}
	nav > a:first-child {
		font-weight: 700;
		font-size: 1.2rem;
		color: #ffd700;
		text-decoration: none;
	}
	.links { display: flex; gap: 1rem; flex: 1; }
	.links a { color: #a0a0c0; text-decoration: none; }
	.links a:hover { color: #fff; }
</style>
