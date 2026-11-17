import { mount } from 'svelte';
import './app.css';
import App from './App.svelte';
import SyncLogin from './SyncLogin.svelte';
import Preferences from './Preferences.svelte';
const target = document.getElementById('app')!;
mount(
  target.dataset.mode === 'sync-login'
    ? SyncLogin
    : target.dataset.mode === 'preferences'
      ? Preferences
      : App,
  { target },
);
