/*
 * Image banner media (sections/image-banner.liquid, Slide blocks): one slide, or a one-at-a-time
 * slider of images and silent looping videos. Styles: section-image-banner.css.
 *
 * - The track scrolls with CSS scroll-snap (swipe / trackpad / arrow keys when focused); the dots
 *   follow the visible slide and jump to a slide when pressed.
 * - Only the visible slide's video plays.
 * - Optional auto-advance (data-autoplay, data-speed in seconds). It stops while keyboard focus is
 *   inside, and for good once the visitor picks a slide.
 * - The pause button stops videos and auto-advance. Visitors whose device asks for reduced motion
 *   start paused.
 * - Theme editor: selecting a Slide block shows that slide and holds auto-advance.
 */
if (!customElements.get('melt-banner-media')) {
  customElements.define(
    'melt-banner-media',
    class MeltBannerMedia extends HTMLElement {
      connectedCallback() {
        this.track = this.querySelector('.banner-media__track');
        this.slides = Array.from(this.querySelectorAll('.banner-media__slide'));
        this.dots = Array.from(this.querySelectorAll('.banner-media__dot'));
        this.toggle = this.querySelector('.banner-media__toggle');
        this.videos = Array.from(this.querySelectorAll('video'));
        if (!this.track || this.slides.length === 0) return;

        this.index = 0;
        this.reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        this.autoplay = this.dataset.autoplay === 'true' && this.slides.length > 1 && !this.reduceMotion;
        this.speed = (parseInt(this.dataset.speed, 10) || 6) * 1000;
        this.hold = false;

        this.onScroll = this.onScroll.bind(this);
        this.onBlockSelect = this.onBlockSelect.bind(this);
        this.onBlockDeselect = this.onBlockDeselect.bind(this);

        if (this.slides.length > 1) {
          this.track.addEventListener('scroll', this.onScroll, { passive: true });
          this.dots.forEach((dot, index) =>
            dot.addEventListener('click', () => {
              this.stopAutoplay();
              this.goTo(index);
            })
          );
          this.addEventListener('focusin', () => this.setHold(true));
          this.addEventListener('focusout', (event) => {
            if (!this.contains(event.relatedTarget)) this.setHold(false);
          });
        }

        this.toggle?.addEventListener('click', () => this.setPaused(!this.paused));
        document.addEventListener('shopify:block:select', this.onBlockSelect);
        document.addEventListener('shopify:block:deselect', this.onBlockDeselect);

        this.setPaused(this.reduceMotion);
      }

      disconnectedCallback() {
        this.track?.removeEventListener('scroll', this.onScroll);
        document.removeEventListener('shopify:block:select', this.onBlockSelect);
        document.removeEventListener('shopify:block:deselect', this.onBlockDeselect);
        window.clearInterval(this.timer);
      }

      goTo(index) {
        this.track.scrollTo({
          left: index * this.track.clientWidth,
          behavior: this.reduceMotion ? 'auto' : 'smooth',
        });
      }

      next() {
        this.goTo((this.index + 1) % this.slides.length);
      }

      onScroll() {
        window.cancelAnimationFrame(this.frame);
        this.frame = window.requestAnimationFrame(() => {
          const index = Math.round(this.track.scrollLeft / this.track.clientWidth);
          if (index === this.index) return;
          this.index = index;
          this.dots.forEach((dot, i) => {
            if (i === index) dot.setAttribute('aria-current', 'true');
            else dot.removeAttribute('aria-current');
          });
          this.updateVideos();
        });
      }

      setPaused(paused) {
        this.paused = paused;
        this.classList.toggle('banner-media--paused', paused);
        if (this.toggle) {
          this.toggle.setAttribute(
            'aria-label',
            paused ? this.toggle.dataset.labelPlay : this.toggle.dataset.labelPause
          );
        }
        this.updateVideos();
        this.updateTimer();
      }

      setHold(hold) {
        this.hold = hold;
        this.updateTimer();
      }

      stopAutoplay() {
        this.autoplay = false;
        this.updateTimer();
      }

      updateTimer() {
        window.clearInterval(this.timer);
        if (this.autoplay && !this.paused && !this.hold) {
          this.timer = window.setInterval(() => this.next(), this.speed);
        }
      }

      updateVideos() {
        const current = this.slides[this.index];
        this.videos.forEach((video) => {
          if (!this.paused && current.contains(video)) {
            video.play().catch(() => {});
          } else {
            video.pause();
          }
        });
      }

      onBlockSelect(event) {
        const index = this.slides.findIndex((slide) => slide === event.target || slide.contains(event.target));
        if (index === -1) return;
        this.setHold(true);
        this.goTo(index);
      }

      onBlockDeselect(event) {
        if (this.slides.some((slide) => slide === event.target || slide.contains(event.target))) {
          this.setHold(false);
        }
      }
    }
  );
}
