<script lang="ts">
  import { onMount } from 'svelte';
  import { Pencil, MoreHorizontal, ArrowRight } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button';
  const meta = JSON.parse(document.getElementById('app')!.dataset.meta || '{}');
  let buttons: { id: string; label: string; time: string; ease: string; title: string }[] = $state(
    [],
  );
  let remaining = $state(''),
    elapsed = $state(0),
    limit = $state(0),
    stopped = $state(false);
  let question = $state(true);
  let queues: { label: string; value: string; kind: string; current: boolean }[] = $state([]);
  let legacyHtml = $state('');
  function update(html: string) {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    legacyHtml =
      Array.from(doc.querySelectorAll('button')).some(
        (b) => !/pycmd\(["'](?:ans|ease[1-4])["']\)/.test(b.getAttribute('onclick') || ''),
      ) || !!doc.querySelector('script,a,[onclick]:not(button)')
        ? html
        : '';
    remaining = doc.querySelector('.stattxt')?.innerHTML || '';
    const labels = [
      ['new', '未学习'],
      ['learn', '学习中'],
      ['review', '待复习'],
    ];
    queues = labels.flatMap(([kind, label]) => {
      const count = doc.querySelector(`.stattxt .${kind}-count`);
      return count
        ? [
            {
              label,
              kind,
              value: count.textContent?.trim() || '0',
              current: !!count.querySelector('u'),
            },
          ]
        : [];
    });
    buttons = Array.from(doc.querySelectorAll('button')).map((b) => {
      const clone = b.cloneNode(true) as HTMLElement;
      clone.querySelectorAll('.stattxt,.nobold').forEach((n) => n.remove());
      return {
        id: b.id,
        label: clone.textContent?.trim() || '',
        time: b.querySelector('.nobold')?.textContent || '',
        ease: b.dataset.ease || '',
        title: b.title,
      };
    });
  }
  Object.assign(window, {
    showQuestion: (html: string, max: number) => {
      question = true;
      update(html);
      elapsed = 0;
      limit = max;
      stopped = false;
    },
    showAnswer: (html: string, stop = false) => {
      question = false;
      update(html);
      stopped = stop;
    },
    selectedAnswerButton: () =>
      document.activeElement instanceof HTMLElement
        ? document.activeElement.dataset.ease
        : undefined,
  });
  onMount(() => {
    const timer = setInterval(() => {
      if (!stopped && limit > 0) elapsed = Math.min(limit, elapsed + 1);
    }, 1000);
    return () => clearInterval(timer);
  });
</script>

<div class="review-controls" class:question>
  <Button variant="ghost" size="sm" onclick={() => window.pycmd('edit')}
    ><Pencil size={15} />{meta.edit}</Button
  >
  <div class="review-ratings">
    <div class="review-remaining" aria-label="剩余卡片">
      {#if queues.length}{#each queues as queue}<span
            class="queue-count queue-{queue.kind}"
            class:current={queue.current}
            ><span>{queue.label}</span><strong>{queue.value}</strong></span
          >{/each}{:else}{@html remaining}{/if}
    </div>
    <div class="review-rating-buttons">
      {#if legacyHtml}<div class="review-native-controls">{@html legacyHtml}</div>{:else}
        {#each buttons as button}<div class="review-rating-option">
            <span>{button.time}</span><Button
              id={button.id || undefined}
              data-ease={button.ease || undefined}
              variant={question || button.id === 'defease' ? 'default' : 'outline'}
              title={button.title}
              onclick={() => window.pycmd(button.ease ? `ease${button.ease}` : 'ans')}
              >{button.label}{#if question}<ArrowRight size={15} />{/if}</Button
            >
          </div>{/each}
      {/if}
    </div>
  </div>
  <div class="review-more">
    {#if limit > 0}<span>{Math.floor(elapsed / 60)}:{String(elapsed % 60).padStart(2, '0')}</span
      >{/if}<Button variant="ghost" size="sm" onclick={() => window.pycmd('more')}
      >{meta.more}<MoreHorizontal size={16} /></Button
    >
  </div>
</div>
