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
    Brain,
  } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  import SelectField from '$lib/SelectField.svelte';
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
  let fsrs = $state(false), deck = $state('');
  const icons = [Palette, BookOpen, Pencil, RefreshCw, Archive, Layers, FlaskConical];
  const current = $derived(pages.find((p) => p.id === active));
  async function request(action: string, extra = {}) {
    error = '';
    try {
      const data = await new Promise<{ pages: Page[]; dark: boolean; fsrs: boolean; deck: string } | null>((resolve) =>
        window.pycmd('prefs:' + JSON.stringify({ action, ...extra }), resolve),
      );
      if (data) {
        pages = data.pages;
        fsrs = data.fsrs;
        deck = data.deck;
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
  const draftVersions = new Map<string, number>();
  function stage(id: string, value: string | number, normalize = false) {
    const version = (draftVersions.get(id) || 0) + 1;
    draftVersions.set(id, version);
    const findItem = () =>
      pages.flatMap((p) => p.groups.flatMap((g) => g.items)).find((item) => item.id === id);
    const item = findItem();
    if (item) item.value = value;
    window.pycmd('prefs:' + JSON.stringify({ action: 'edit', id, value }), (result) => {
      if (draftVersions.get(id) !== version || result?.id !== id) return;
      const current = findItem();
      // Native spinboxes clamp intermediate digits (6 while entering 60).
      // Keep that draft while typing, then normalize when focus leaves.
      if (current?.type === 'number' && !normalize && document.activeElement?.id === id) return;
      if (current) current.value = result.value;
    });
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
      <button class:active={active === 'algorithm'} onclick={() => { active = 'algorithm'; search = ''; }}><Brain size={17} /><span>复习算法</span></button>
    </nav>
  </aside>
  <main class="preferences-main">
    <header>
      <span>学习空间</span><ChevronRight size={13} /><strong>{active === 'algorithm' ? '复习算法' : current?.title || '偏好设置'}</strong>
    </header>
    <div class="preferences-content">
      <div class="preferences-heading">
        <h1>{active === 'algorithm' ? '复习算法' : current?.title || '偏好设置'}</h1>

      </div>
      {#if active === 'algorithm'}
        <section class="preferences-card algorithm-card">
          <span class="algorithm-caption">当前算法</span>
          <h2>{fsrs ? 'FSRS' : 'SM-2 改进版'}</h2>
          <p>{fsrs ? '根据复习记录估计记忆状态，安排下一次复习。' : '根据评分、难度系数和上次间隔安排复习。'}</p>
          <div class="algorithm-location"><strong>算法开关在「牌组选项 → FSRS」</strong><p>开启 FSRS 使用记忆模型，关闭则使用传统算法。此开关对整个资料库生效；目标保留率等参数按牌组预设设置。</p></div>
          <p class="algorithm-caption">当前牌组：{deck}</p>
          <Button onclick={() => request('algorithm')}>打开牌组选项</Button>
        </section>
      {:else}
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
                    {:else if item.type === 'select'}<SelectField id={item.id} label={item.label} disabled={item.disabled} value={String(item.value)} options={(item.options||[]).map(option=>({value:String(option.value),label:option.label}))} onValueChange={value=>request('change',{id:item.id,value:Number(value)})}/>
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
                        onblur={(e) => {
                          if (
                            e.currentTarget.value !== '' &&
                            Number.isFinite(e.currentTarget.valueAsNumber)
                          )
                            stage(item.id, e.currentTarget.valueAsNumber, true);
                          else void request('load');
                        }}
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
      {/if}
    </div>
    <footer>
      <Button variant="ghost" onclick={() => request('help')}>帮助</Button><Button
        onclick={() => request('done')}>完成</Button
      >
    </footer>
  </main>
</div>
