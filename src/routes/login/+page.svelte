<script lang="ts">
	let { form } = $props();
</script>

<h1>Login</h1>
<form method="POST">
	{#if form?.error}<p class="error">{form.error}</p>{/if}
	<label>Email <input type="email" name="email" required /></label>
	<label>Password <input type="password" name="password" required /></label>
	<button type="submit">Login</button>
	<p><a href="/signup">Create account</a></p>
</form>

<style>
	h1 { text-align: center; margin-top: 3rem; color: #ffd700; }
	form { max-width: 320px; margin: 2rem auto; display: flex; flex-direction: column; gap: 1rem; }
	label { display: flex; flex-direction: column; gap: 0.25rem; color: #a0a0c0; }
	input { padding: 0.5rem; border: 1px solid #333; border-radius: 4px; background: #1a1a2e; color: #e0e0e0; }
	button { padding: 0.6rem; background: #ffd700; color: #000; border: none; border-radius: 4px; font-weight: 600; cursor: pointer; }
	.error { color: #ff4444; text-align: center; }
	a { color: #88aaff; }
</style>
