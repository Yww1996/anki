<script lang="ts">
  import {
    Layers,
    ChevronRight,
    Plus,
    LayoutList,
    ChartNoAxesColumn,
    RefreshCw,
  } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button';
  const meta = JSON.parse(document.getElementById('app')!.dataset.meta || '{}');
  const doc = new DOMParser().parseFromString(meta.links || '', 'text/html');
  const links = Array.from(doc.querySelectorAll('.toolbar a'))
    .map((a) => ({
      label: a.textContent?.trim() || '',
      command: a.getAttribute('onclick')?.match(/pycmd\(['"]([^'"]+)['"]\)/)?.[1] || '',
      id: a.id,
      title: a.getAttribute('title') || '',
    }))
    .filter((a) => a.command);
  let syncState = $state(0);
  Object.assign(window, { updateSyncColor: (required: number) => (syncState = required) });
</script>

<div class="review-header">
  {#if doc.querySelector('.left-tray')?.innerHTML}<div class="review-extension">
      {@html doc.querySelector('.left-tray')!.innerHTML}
    </div>{/if}<Button variant="ghost" class="review-brand" onclick={() => window.pycmd('decks')}
    ><span class="review-brand-icon"><Layers size={19} /></span>Anki</Button
  >
  <div class="review-breadcrumb"><ChevronRight size={13} /><span>专注学习</span></div>
  <nav aria-label="学习导航">
    {#each links as link}<Button
        variant={link.id === 'sync' ? 'outline' : 'ghost'}
        size="sm"
        id={link.id || undefined}
        title={link.title}
        onclick={() => window.pycmd(link.command)}
        >{#if link.id === 'add'}<Plus size={15} />{:else if link.id === 'browse'}<LayoutList
            size={15}
          />{:else if link.id === 'stats'}<ChartNoAxesColumn
            size={15}
          />{:else if link.id === 'sync'}<RefreshCw
            id="sync-spinner"
            size={15}
          />{/if}{link.label}{#if link.id === 'sync' && syncState > 0}<span class="tiny-dot"
          ></span>{/if}</Button
      >{/each}
  </nav>
  {#if doc.querySelector('.right-tray')?.innerHTML}<div class="review-extension">
      {@html doc.querySelector('.right-tray')!.innerHTML}
    </div>{/if}
</div>
