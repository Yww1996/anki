<script lang="ts">
  import { onMount } from 'svelte';
  import {
    Layers,
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
    CalendarDays,
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
  const today = new Intl.DateTimeFormat('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  }).format(new Date());
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
<Sidebar.Provider style="--sidebar-width:15rem">
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
          >Anki<span class="brand-suffix">学习空间</span></span
        ></a
      ></Sidebar.Header
    >
    <Sidebar.Content
      ><Sidebar.Group class="sidebar-navigation"
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
                ><House /><span>今日学习</span><span class="nav-count">{due}</span></NavButton
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
      <Sidebar.Group class="sidebar-deck-group"
        ><Sidebar.GroupLabel class="sidebar-group-heading"
          >我的牌组<button class="sidebar-add" aria-label="新建牌组" onclick={() => act('create')}
            ><Plus size={14} /></button
          ></Sidebar.GroupLabel
        ><Sidebar.GroupContent
          ><Sidebar.Menu
            >{#each home.decks as deck}<Sidebar.MenuItem
                ><NavButton
                  isActive={(page === 'cards' && deckId === deck.id) ||
                    (page === 'overview' && home.overview?.id === deck.id)}
                  onclick={() => browse(deck.id)}
                  class="deck-nav-button"
                  ><DeckIcon {deck} small /><span>{deck.name}</span></NavButton
                ></Sidebar.MenuItem
              >{/each}</Sidebar.Menu
          ></Sidebar.GroupContent
        ></Sidebar.Group
      >
      <div class="sidebar-tip"><p>每天留一点时间，<br />给值得记住的事。</p></div></Sidebar.Content
    >
    <Sidebar.Footer class="app-sidebar-footer"
      ><Sidebar.Menu
        ><Sidebar.MenuItem
          ><NavButton onclick={() => act('settings')} class="settings-nav"
            ><Settings2 /><span>偏好设置</span><span class="ml-auto text-xs">⌘ ,</span></NavButton
          ></Sidebar.MenuItem
        ></Sidebar.Menu
      >
      <div class="workspace-profile">
        <span class="workspace-avatar"><BookOpen size={18} /></span><span
          ><strong>{home.profile || 'Anki'}</strong><small>本机资料库</small></span
        >
      </div></Sidebar.Footer
    >
  </Sidebar.Root>
  <main class="app-main">
    <header class="app-topbar">
      <div class="topbar-breadcrumb">
        <Sidebar.Trigger aria-label="切换侧边栏" /><span class="breadcrumb-root">学习空间</span
        ><ChevronRight size={13} /><strong
          >{page === 'home' ? '今日学习' : page === 'overview' ? '牌组学习' : '卡片管理'}</strong
        >
      </div>
      <div class="topbar-actions">
        <button
          class="quick-search-button"
          onclick={() => {
            browse();
            setTimeout(() => document.getElementById('card-search')?.focus(), 0);
          }}><Search size={14} /><span>搜索卡片</span><kbd>⌘ K</kbd></button
        ><Button variant="ghost" size="icon-sm" aria-label="切换深浅色" onclick={() => act('theme')}
          >{#if home.dark}<Sun size={17} />{:else}<Moon size={17} />{/if}</Button
        ><Button variant="outline" size="sm" onclick={() => act('sync')}
          ><RefreshCw size={14} />同步</Button
        >
      </div>
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
        <section class="home-page page-content">
          <div class="page-heading">
            <div>
              <div class="eyebrow"><CalendarDays size={14} />{today}</div>
              <h1>今天，又是积累的一天。</h1>
              <p>一点专注，让知识留得更久。</p>
            </div>
            <Button variant="outline" onclick={() => act('add')}><Plus size={16} />添加卡片</Button>
          </div>
          <div class="home-grid">
            <div class="home-primary">
              <section class="study-hero">
                <div class="hero-content">
                  <Badge variant="secondary" class="hero-badge"
                    ><span class="tiny-dot"></span>今日学习</Badge
                  >
                  <h2>
                    {busy ? '正在读取牌组…' : due ? `${due} 张卡片，` : '今天的复习，完成了。'}<br
                    />把新知变成记忆。
                  </h2>
                  <p>跟着自己的节奏，完成今天的一小步。</p>
                  <div class="hero-counts">
                    <div><strong>{home.review}</strong><span>待复习</span></div>
                    <div><strong>{home.learning}</strong><span>学习中</span></div>
                    <div><strong>{home.new}</strong><span>未学习</span></div>
                  </div>
                  <div class="hero-actions">
                    <Button
                      size="lg"
                      onclick={() => act('study')}
                      disabled={!home.decks.length || busy}
                      >继续当前牌组<ArrowRight size={16} /></Button
                    >
                  </div>
                </div>
                <div class="memory-art" aria-hidden="true">
                  <div class="art-card art-back"></div>
                  <div class="art-card art-front">
                    <span class="art-symbol">Aa</span><span class="art-label"
                      >A LITTLE EVERY DAY</span
                    >
                    <div class="art-line"></div>
                    <span class="art-word">Remember<br />more.</span><span class="art-mark"
                      ><Check size={17} /></span
                    >
                  </div>
                  <span class="art-star">✦</span>
                </div>
              </section>
              <section class="deck-section">
                <div class="section-heading">
                  <div class="flex items-center gap-2">
                    <h2>我的牌组</h2>
                    <span class="quiet-count">{home.decks.length}</span>
                  </div>
                  <Button variant="ghost" size="sm" onclick={() => act('create')}
                    ><Plus size={15} />新建牌组</Button
                  >
                </div>
                <div class="deck-table">
                  <div class="deck-table-head">
                    <span>牌组名称</span><span>待复习</span><span>未学习</span><span></span>
                  </div>
                  {#each home.decks as deck}<div class="deck-row">
                      <button
                        class="deck-title-button"
                        onclick={() => act('study', { deckId: deck.id })}
                        ><DeckIcon {deck} /><span
                          ><strong>{deck.name}</strong><small>{deck.learning} 张学习中</small></span
                        ></button
                      ><span class="deck-number blue-text">{deck.review}</span><span
                        class="deck-number muted-text">{deck.new}</span
                      ><Menu.Root
                        ><Menu.Trigger class="icon-control" aria-label={`${deck.name}更多操作`}
                          ><MoreHorizontal size={18} /></Menu.Trigger
                        ><Menu.Content align="end"
                          ><Menu.Item onclick={() => act('study', { deckId: deck.id })}
                            >学习此牌组</Menu.Item
                          ><Menu.Item onclick={() => browse(deck.id)}>查看卡片</Menu.Item><Menu.Item
                            onclick={() => act('options', { deckId: deck.id })}>牌组选项</Menu.Item
                          ><Menu.Item onclick={() => act('rename', { deckId: deck.id })}
                            >重命名牌组</Menu.Item
                          ></Menu.Content
                        ></Menu.Root
                      >
                    </div>{/each}
                  {#if !home.decks.length && !busy}<div class="empty-state">
                      <BookOpen size={30} />
                      <h3>从第一张卡片开始</h3>
                      <Button onclick={() => act('create')}>新建牌组</Button>
                    </div>{/if}
                </div>
                <div class="deck-section-footer">
                  <BookOpen size={14} /><span>好记性，从一张好卡片开始。</span><button
                    onclick={() => browse()}>管理全部卡片<ArrowRight size={13} /></button
                  >
                </div>
              </section>
            </div>
            <aside class="home-aside">
              <section class="daily-goal">
                <div class="aside-heading">
                  <h3>今日学习</h3>
                  <Check size={17} />
                </div>
                <div class="goal-number">{home.completed}<span> 次作答</span></div>
                <div class="live-studied">{@html home.studiedToday}</div>
              </section>
              <section class="activity-panel">
                <div class="aside-heading">
                  <h3>学习足迹</h3>
                  <Badge variant="outline" class="sample-label">最近28天</Badge>
                </div>
                <p class="activity-subtitle">把坚持，留在日历里。</p>
                <div class="activity-grid" aria-label="最近28天的真实作答次数">
                  {#each home.activity as count, i}<span
                      class="activity-cell level-{Math.min(4, Math.ceil(count / 10))}"
                      title={`${27 - i}天前 · ${count}次作答`}
                    ></span>{/each}
                </div>
                <div class="activity-legend">
                  <span>过去 4 周</span>
                  <div>
                    少<span class="activity-cell level-0"></span><span class="activity-cell level-2"
                    ></span><span class="activity-cell level-4"></span>多
                  </div>
                </div>
              </section>
              <div class="preview-note">
                <span class="preview-note-icon"><Layers size={18} /></span><strong
                  >{home.total} 张卡片，慢慢积累。</strong
                >
                <p>今天的数量由牌组学习限制决定。</p>
                <Button variant="outline" size="sm" onclick={() => act('import')}
                  ><Download size={14} />导入资料</Button
                >
              </div>
            </aside>
          </div>
        </section>
      {:else}
        <section class="cards-page">
          <div class="cards-page-heading">
            <div>
              <h1>卡片管理</h1>
              <p>整理每一张，值得记住的卡片。</p>
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
                ><select class="live-deck-filter" aria-label="筛选牌组" bind:value={deckId}
                  ><option value="all">全部牌组</option>{#each home.decks as deck}<option
                      value={deck.id}>{deck.name}</option
                    >{/each}</select
                >
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
