/*
 * One-at-a-time image slider with dot indicators (Image with text, when it has 2+ images).
 * The track scrolls with CSS scroll-snap (swipe / trackpad / arrow keys when focused); the dots
 * follow the visible slide and jump to a slide when pressed. Styles: component-melt-image-slider.css.
 */
if (!customElements.get('melt-image-slider')) {
  customElements.define(
    'melt-image-slider',
    class MeltImageSlider extends HTMLElement {
      connectedCallback() {
        this.track = this.querySelector('.melt-image-slider__track');
        this.dots = Array.from(this.querySelectorAll('.melt-image-slider__dot'));
        if (!this.track || this.dots.length === 0) return;

        this.onScroll = this.onScroll.bind(this);
        this.track.addEventListener('scroll', this.onScroll, { passive: true });
        this.dots.forEach((dot, index) => dot.addEventListener('click', () => this.goTo(index)));
      }

      disconnectedCallback() {
        this.track?.removeEventListener('scroll', this.onScroll);
      }

      goTo(index) {
        const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        this.track.scrollTo({ left: index * this.track.clientWidth, behavior: reduceMotion ? 'auto' : 'smooth' });
      }

      onScroll() {
        window.cancelAnimationFrame(this.frame);
        this.frame = window.requestAnimationFrame(() => {
          const index = Math.round(this.track.scrollLeft / this.track.clientWidth);
          this.dots.forEach((dot, i) => {
            if (i === index) dot.setAttribute('aria-current', 'true');
            else dot.removeAttribute('aria-current');
          });
        });
      }
    }
  );
}
