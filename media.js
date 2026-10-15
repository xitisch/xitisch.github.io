(() => {
  // Videos autoplay as silent loops straight from the HTML, with no click
  // needed. Visitors who ask for reduced motion get a paused video with
  // controls instead; everyone else can click a video to pause it.
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  document.querySelectorAll('video[autoplay]').forEach((video) => {
    if (reduceMotion) {
      video.pause();
      video.controls = true;
      return;
    }

    video.muted = true;
    // Some browsers (e.g. iOS Low Power Mode) block autoplay; offer controls then.
    video.play().catch(() => {
      video.controls = true;
    });
    video.addEventListener('click', () => {
      if (video.controls) return;
      if (video.paused) video.play();
      else video.pause();
    });
  });
})();
