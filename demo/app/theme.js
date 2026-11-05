// Spec: knowledge/policies/ui-ux.md — light, dark or system theme, remembered per browser.
(() => {
  const KEY = 'aeion.theme';
  const CHOICES = ['system', 'light', 'dark'];
  const LABELS = {system: 'Auto', light: 'Light', dark: 'Dark'};
  const read = () => { try { const v = localStorage.getItem(KEY); return CHOICES.includes(v) ? v : 'system'; } catch { return 'system'; } };
  const apply = (choice) => {
    if (choice === 'system') document.documentElement.removeAttribute('data-theme');
    else document.documentElement.setAttribute('data-theme', choice);
    document.querySelectorAll('[data-theme-toggle]').forEach((button) => {
      button.replaceChildren(document.createTextNode('Theme '), Object.assign(document.createElement('b'), {textContent: LABELS[choice]}));
      button.setAttribute('aria-label', `Colour theme: ${LABELS[choice]}. Change theme`);
    });
  };
  let current = read();
  apply(current);
  document.addEventListener('DOMContentLoaded', () => {
    apply(current);
    document.querySelectorAll('[data-theme-toggle]').forEach((button) => button.addEventListener('click', () => {
      current = CHOICES[(CHOICES.indexOf(current) + 1) % CHOICES.length];
      try { localStorage.setItem(KEY, current); } catch { /* private window: the choice lasts this page only */ }
      apply(current);
    }));
  });
})();
