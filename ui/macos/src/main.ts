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

// The native webview must grow when compact controls wrap at narrow widths.
if (target.dataset.mode?.startsWith('review-')) {
  let lastHeight = -1;
  let attempts = 0;
  const notifyHeight = () => {
    if (!window.pycmd) {
      if (++attempts < 250) setTimeout(notifyHeight, 20);
      return;
    }
    const height = Math.ceil(target.getBoundingClientRect().height);
    if (height !== lastHeight) {
      lastHeight = height;
      window.pycmd('modern-chrome-resize');
    }
  };
  const sizeObserver = new ResizeObserver(notifyHeight);
  sizeObserver.observe(target);
  window.addEventListener('pagehide', () => sizeObserver.disconnect(), { once: true });
}
