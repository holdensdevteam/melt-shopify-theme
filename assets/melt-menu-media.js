// Mega menu media panel (snippets/header-mega-menu.liquid). Hovering or focusing a menu link shows
// that link's image or video; leaving the links, or closing the menu, goes back to the default.
if (!customElements.get('melt-menu-media')) {
  customElements.define(
    'melt-menu-media',
    class MeltMenuMedia extends HTMLElement {
      connectedCallback() {
        this.items = Array.from(this.querySelectorAll('[data-menu-media]'));
        this.reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
        this.list = this.querySelector('.mega-menu__list');
        this.details = this.closest('details');

        this.addEventListener('pointerover', this.onTarget.bind(this));
        this.addEventListener('focusin', this.onTarget.bind(this));
        this.list?.addEventListener('pointerleave', () => this.show('default'));
        this.details?.addEventListener('toggle', () => {
          if (!this.details.open) this.show('default');
        });
      }

      onTarget(event) {
        const link = event.target.closest('[data-menu-media-target]');
        if (link && this.contains(link)) this.show(link.dataset.menuMediaTarget);
      }

      show(key) {
        const next =
          this.items.find((item) => item.dataset.menuMedia === key) ||
          this.items.find((item) => item.dataset.menuMedia === 'default');
        if (!next || next.classList.contains('is-active')) return;

        this.items.forEach((item) => {
          const active = item === next;
          item.classList.toggle('is-active', active);
          const video = item.querySelector('video');
          if (!video) return;
          if (active && !this.reducedMotion.matches) {
            video.play().catch(() => {});
          } else {
            video.pause();
          }
        });
      }
    }
  );
}
