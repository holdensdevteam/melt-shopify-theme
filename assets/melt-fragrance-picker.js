/*
 * Melt: <melt-fragrance-picker> — the Fragrance picker block (snippets/melt-fragrance-picker.liquid).
 *
 * - Up to data-max checkboxes can be ticked; at the limit the others are disabled (and faded in
 *   CSS) until one is unticked.
 * - The ticked names, in list order, go into the hidden properties[...] input, which is tied to the
 *   product form, so they're added to the cart line and the order.
 * - With data-required="true", Add to cart is stopped until exactly data-max are ticked: a
 *   capture-phase submit listener on document runs before Dawn's product-form handler.
 */
if (!customElements.get('melt-fragrance-picker')) {
  customElements.define(
    'melt-fragrance-picker',
    class MeltFragrancePicker extends HTMLElement {
      connectedCallback() {
        this.max = parseInt(this.dataset.max, 10) || 5;
        this.required = this.dataset.required === 'true';
        this.inputs = Array.from(this.querySelectorAll('.melt-fragrance-picker__input'));
        this.valueInput = this.querySelector('.melt-fragrance-picker__value');
        this.countEl = this.querySelector('.melt-fragrance-picker__count');
        this.errorEl = this.querySelector('.melt-fragrance-picker__error');

        this.onChange = this.update.bind(this);
        this.onSubmit = this.validate.bind(this);
        this.addEventListener('change', this.onChange);
        document.addEventListener('submit', this.onSubmit, true);
        this.update();
      }

      disconnectedCallback() {
        this.removeEventListener('change', this.onChange);
        document.removeEventListener('submit', this.onSubmit, true);
      }

      get chosen() {
        return this.inputs.filter((input) => input.checked);
      }

      update() {
        const chosen = this.chosen;
        const full = chosen.length >= this.max;

        this.inputs.forEach((input) => {
          const locked = full && !input.checked;
          input.disabled = locked;
          input.closest('.melt-fragrance-picker__item')?.classList.toggle('is-locked', locked);
        });

        this.classList.toggle('is-full', full);
        this.valueInput.value = chosen.map((input) => input.value).join(', ');
        if (this.countEl && this.dataset.countText) {
          this.countEl.textContent = this.dataset.countText.replace('[count]', chosen.length);
        }
        if (this.errorEl && (!this.required || chosen.length === this.max)) this.errorEl.hidden = true;
      }

      validate(event) {
        if (!this.required) return;
        if (!event.target || event.target.id !== this.dataset.formId) return;
        if (this.chosen.length === this.max) return;

        event.preventDefault();
        event.stopImmediatePropagation();
        if (this.errorEl) this.errorEl.hidden = false;
        const firstFree = this.inputs.find((input) => !input.checked && !input.disabled);
        (firstFree || this.inputs[0])?.focus();
      }
    }
  );
}
