<script lang="ts">
	import { T, useTask } from '@threlte/core';

	let { reelIndex, spinning }: { reelIndex: number; spinning: boolean } = $props();

	let mesh: any = $state(null);

	useTask((delta) => {
		if (!mesh) return;
		if (spinning) {
			mesh.rotation.x += delta * 8;
		}
	});
</script>

<T.Mesh position={[-1.5 + reelIndex * 1.5, 0.5, 0.5]} bind:ref={mesh}>
	<T.CylinderGeometry args={[0.6, 0.6, 0.1, 8]} />
	<T.MeshStandardMaterial color="#222" />
</T.Mesh>
