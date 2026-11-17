import { mount } from 'svelte';
import './app.css';
import App from './App.svelte';
import SyncLogin from './SyncLogin.svelte';
const target = document.getElementById('app')!;
mount(target.dataset.mode === 'sync-login' ? SyncLogin : App, { target });
