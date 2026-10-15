(() => {
  // Videos ship with native controls so they work without JavaScript. When
  // motion is welcome, turn them into silent loops that pause on click.
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (reduceMotion.matches) return;

  document.querySelectorAll('video[data-autoplay]').forEach((video) => {
    video.controls = false;
    video.muted = true;
    video.play().catch(() => {
      video.controls = true;
    });
    video.addEventListener('click', () => {
      if (video.paused) video.play();
      else video.pause();
    });
  });
})();
