<script lang="ts">
	let { data } = $props();

	let coins = $state(data.coins);
	let bets = $state<{ numbers: string; odds: number; amt: number }[]>([]);
	let spinning = $state(false);
	let result = $state<{ winning_number: number; total_bet: number; total_win: number; new_coins: number } | null>(null);
	let error = $state<string | null>(null);

	const redNumbers = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36];

	const singleBets = Array.from({ length: 37 }, (_, i) => ({
		numbers: String(i),
		odds: 35,
		label: String(i),
		color: i === 0 ? '#4caf50' : redNumbers.includes(i) ? '#ff4444' : '#e0e0e0'
	}));

	const specialBets = [
		{ numbers: '1,2,3,4,5,6,7,8,9,10,11,12', odds: 2, label: '1-12' },
		{ numbers: '13,14,15,16,17,18,19,20,21,22,23,24', odds: 2, label: '13-24' },
		{ numbers: '25,26,27,28,29,30,31,32,33,34,35,36', odds: 2, label: '25-36' },
		{ numbers: '1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35', odds: 1, label: 'Odd' },
		{ numbers: '2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36', odds: 1, label: 'Even' },
		{ numbers: '1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18', odds: 1, label: '1-18' },
		{ numbers: '19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36', odds: 1, label: '19-36' },
		{ numbers: redNumbers.join(','), odds: 1, label: 'Red' },
		{
			numbers: Array.from({ length: 37 }, (_, i) => i)
				.filter(n => !redNumbers.includes(n) && n !== 0)
				.join(','),
			odds: 1,
			label: 'Black'
		},
	];

	function toggleBet(bet: { numbers: string; odds: number; label: string }) {
		const existing = bets.find(b => b.numbers === bet.numbers);
		if (existing) {
			bets = bets.filter(b => b.numbers !== bet.numbers);
		} else {
			bets = [...bets, { numbers: bet.numbers, odds: bet.odds, amt: 10 }];
		}
	}

	async function spin() {
		if (bets.length === 0) return;
		spinning = true;
		error = null;
		result = null;

		const res = await fetch('/roulette/spin', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ bets })
		});
		const d = await res.json();
		if (res.ok) {
			result = d;
			coins = d.new_coins;
			bets = [];
		} else {
			error = d.error;
		}
		spinning = false;
	}
</script>

<h1>Roulette</h1>
<p class="coins">Coins: {coins}</p>

<div class="layout">
	<div class="table">
		<h3>Numbers</h3>
		<div class="grid">
			{#each singleBets as bet}
				<button
					class="cell"
					style="background: {bet.color}"
					class:selected={bets.some(b => b.numbers === bet.numbers)}
					onclick={() => toggleBet(bet)}
				>
					{bet.label}
				</button>
			{/each}
		</div>
		<h3>Outside Bets</h3>
		<div class="special">
			{#each specialBets as bet}
				<button
					class:selected={bets.some(b => b.numbers === bet.numbers)}
					onclick={() => toggleBet(bet)}
				>
					{bet.label}
				</button>
			{/each}
		</div>
	</div>
	<div class="info">
		<p>Current bets: {bets.reduce((s, b) => s + b.amt, 0)}</p>
		<button onclick={spin} disabled={bets.length === 0 || spinning}>
			{spinning ? 'Spinning...' : 'Spin!'}
		</button>
		{#if error}<p class="error">{error}</p>{/if}
		{#if result}
			<div class="result">
				<h2>Result: {result.winning_number}</h2>
				<p class:win={result.total_win > 0} class:lose={result.total_win === 0}>
					{result.total_win > 0 ? `You won ${result.total_win} coins!` : 'No win this time.'}
				</p>
			</div>
		{/if}
	</div>
</div>

<style>
	h1 { text-align: center; color: #ffd700; }
	.coins { text-align: center; color: #a0a0c0; }
	.layout { display: flex; gap: 2rem; max-width: 800px; margin: 2rem auto; }
	.table { flex: 1; }
	.grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 2px; margin-bottom: 1rem; }
	.cell { padding: 0.5rem; border: 1px solid #333; border-radius: 2px; color: #fff; font-weight: 600; cursor: pointer; }
	.cell.selected { outline: 3px solid #ffd700; }
	.special { display: flex; flex-wrap: wrap; gap: 4px; }
	.special button { padding: 0.4rem 0.8rem; border: 1px solid #555; border-radius: 4px; background: #2a2a4e; color: #e0e0e0; cursor: pointer; }
	.special button.selected { background: #ffd700; color: #000; }
	.info { width: 200px; }
	.info button { width: 100%; padding: 0.6rem; background: #4caf50; color: #000; border: none; border-radius: 4px; font-weight: 600; cursor: pointer; }
	.info button:disabled { opacity: 0.5; }
	.error { color: #ff4444; }
	.result { margin-top: 1rem; }
	.result h2 { color: #ffd700; }
	.win { color: #4caf50; }
	.lose { color: #ff4444; }
</style>
