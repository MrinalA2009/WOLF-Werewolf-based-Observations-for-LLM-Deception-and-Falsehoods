document.addEventListener('DOMContentLoaded', () => {
  const openBtn = document.getElementById('open-debate-trainer');
  const learnBtn = document.getElementById('learn-debate-trainer');
  const panel = document.getElementById('feature-panel');

  function openTrainer() {
    if (window.DebateTrainer?.mountDebateTrainer) {
      window.DebateTrainer.mountDebateTrainer();
      panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  if (openBtn) openBtn.addEventListener('click', openTrainer);
  if (learnBtn) learnBtn.addEventListener('click', () => {
    openTrainer();
    // Add details banner
    const bannerId = 'dt-info-banner';
    if (!document.getElementById(bannerId)) {
      const div = document.createElement('div');
      div.id = bannerId;
      div.className = 'dt-card';
      div.style.marginBottom = '12px';
      div.innerHTML = `
        <div style="font-weight:700;margin-bottom:6px;">Debate Trainer</div>
        <div class="dt-subtle">Critique by speech type (Constructive, Rebuttal, Summary, Final Focus), practice iterative revisions, and spar against AI opponents with Elo ratings.</div>
      `;
      panel.prepend(div);
    }
  });
});