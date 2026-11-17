<script lang="ts">
  import { onMount } from 'svelte';
  import { Select } from 'bits-ui';
  import { Check, ChevronDown } from '@lucide/svelte';
  let { value = $bindable(''), options, label, id, disabled = false, class: className = '', onValueChange = (_value: string) => {} }: {
    value?: string;
    options: {value: string; label: string; disabled?: boolean}[];
    label: string;
    id?: string;
    disabled?: boolean;
    class?: string;
    onValueChange?: (value: string) => void;
  } = $props();
  let open = $state(false);
  onMount(() => {
    const dismiss = (event: KeyboardEvent) => {
      if (open && event.key === 'Escape') {
        // Anki's webview also closes child windows on Escape. Consume this one
        // before that document listener so only the selection popup closes.
        event.preventDefault();
        event.stopImmediatePropagation();
        open = false;
      }
    };
    document.addEventListener('keydown', dismiss, true);
    return () => document.removeEventListener('keydown', dismiss, true);
  });
  const selected = $derived(options.find(option => option.value === value)?.label || '请选择');
</script>

<Select.Root type="single" bind:open bind:value items={options} {disabled} {onValueChange} allowDeselect={false}>
  <Select.Trigger {id} title={selected} aria-label={label} class={`modern-select-trigger ${className}`}><span>{selected}</span><ChevronDown size={16} aria-hidden="true"/></Select.Trigger>
  <Select.Portal>
    <Select.Content class="modern-select-content" sideOffset={5} align="start" collisionPadding={12}>

        {#each options as option (option.value)}
          <Select.Item value={option.value} label={option.label} disabled={option.disabled} class="modern-select-option">
            {#snippet children({ selected })}<span>{option.label}</span><span class="modern-select-check">{#if selected}<Check size={16} aria-hidden="true"/>{/if}</span>{/snippet}
          </Select.Item>
        {/each}

    </Select.Content>
  </Select.Portal>
</Select.Root>
