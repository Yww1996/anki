<script lang="ts">
  import { onMount } from 'svelte';
  import { RefreshCw, ArrowUpRight, LockKeyhole } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  let username = $state(''),
    password = $state('');
  let userInput = $state<HTMLInputElement | null>(null);
  const root = document.getElementById('app')!;
  const labels = JSON.parse(root.dataset.labels || '{}');
  const send = (accepted: boolean) =>
    window.pycmd(
      `sync-login:${JSON.stringify({ accepted, username: accepted ? username.trim() : '', password: accepted ? password : '' })}`,
    );
  onMount(() => {
    username = root.dataset.username || '';
    document.documentElement.classList.toggle('dark', root.dataset.dark === 'true');
    setTimeout(() => userInput?.focus(), 100);
  });
  function submit(event: SubmitEvent) {
    event.preventDefault();
    if (username.trim() && password) send(true);
  }
</script>

<section class="sync-login-page">
  <div class="sync-login-symbol"><RefreshCw size={25} /></div>
  <h1>{labels.title}</h1>
  <p class="sync-login-intro">登录 AnkiWeb，让卡片和学习进度随身同步。</p>
  <form onsubmit={submit}>
    <div class="sync-form-field">
      <label for="sync-username">{labels.username}</label><Input
        bind:ref={userInput}
        id="sync-username"
        name="username"
        autocomplete="username"
        bind:value={username}
        placeholder="name@example.com"
        required
      />
    </div>
    <div class="sync-form-field">
      <label for="sync-password">{labels.password}</label><Input
        id="sync-password"
        name="password"
        type="password"
        autocomplete="current-password"
        bind:value={password}
        required
      />
    </div>
    <p class="sync-login-register">
      还没有账户？<a href="https://ankiweb.net/account/register"
        >注册 AnkiWeb<ArrowUpRight size={12} /></a
      >
    </p>
    <div class="sync-login-footer">
      <Button variant="outline" type="button" onclick={() => send(false)}>{labels.cancel}</Button
      ><Button type="submit" disabled={!username.trim() || !password}>{labels.submit}</Button>
    </div>
  </form>
  <p class="sync-login-security"><LockKeyhole size={12} />登录信息由 Anki 处理</p>
</section>
