<script lang="ts">
  import { onMount } from 'svelte';
  import {
    Layers,
    Cloud,
    CloudCheck,
    House,
    LayoutList,
    ChartNoAxesColumn,
    Settings2,
    Search,
    Plus,
    ChevronRight,
    Moon,
    Sun,
    BookOpen,
    ArrowRight,
    Check,
    MoreHorizontal,
    RefreshCw,
    Download,
    Pencil,
    X,
  } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  import { Badge } from '$lib/components/ui/badge';
  import * as Sidebar from '$lib/components/ui/sidebar';
  import * as Table from '$lib/components/ui/table';
  import * as Tabs from '$lib/components/ui/tabs';
  import * as Menu from '$lib/components/ui/dropdown-menu';
  import NavButton from '$lib/NavButton.svelte';
  import DeckIcon from '$lib/DeckIcon.svelte';
  import SelectField from '$lib/SelectField.svelte';
  import { command, type Home, type Card } from '$lib/bridge';
  let home: Home = $state({
    decks: [],
    new: 0,
    learning: 0,
    review: 0,
    completed: 0,
    studiedToday: '',
    activity: [],
    total: 0,
    dark: false,
    profile: '',
    page: 'home',
  });
  let page = $state('home'),
    query = $state(''),
    deckId = $state('all'),
    filter = $state('all'),
    selectedId = $state(''),
    error = $state('');
  let cards: Card[] = $state([]),
    total = $state(0),
    busy = $state(true),
    ready = $state(false);
  let revision = 0;
  const selected = $derived(cards.find((c) => c.id === selectedId));
  const due = $derived(home.new + home.learning + home.review);
  let chosenDeckId = $state('');
  let syncOpen = $state(false);
  let syncStatus = $state({mediaActive:false,mediaMessage:'',collectionComplete:false});
  async function readSyncStatus() {
    try { syncStatus = await command<typeof syncStatus>('sync-status'); } catch { /* Retain the last known state while native operations run. */ }
  }
  onMount(() => {
    void readSyncStatus();
    const timer = setInterval(() => { if (!document.hidden) void readSyncStatus(); }, 2000);
    return () => clearInterval(timer);
  });
  const currentDeck = $derived(
    home.decks.find((deck) => deck.id === (chosenDeckId || home.currentDeckId)) || home.decks[0],
  );
  const currentDue = $derived(
    currentDeck ? currentDeck.new + currentDeck.learning + currentDeck.review : 0,
  );
  async function act(action: string, args = {}) {
    error = '';
    try {
      await command(action, args);
      if (action === 'theme') await refresh();
    } catch (e) {
      error = String(e instanceof Error ? e.message : e);
    }
  }
  async function refresh(navigate = false) {
    try {
      home = await command<Home>('home', { navigate });
      document.documentElement.classList.toggle('dark', home.dark);
    } catch (e) {
      error = String(e);
    } finally {
      busy = false;
    }
  }
  onMount(async () => {
    await refresh();
    page = home.page;
    if (page === 'cards' && home.cardFilters) {
      query = home.cardFilters.query;
      deckId = home.cardFilters.deckId;
      filter = home.cardFilters.state;
    }
    ready = true;
  });
  $effect(() => {
    if (!ready || page !== 'cards') return;
    const args = { query, deckId, state: filter };
    const current = ++revision;
    const timer = setTimeout(async () => {
      busy = true;
      error = '';
      try {
        const result = await command<{ cards: Card[]; total: number }>('cards', args);
        if (revision !== current) return;
        cards = result.cards;
        total = result.total;
        if (!cards.some((c) => c.id === selectedId)) selectedId = cards[0]?.id || '';
      } catch (e) {
        if (revision === current) error = String(e);
      } finally {
        if (revision === current) busy = false;
      }
    }, 250);
    return () => {
      clearTimeout(timer);
      revision++;
    };
  });
  $effect(() => {
    if (page !== 'overview') return;
    const timer = setInterval(() => {
      void refresh();
    }, 60000);
    return () => clearInterval(timer);
  });
  function browse(id = 'all') {
    deckId = id;
    query = '';
    page = 'cards';
  }
  function keydown(e: KeyboardEvent) {
    if (
      page === 'overview' &&
      home.overview &&
      !home.overview.finished &&
      !e.metaKey &&
      !e.ctrlKey &&
      !e.altKey &&
      (e.key === ' ' || e.key === 'Enter') &&
      !(e.target instanceof HTMLElement && e.target.closest('button,input,select,textarea,a'))
    ) {
      e.preventDefault();
      void act('overview-action', { command: 'study' });
      return;
    }
    if (!(e.metaKey || e.ctrlKey)) return;
    if (e.key.toLowerCase() === 'k') {
      e.preventDefault();
      browse();
      setTimeout(() => document.getElementById('card-search')?.focus(), 0);
    }
    if (e.key === '2') {
      e.preventDefault();
      browse();
    }
    if (e.key === ',') {
      e.preventDefault();
      void act('settings');
    }
    if (e.key.toLowerCase() === 'n') {
      e.preventDefault();
      void act('add');
    }
  }
