<script lang="ts">
import { page } from "$app/stores";

let _coins = $derived($page.data.user?.coins ?? 0);
</script>

<span class="coins">🪙 {_coins}</span>

<style>
	.coins {
		font-weight: 600;
		color: #ffd700;
	}
</style>
