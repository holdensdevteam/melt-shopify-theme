/*
 * Footer menu accordion (sections/footer.liquid).
 *
 * Below 990px each footer menu collapses behind its heading button. The CSS only
 * hides the links once this element is defined, so without JS they stay visible.
 * On desktop the toggle button is hidden and the menus are always open.
 */
if (!customElements.get('footer-accordion')) {
  customElements.define(
    'footer-accordion',
    class FooterAccordion extends HTMLElement {
      connectedCallback() {
        this.toggle = this.querySelector('.footer-accordion__toggle');
        if (!this.toggle) return;

        this.toggle.addEventListener('click', () => this.setOpen(!this.classList.contains('is-open')));

        // Open the menu being edited when it's selected in the theme editor.
        this.addEventListener('shopify:block:select', () => this.setOpen(true));
      }

      setOpen(open) {
        this.classList.toggle('is-open', open);
        this.toggle.setAttribute('aria-expanded', open);
      }
    }
  );
}
