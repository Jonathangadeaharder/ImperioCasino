<script lang="ts">
	import { page } from '$app/stores';
	let user = $derived($page.data.user);
</script>

<h1>Welcome{user ? `, ${user.username}` : ''}</h1>
<p class="subtitle">Choose your game</p>

<div class="games">
	<a href="/blackjack" class="card blackjack">
		<h2>♠ Blackjack</h2>
		<p>Beat the dealer. Hit, stand, double down, split.</p>
	</a>
	<a href="/roulette" class="card roulette">
		<h2>🔴 Roulette</h2>
		<p>Place your bets. Spin the wheel.</p>
	</a>
	<a href="/slots" class="card slots">
		<h2>🍒 Slots</h2>
		<p>3D slot machine. Match 3 to win big.</p>
	</a>
</div>

<style>
	h1 { text-align: center; margin-top: 3rem; color: #ffd700; font-size: 2rem; }
	.subtitle { text-align: center; color: #888; margin-bottom: 2rem; }
	.games { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; max-width: 960px; margin: 0 auto; }
	.card { display: block; padding: 2rem; border-radius: 12px; text-decoration: none; color: #e0e0e0; border: 1px solid #333; transition: transform 0.2s, border-color 0.2s; }
	.card:hover { transform: translateY(-4px); }
	.card h2 { margin: 0 0 0.5rem; }
	.card p { margin: 0; color: #888; font-size: 0.9rem; }
	.blackjack:hover { border-color: #4caf50; }
	.roulette:hover { border-color: #ff4444; }
	.slots:hover { border-color: #ffd700; }
</style>