</script>

<svelte:window onkeydown={keydown} />
<Sidebar.Provider class={page === 'home' ? 'native-split-home' : ''} style="--sidebar-width:13rem">
  <Sidebar.Root collapsible="offcanvas" class="app-sidebar">
    <Sidebar.Header class="brand-header"
      ><a
        href="#home"
        class="brand-link"
        onclick={(e) => {
          e.preventDefault();
          page = 'home';
          void refresh(true);
        }}
        ><span class="brand-symbol"><Layers size={23} /></span><span class="brand-word"
          >Anki</span
        ></a
      ></Sidebar.Header
    >
    <Sidebar.Content
      >{#if page !== 'home'}<Sidebar.Group class="sidebar-navigation"
        ><Sidebar.GroupContent
          ><Sidebar.Menu>
            <Sidebar.MenuItem
              ><NavButton
                isActive={page === 'home'}
                onclick={() => {
                  page = 'home';
                  void refresh(true);
                }}
                class="main-nav-button"
                ><House /><span>今日学习</span>{#if page !== 'home'}<span class="nav-count"
                    >{due}</span
                  >{/if}</NavButton
              ></Sidebar.MenuItem
            >
            <Sidebar.MenuItem
              ><NavButton
                isActive={page === 'cards' && deckId === 'all'}
                onclick={() => browse()}
                class="main-nav-button"
                ><LayoutList /><span>卡片管理</span><span class="nav-shortcut">⌘ 2</span></NavButton
              ></Sidebar.MenuItem
            >
            <Sidebar.MenuItem
              ><NavButton onclick={() => act('stats')} class="main-nav-button"
                ><ChartNoAxesColumn /><span>学习统计</span></NavButton
              ></Sidebar.MenuItem
            >
          </Sidebar.Menu></Sidebar.GroupContent
        ></Sidebar.Group
      >
      {/if}<Sidebar.Group class="sidebar-deck-group"
          ><Sidebar.GroupLabel class="sidebar-group-heading"
            >我的牌组<button class="sidebar-add" aria-label="新建牌组" onclick={() => act('create')}
              ><Plus size={14} /></button
            ></Sidebar.GroupLabel
          ><Sidebar.GroupContent
            ><Sidebar.Menu
              >{#each home.decks as deck}<Sidebar.MenuItem
                  ><NavButton
                    isActive={(page === 'home' && currentDeck?.id === deck.id) || (page === 'cards' && deckId === deck.id) ||
                      (page === 'overview' && home.overview?.id === deck.id)}
                    onclick={() => page === 'home' ? (chosenDeckId = deck.id) : browse(deck.id)}
                    class="deck-nav-button"
                    ><DeckIcon {deck} small /><span>{deck.name}</span>{#if page === 'home'}<span class="split-nav-count">{deck.new + deck.learning + deck.review || '—'}</span>{/if}</NavButton
                  ></Sidebar.MenuItem
                >{/each}</Sidebar.Menu
            ></Sidebar.GroupContent
          ></Sidebar.Group
        >
      </Sidebar.Content
    >
    <Sidebar.Footer class="app-sidebar-footer"
      ><Sidebar.Menu
        >{#if page === 'home'}<Sidebar.MenuItem><NavButton class="settings-nav" onclick={() => act('stats')}><ChartNoAxesColumn/><span>学习统计</span></NavButton></Sidebar.MenuItem>{/if}<Sidebar.MenuItem
          ><NavButton onclick={() => act('settings')} class="settings-nav"
            ><Settings2 /><span>偏好设置</span><span class="ml-auto text-xs">⌘ ,</span></NavButton
          ></Sidebar.MenuItem
        ></Sidebar.Menu
      >
      <div class="workspace-profile">
        <span class="workspace-avatar"><BookOpen size={18} /></span><span
          ><strong>{home.profile || 'Anki'}</strong></span
        >
      </div></Sidebar.Footer
    >
  </Sidebar.Root>
  <main class="app-main">
    <header class="app-topbar">
      <div class="topbar-breadcrumb">
        <Sidebar.Trigger aria-label="切换侧边栏" /><span class="breadcrumb-root">学习空间</span
        ><ChevronRight size={13} /><strong
          >{page === 'home' ? '牌组' : page === 'overview' ? '牌组学习' : '卡片管理'}</strong
        >
      </div>
      <div class="topbar-actions">
        {#if page === 'home'}<Button variant="ghost" size="icon-sm" aria-label="添加卡片" onclick={() => act('add')}><Plus size={18}/></Button>{/if}
        <button
          class="quick-search-button"
          onclick={() => {
            browse();
            setTimeout(() => document.getElementById('card-search')?.focus(), 0);
          }}><Search size={14} /><span>搜索卡片</span><kbd>⌘ K</kbd></button
        ><Button variant="ghost" size="icon-sm" aria-label="切换深浅色" onclick={() => act('theme')}
          >{#if home.dark}<Sun size={17} />{:else}<Moon size={17} />{/if}</Button
        ><Button variant="ghost" class="sync-status-trigger" size="sm" aria-expanded={syncOpen} onclick={() => {syncOpen = !syncOpen; void readSyncStatus();}}
          >{#if syncStatus.mediaActive}<RefreshCw size={15} />同步中{:else if syncStatus.collectionComplete}<CloudCheck size={15} />最近已同步{:else}<Cloud size={15} />同步{/if}</Button
        >
      </div>
      {#if syncOpen}<section class="sync-status-panel" aria-label="同步状态">
        <div class="sync-status-heading"><strong>同步状态</strong><Button variant="ghost" size="icon-sm" aria-label="关闭同步状态" onclick={() => (syncOpen=false)}><X size={16}/></Button></div>
        <p aria-live="polite">{syncStatus.mediaActive ? syncStatus.mediaMessage || '正在同步媒体…' : syncStatus.collectionComplete ? '上次集合同步已完成，媒体状态可在详情中查看。' : '将卡片与学习记录同步到 AnkiWeb。'}</p>
        {#if syncStatus.collectionComplete && syncStatus.mediaActive}<p>集合已完成，媒体仍在同步。</p>{/if}
        <div class="sync-status-actions"><Button variant="ghost" size="sm" onclick={() => act('sync-log')}>媒体详情</Button><Button size="sm" onclick={() => {syncOpen=false;void act('sync');}}>立即同步</Button></div>
      </section>{/if}
    </header>
    {#if error}<div class="live-error" role="alert">
        {error}<button aria-label="关闭提示" onclick={() => (error = '')}><X size={16} /></button>
      </div>{/if}
    <div class="app-scroll" aria-busy={busy}>
      {#if page === 'overview' && home.overview}
        {@const deck = home.overview}
        <section class="page-content modern-overview">
          <div class="page-heading">
            <div>
              <div class="eyebrow"><BookOpen size={14} />我的牌组</div>
              <h1>{deck.name}</h1>
              <p>
                {deck.finished
                  ? '这一轮学习已完成，给记忆一点沉淀的时间。'
                  : '按自己的节奏，开始今天的专注。'}
              </p>
            </div>
            <Button variant="outline" onclick={() => act('overview-action', { command: 'opts' })}
              ><Settings2 size={15} />牌组选项</Button
            >
          </div>
          <section class="overview-focus-panel">
            <span class="overview-emblem"
              >{#if deck.finished}<Check size={30} />{:else}<Layers size={30} />{/if}</span
            ><Badge variant="secondary">{deck.finished ? '本轮已完成' : '准备开始'}</Badge>
            <h2>{deck.finished ? '每一次回忆，都有收获。' : '把熟悉，变成长久的记忆。'}</h2>
            <div class="overview-count-grid">
              <div>
                <strong>{deck.new}</strong><span><i class="status-dot new"></i>未学习</span>
              </div>
              <div>
                <strong>{deck.learning}</strong><span
                  ><i class="status-dot learning"></i>学习中</span
                >
              </div>
              <div>
                <strong>{deck.review}</strong><span><i class="status-dot review"></i>待复习</span>
              </div>
            </div>
            {#if !deck.finished}<Button
                size="lg"
                onclick={() => act('overview-action', { command: 'study' })}
                >开始学习<ArrowRight size={16} /></Button
              >
              <p class="overview-shortcut">空格或 Enter 开始学习</p>{:else}<Button
                size="lg"
                onclick={() => {
                  page = 'home';
                  void refresh(true);
                }}>返回今日学习<ArrowRight size={16} /></Button
              >{/if}
            {#if deck.finished && deck.learnRemaining}<p class="overview-note">
                还有 {deck.learnRemaining} 张卡片待学习，下一张约在 {Math.max(
                  1,
                  Math.ceil(deck.nextLearnSeconds / 60),
                )} 分钟后到期。
              </p>{/if}
            {#if deck.finished && deck.newLimitReached}<p class="overview-note">
                已达到当前牌组的每日新卡片上限。
              </p>{/if}{#if deck.finished && deck.reviewLimitReached}<p class="overview-note">
                已达到当前牌组的每日复习上限。
              </p>{/if}
          </section>
          <div class="overview-tools">
            <Button variant="outline" onclick={() => browse(deck.id)}
              ><LayoutList size={15} />查看卡片</Button
            >{#if deck.filtered}<Button
                variant="outline"
                onclick={() => act('overview-action', { command: 'refresh' })}
                ><RefreshCw size={15} />重新构建</Button
              ><Button
                variant="outline"
                onclick={() => act('overview-action', { command: 'empty' })}>清空筛选牌组</Button
              >{:else}<Button
                variant="outline"
                onclick={() => act('overview-action', { command: 'studymore' })}
                ><Plus size={15} />自定义学习</Button
              ><Button
                variant="ghost"
                onclick={() => act('overview-action', { command: 'description' })}
                ><Pencil size={15} />编辑描述</Button
              >{/if}{#if deck.buried}<Button
                variant="outline"
                onclick={() => act('overview-action', { command: 'unbury' })}>取消搁置</Button
              >{/if}{#if deck.shared}<Button
                variant="ghost"
                onclick={() => act('overview-action', { command: 'review' })}
                >查看共享牌组更新</Button
              >{/if}
          </div>
          {#if deck.description.trim()}<section class="overview-description">
              <h2>牌组描述</h2>
              <p>{deck.description}</p>
            </section>{/if}
        </section>
      {:else if page === 'home'}
        <section class="home-page native-split-page page-content">
          {#if currentDeck}
          <label class="split-mobile-picker"><span>当前牌组</span><SelectField label="选择牌组" value={currentDeck.id} options={home.decks.map(deck=>({value:deck.id,label:deck.name}))} onValueChange={value=>(chosenDeckId=value)}/></label>
          <div class="split-focus">
            <span class="split-deck-emblem"><BookOpen size={28}/></span>
            <p class="split-caption">当前牌组</p>
            <h1>{currentDeck.name}</h1>
            <p class="split-total">共 {currentDeck.total ?? 0} 张卡片</p>
            <div class="split-counts" aria-label="待学数量">
              <div><strong>{currentDeck.new}</strong><span>未学习</span></div>
              <div><strong>{currentDeck.learning}</strong><span>学习中</span></div>
              <div><strong>{currentDeck.review}</strong><span>待复习</span></div>
            </div>
            <Button class="split-study-action" size="lg" disabled={busy} onclick={() => currentDue ? act('begin-study',{deckId:currentDeck.id}) : browse(currentDeck.id)}>{currentDue ? '开始学习' : '浏览卡片'}<ArrowRight size={17}/></Button>
            <div class="split-secondary-actions"><Button variant="ghost" size="sm" onclick={() => act('options',{deckId:currentDeck.id})}>牌组选项</Button><Button variant="ghost" size="sm" onclick={() => browse(currentDeck.id)}>浏览卡片</Button></div>
          </div>
          {:else if busy}<p class="home-loading" role="status">正在读取牌组…</p>
          {:else}<div class="split-focus"><span class="split-deck-emblem"><BookOpen size={28}/></span><h1>还没有牌组</h1><p class="split-total">创建牌组，开始第一次学习。</p><Button onclick={() => act('create')}>新建牌组</Button><Button variant="ghost" onclick={() => act('import')}>导入</Button></div>{/if}
        </section>
      {:else}
        <section class="cards-page">
          <div class="cards-page-heading">
            <div>
              <h1>卡片管理</h1>
              <p>搜索、预览与管理卡片。</p>
            </div>
            <div class="flex gap-2">
              <Button variant="outline" onclick={() => act('browse')}>完整管理</Button><Button
                onclick={() => act('add')}><Plus size={16} />添加卡片</Button
              >
            </div>
          </div>
          <div class="cards-workspace">
            <section class="cards-list-pane">
              <div class="cards-search-row">
                <div class="search-field">
                  <Search size={16} /><Input
                    id="card-search"
                    aria-label="搜索卡片"
                    placeholder="搜索内容或使用 Anki 搜索语法…"
                    bind:value={query}
                  />
                </div>
              </div>
              <div class="list-filter-row">
                <Tabs.Root bind:value={filter}
                  ><Tabs.List
                    ><Tabs.Trigger value="all">全部</Tabs.Trigger><Tabs.Trigger value="review"
                      >待复习</Tabs.Trigger
                    ><Tabs.Trigger value="learning">学习中</Tabs.Trigger><Tabs.Trigger value="new"
                      >未学习</Tabs.Trigger
                    ></Tabs.List
                  ></Tabs.Root
                ><SelectField class="live-deck-filter" label="筛选牌组" bind:value={deckId} options={[{value:'all',label:'全部牌组'},...home.decks.map(deck=>({value:deck.id,label:deck.name}))]}/>

              </div>
              <div class="card-table-wrap">
                <Table.Root class="card-data-table"
                  ><Table.Header
                    ><Table.Row
                      ><Table.Head>卡片内容</Table.Head><Table.Head>类型</Table.Head></Table.Row
                    ></Table.Header
                  ><Table.Body
                    >{#each cards as card}<Table.Row
                        class={selectedId === card.id ? 'selected-card-row' : ''}
                        ><Table.Cell
                          ><button
                            class="card-row-button"
                            aria-pressed={selectedId === card.id}
                            onclick={() => (selectedId = card.id)}
                            ><span class="card-row-title">{card.front || '（媒体或空白字段）'}</span
                            ><span class="card-row-subtitle"
                              >{home.decks.find((d) => d.id === card.deckId)?.name ||
                                '牌组'}{card.suspended ? ' · 已暂停' : ''}</span
                            ></button
                          ></Table.Cell
                        ><Table.Cell><Badge variant="secondary">{card.type}</Badge></Table.Cell
                        ></Table.Row
                      >{/each}</Table.Body
                  ></Table.Root
                >{#if !cards.length && !busy}<div class="empty-state">
                    <Search size={28} />
                    <h3>没有找到卡片</h3>
                    <p>尝试其他关键词或筛选条件。</p>
                  </div>{/if}
              </div>
              <div class="live-list-footer">
                {busy
                  ? '正在搜索…'
                  : `共 ${total} 张卡片${total > 100 ? '，显示前 100 张，请搜索缩小范围' : ''}`}
              </div>
            </section>
            <section class="live-detail">
              {#if selected}<div class="section-heading">
                  <h2>卡片详情</h2>
                  <Button size="sm" onclick={() => act('edit', { id: selected.id })}
                    ><Pencil size={14} />编辑</Button
                  >
                </div>
                <p class="muted-text">{selected.type}</p>
                {#each selected.fields as field}<div class="live-field">
                    <h3>{field.name}</h3>
                    <div>{field.text || '（媒体或空白字段）'}</div>
                  </div>{/each}{#if selected.tags.length}<div class="flex flex-wrap gap-2">
                    {#each selected.tags as tag}<Badge variant="secondary">{tag}</Badge>{/each}
                  </div>{/if}
                <p class="live-detail-note">点“编辑”可修改全部字段、媒体与模板。</p>{:else}<div
                  class="empty-state"
                >
                  <BookOpen size={30} />
                  <p>选择一张卡片查看详情。</p>
                </div>{/if}
            </section>
          </div>
        </section>
      {/if}
    </div>
  </main></Sidebar.Provider
>
