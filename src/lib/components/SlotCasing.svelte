<script lang="ts">
	import { T } from '@threlte/core';
</script>

<T.Mesh position={[0, -1.5, -2]}>
	<T.BoxGeometry args={[6, 4, 1.5]} />
	<T.MeshStandardMaterial color="#1a1a3e" metalness={0.6} roughness={0.2} />
</T.Mesh>
