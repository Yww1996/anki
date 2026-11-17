<script lang="ts">
  import { onMount } from 'svelte';
  import {
    Settings2,
    Palette,
    BookOpen,
    Pencil,
    RefreshCw,
    Archive,
    FlaskConical,
    Layers,
    ChevronRight,
    Search,
  } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  import { Switch } from '$lib/components/ui/switch';
  interface Item {
    id: string;
    type: string;
    label: string;
    value?: string | number | boolean;
    disabled?: boolean;
    hidden?: boolean;
    hint?: string;
    options?: { label: string; value: number }[];
    min?: number;
    max?: number;
    step?: number;
    suffix?: string;
    placeholder?: string;
  }
  interface Page {
    id: string;
    title: string;
    groups: { title: string; items: Item[] }[];
    labs: boolean;
  }
  let pages: Page[] = $state([]),
    active = $state('0'),
    search = $state(''),
    error = $state('');
  const icons = [Palette, BookOpen, Pencil, RefreshCw, Archive, Layers, FlaskConical];
  const current = $derived(pages.find((p) => p.id === active));
  async function request(action: string, extra = {}) {
    error = '';
    try {
      const data = await new Promise<{ pages: Page[]; dark: boolean } | null>((resolve) =>
        window.pycmd('prefs:' + JSON.stringify({ action, ...extra }), resolve),
      );
      if (data) {
        pages = data.pages;
        document.documentElement.classList.toggle('dark', data.dark);
      }
    } catch (e) {
      error = String(e);
    }
  }
  onMount(async () => {
    for (let i = 0; !window.pycmd && i < 250; i++) await new Promise((r) => setTimeout(r, 20));
    await request('load');
  });
  function stage(id: string, value: string | number) {
    window.pycmd('prefs:' + JSON.stringify({ action: 'edit', id, value }));
  }
  function match(item: Item) {
    return (
      !item.hidden &&
      (!search || `${item.label} ${item.hint || ''}`.toLowerCase().includes(search.toLowerCase()))
    );
  }
</script>

<svelte:window onfocus={() => request('load')} />
<div class="preferences-shell">
  <aside class="preferences-nav">
    <div class="preferences-brand"><Settings2 size={22} /><span>偏好设置</span></div>
    <nav aria-label="设置分类">
      {#each pages as page, i}{@const Icon = icons[i] || Settings2}<button
          class:active={active === page.id}
          onclick={() => {
            active = page.id;
            search = '';
          }}><Icon size={17} /><span>{page.title}</span></button
        >{/each}
    </nav>
    <p>让学习空间，<br />更合你的习惯。</p>
  </aside>
  <main class="preferences-main">
    <header>
      <span>学习空间</span><ChevronRight size={13} /><strong>{current?.title || '偏好设置'}</strong>
    </header>
    <div class="preferences-content">
      <div class="preferences-heading">
        <h1>{current?.title || '偏好设置'}</h1>
        <p>调整习惯，让每一次学习更顺手。</p>
      </div>
      <div class="preferences-search">
        <Search size={15} /><Input
          aria-label="搜索当前分类设置"
          placeholder="搜索当前分类…"
          bind:value={search}
        />
      </div>
      {#if error}<p role="alert">{error}</p>{/if}
      {#if current?.labs}<section class="preferences-card">
          <h2>实验功能</h2>
          <p class="preferences-explanation">查看 Anki 的实验功能和原始说明。</p>
          <Button variant="outline" onclick={() => request('labs')}>打开实验功能</Button>
        </section>{/if}
      {#each current?.groups || [] as group}{#if group.items.some(match)}<section
            class="preferences-card"
          >
            {#if group.title}<h2>
                {group.title}
              </h2>{/if}{#each group.items.filter(match) as item (item.id)}
              {#if item.type === 'info'}<p class="preferences-explanation">{item.label}</p>
              {:else}<div class="preferences-row" class:stacked={item.type === 'text'}>
                  <div class="preferences-row-label">
                    <label for={item.id}>{item.label}</label>{#if item.hint}<p>{item.hint}</p>{/if}
                  </div>
                  <div class="preferences-row-control">
                    {#if item.type === 'switch'}<Switch
                        id={item.id}
                        aria-label={item.label}
                        checked={Boolean(item.value)}
                        disabled={item.disabled}
                        onCheckedChange={(value) => request('change', { id: item.id, value })}
                      />
                    {:else if item.type === 'select'}<select
                        id={item.id}
                        aria-label={item.label}
                        disabled={item.disabled}
                        value={Number(item.value)}
                        onchange={(e) =>
                          request('change', { id: item.id, value: Number(e.currentTarget.value) })}
                        >{#each item.options || [] as option}<option value={option.value}
                            >{option.label}</option
                          >{/each}</select
                      >
                    {:else if item.type === 'number'}<Input
                        id={item.id}
                        aria-label={item.label}
                        type="number"
                        value={Number(item.value)}
                        min={item.min}
                        max={item.max}
                        step={item.step}
                        disabled={item.disabled}
                        class="preferences-number"
                        oninput={(e) => {
                          if (
                            e.currentTarget.value !== '' &&
                            Number.isFinite(e.currentTarget.valueAsNumber)
                          )
                            stage(item.id, e.currentTarget.valueAsNumber);
                        }}
                      />{#if item.suffix}<span class="preferences-suffix">{item.suffix}</span>{/if}
                    {:else if item.type === 'text'}<Input
                        id={item.id}
                        aria-label={item.label}
                        value={String(item.value)}
                        placeholder={item.placeholder}
                        disabled={item.disabled}
                        oninput={(e) => stage(item.id, e.currentTarget.value)}
                      />
                    {:else if item.type === 'button'}<Button
                        id={item.id}
                        variant="outline"
                        size="sm"
                        disabled={item.disabled}
                        onclick={() => request('button', { id: item.id })}>{item.label}</Button
                      >{/if}
                  </div>
                </div>{/if}{/each}
          </section>{/if}{/each}
    </div>
    <footer>
      <Button variant="ghost" onclick={() => request('help')}>帮助</Button><Button
        onclick={() => request('done')}>完成</Button
      >
    </footer>
  </main>
</div>
