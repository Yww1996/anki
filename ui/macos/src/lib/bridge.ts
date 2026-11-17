export interface Deck {
  id: string;
  name: string;
  description: string;
  color: string;
  icon: 'book';
  new: number;
  learning: number;
  review: number;
  level: number;
}
export interface Home {
  decks: Deck[];
  new: number;
  learning: number;
  review: number;
  completed: number;
  studiedToday: string;
  activity: number[];
  total: number;
  dark: boolean;
  profile: string;
  page: string;
  cardFilters?: { query: string; deckId: string; state: string };
  overview?: {
    id: string;
    name: string;
    new: number;
    learning: number;
    review: number;
    finished: boolean;
    filtered: boolean;
    description: string;
    buried: boolean;
    learnRemaining: number;
    nextLearnSeconds: number;
    newLimitReached: boolean;
    reviewLimitReached: boolean;
    shared: boolean;
  };
}
export interface Card {
  id: string;
  deckId: string;
  front: string;
  back: string;
  tags: string[];
  fields: { name: string; text: string }[];
  type: string;
  suspended: boolean;
}
declare global {
  interface Window {
    pycmd: (command: string, callback?: (result: any) => void) => void;
    ankiModernReceive: (message: { id: number; result: any; error: string }) => void;
  }
}
let nextId = 0;
const pending = new Map<
  number,
  {
    resolve: (result: any) => void;
    reject: (error: Error) => void;
    timer: ReturnType<typeof setTimeout>;
  }
>();
window.ankiModernReceive = ({ id, result, error }) => {
  const req = pending.get(id);
  if (!req) return;
  clearTimeout(req.timer);
  pending.delete(id);
  if (error) req.reject(new Error(error));
  else req.resolve(result);
};
export async function command<T = unknown>(action: string, args = {}): Promise<T> {
  // Qt installs its web channel at DocumentReady, after Svelte has mounted.
  for (let attempt = 0; !window.pycmd && attempt < 250; attempt++)
    await new Promise((resolve) => setTimeout(resolve, 20));
  return new Promise((resolve, reject) => {
    const id = ++nextId;
    const timer = setTimeout(() => {
      pending.delete(id);
      reject(new Error('操作等待时间较长，请重试。'));
    }, 60000);
    pending.set(id, { resolve, reject, timer });
    if (!window.pycmd) {
      clearTimeout(timer);
      pending.delete(id);
      reject(new Error('请从 Anki 应用打开这个界面。'));
      return;
    }
    window.pycmd(`modern:${JSON.stringify({ id, action, args })}`);
  });
}
