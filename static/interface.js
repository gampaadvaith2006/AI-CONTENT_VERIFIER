document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('news');
  const count = document.getElementById('charCount');
  const updateCount = () => { count.textContent = `${input.value.length.toLocaleString()} / 5,000`; };
  input.addEventListener('input', updateCount);
  document.getElementById('exampleButton').addEventListener('click', () => {
    input.value = 'Scientists announce that drinking two cups of coffee every morning permanently increases human intelligence by 50%, according to a new international study.';
    updateCount(); input.focus();
  });
  const motion = document.getElementById('motionButton');
  const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
  function setMotion(paused) {
    document.body.classList.toggle('motion-paused', paused);
    motion.setAttribute('aria-pressed', String(paused));
    motion.textContent = paused ? 'Resume motion' : 'Pause motion';
  }
  setMotion(preference.matches);
  motion.addEventListener('click', () => setMotion(!document.body.classList.contains('motion-paused')));
});
