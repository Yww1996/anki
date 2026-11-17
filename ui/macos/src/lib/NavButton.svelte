<script lang="ts">
  import { tick, type Snippet } from 'svelte';
  import { MenuButton } from '$lib/components/ui/sidebar';
  import { useSidebar } from '$lib/components/ui/sidebar/context.svelte.js';
  let {
    isActive = false,
    class: className,
    onclick,
    children,
  }: { isActive?: boolean; class?: string; onclick: () => void; children?: Snippet } = $props();
  const sidebar = useSidebar();
  async function activate() {
    if (sidebar.isMobile) {
      sidebar.setOpenMobile(false);
      await tick();
    }
    onclick();
  }
</script>

<MenuButton {isActive} class={className} onclick={activate}>{@render children?.()}</MenuButton>
