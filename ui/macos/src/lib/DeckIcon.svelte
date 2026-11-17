<script lang="ts">
  import { Languages, BookOpen, Sparkles } from '@lucide/svelte';
  type Deck = { color: string; icon: string };
  let { deck, small = false }: { deck: Deck; small?: boolean } = $props();
</script>

<span class:small class="deck-icon {deck.color}">
  {#if deck.icon === 'languages'}<Languages
      size={small ? 15 : 21}
      strokeWidth={1.7}
    />{:else if deck.icon === 'book'}<BookOpen
      size={small ? 15 : 21}
      strokeWidth={1.7}
    />{:else}<Sparkles size={small ? 15 : 21} strokeWidth={1.7} />{/if}
</span>
