/*
 * Melt: close Seal Subscriptions' "Subscription details" popup on a click anywhere outside it,
 * or on Escape. Seal (set to open the popup on click) only closes it when the same text is
 * clicked again. Seal shows the popup by adding .sls-show to .sls-more-info-text, which also
 * contains the popup, so clicks inside the popup or on the text are left to Seal.
 * Loaded by snippets/buy-buttons.liquid.
 */
(() => {
  if (window.meltSealDetails) return;
  window.meltSealDetails = true;

  const closeOpen = (except) => {
    document.querySelectorAll('.sls-more-info-text.sls-show').forEach((el) => {
      if (!except || !el.contains(except)) el.classList.remove('sls-show');
    });
  };

  document.addEventListener('click', (event) => closeOpen(event.target));

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeOpen(null);
  });
})();
