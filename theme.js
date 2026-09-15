(() => {
  const root = document.documentElement;
  const storageKey = 'portfolio-theme';
  const colorPreference = window.matchMedia('(prefers-color-scheme: dark)');
  const themeColors = { light: '#fbfaf6', dark: '#111827' };
  let hasStoredPreference = false;

  const readStoredTheme = () => {
    try {
      const storedTheme = localStorage.getItem(storageKey);
      if (storedTheme === 'light' || storedTheme === 'dark') {
        hasStoredPreference = true;
        return storedTheme;
      }
    } catch {
      return null;
    }

    return null;
  };

  const updateThemeColor = (theme) => {
    const themeColor = document.querySelector('meta[name="theme-color"]');
    if (themeColor) themeColor.setAttribute('content', themeColors[theme]);
  };

  const updateToggle = (theme) => {
    const toggle = document.querySelector('.theme-toggle');
    if (!toggle) return;

    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    const label = `Switch to ${nextTheme} theme`;
    toggle.setAttribute('aria-label', label);
    toggle.setAttribute('aria-pressed', String(theme === 'dark'));
    toggle.setAttribute('title', label);
  };

  const applyTheme = (theme) => {
    root.dataset.theme = theme;
    updateThemeColor(theme);
    updateToggle(theme);
  };

  const systemTheme = () => (colorPreference.matches ? 'dark' : 'light');
  applyTheme(readStoredTheme() || systemTheme());

  const setupToggle = () => {
    const toggle = document.querySelector('.theme-toggle');
    if (!toggle) return;

    toggle.hidden = false;
    updateToggle(root.dataset.theme);
    toggle.addEventListener('click', () => {
      const nextTheme = root.dataset.theme === 'dark' ? 'light' : 'dark';
      hasStoredPreference = true;
      applyTheme(nextTheme);

      try {
        localStorage.setItem(storageKey, nextTheme);
      } catch {
        // The selected theme still applies for the current page.
      }
    });
  };

  colorPreference.addEventListener('change', () => {
    if (!hasStoredPreference) applyTheme(systemTheme());
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupToggle);
  } else {
    setupToggle();
  }
})();
