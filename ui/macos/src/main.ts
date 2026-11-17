import { mount } from 'svelte';
import './app.css';
import App from './App.svelte';
import SyncLogin from './SyncLogin.svelte';
import Preferences from './Preferences.svelte';
import ReviewControls from './ReviewControls.svelte';
import ReviewHeader from './ReviewHeader.svelte';
const target = document.getElementById('app')!;
if (target.dataset.mode?.startsWith('review-'))
  document.documentElement.classList.add('compact-chrome');
mount(
  target.dataset.mode === 'sync-login'
    ? SyncLogin
    : target.dataset.mode === 'preferences'
      ? Preferences
      : target.dataset.mode === 'review-controls'
        ? ReviewControls
        : target.dataset.mode === 'review-header'
          ? ReviewHeader
          : App,
  { target },
);

// Theme updates reach each embedded view through Anki's existing body classes.
const syncTheme = () =>
  document.documentElement.classList.toggle('dark', document.body.classList.contains('nightMode'));
syncTheme();
const themeObserver = new MutationObserver(syncTheme);
themeObserver.observe(document.body, { attributes: true, attributeFilter: ['class'] });
window.addEventListener('pagehide', () => themeObserver.disconnect(), { once: true });
