
// --- Filtros de jogos ---
const rows = Array.from(document.querySelectorAll('.match-row'));
const searchInput = document.getElementById('filter-search');
const chipsContainer = document.getElementById('filter-chips');
const statusSelect = document.getElementById('filter-status');
const noResults = document.getElementById('no-results');

// Coletar campeonatos únicos
const comps = [...new Set(rows.map(r => r.dataset.comp).filter(Boolean))];
comps.forEach(comp => {
  const btn = document.createElement('button');
  btn.className = 'filter-chip';
  btn.dataset.comp = comp;
  btn.textContent = comp;
  btn.type = 'button';
  chipsContainer.appendChild(btn);
});

function applyFilters() {
  const search = searchInput.value.toLowerCase().trim();
  const comp = chipsContainer.querySelector('.filter-chip.active')?.dataset.comp || '';
  const status = statusSelect.value;
  let visible = 0;
  rows.forEach(row => {
    const matchesSearch = !search || row.dataset.home.includes(search) || row.dataset.away.includes(search);
    const matchesComp = !comp || row.dataset.comp === comp;
    const matchesStatus = !status || row.dataset.status === status;
    const show = matchesSearch && matchesComp && matchesStatus;
    row.style.display = show ? '' : 'none';
    if (show) visible++;
  });
  noResults.style.display = visible === 0 ? '' : 'none';
}

chipsContainer.addEventListener('click', function(e) {
  const chip = e.target.closest('.filter-chip');
  if (!chip) return;
  chipsContainer.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
  chip.classList.add('active');
  applyFilters();
});

searchInput.addEventListener('input', applyFilters);
statusSelect.addEventListener('change', applyFilters);

// Criar jogo feedback
const form = document.querySelector('form.side-form');
if (form) {
  form.addEventListener('submit', function(e) {
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Criando...';
    setTimeout(() => { submitBtn.disabled = false; submitBtn.textContent = originalText; }, 2000);
  });
}

// Converte os flashes do Flask para toasters
document.addEventListener('DOMContentLoaded', function() {
  const flashElements = document.querySelectorAll('.flash');
  flashElements.forEach(el => {
    const type = el.className.includes('success') ? 'success' : 
                 el.className.includes('error') ? 'error' : 'info';
    const message = el.textContent.trim();
    Toast[type](message);
    el.remove();
  });

  // AJAX Form Submission
  document.querySelectorAll('.result-form').forEach(form => {
    form.addEventListener('submit', async function(e) {
      e.preventDefault();
      const fd = new FormData(this);
      try {
        const res = await fetch(this.action, {
          method: 'POST',
          body: fd,
          headers: {'X-Requested-With': 'XMLHttpRequest'}
        });
        if(res.ok) {
          window.location.reload();
        } else {
          Toast.error('Erro ao salvar resultado');
        }
      } catch(err) { console.error(err); }
    });
  });

  // Handle modal form submission with AJAX
  const adminForm = document.getElementById('admin-result-form');
  if (adminForm) {
    adminForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      const fd = new FormData(this);
      try {
        const res = await fetch(this.action, {
          method: 'POST',
          body: fd,
          headers: {'X-Requested-With': 'XMLHttpRequest'}
        });
        if(res.ok) {
          window.location.reload();
        } else {
          Toast.error('Erro ao salvar resultado');
        }
      } catch(err) { 
        console.error(err); 
        Toast.error('Erro na conexão');
      }
    });
  }
});

function openAdminModal(gameId, homeTeam, awayTeam) {
  const adminModal = document.getElementById('admin-result-modal');
  const adminForm = document.getElementById('admin-result-form');
  document.getElementById('modal-home-team').textContent = homeTeam;
  document.getElementById('modal-away-team').textContent = awayTeam;
  document.getElementById('modal-home-score').value = '';
  document.getElementById('modal-away-score').value = '';
  adminForm.action = "{{ url_for('games.record_result', game_id=0) }}".replace('0', gameId);
  adminModal.classList.add('active');
  setTimeout(() => document.getElementById('modal-home-score').focus(), 100);
}

function closeAdminModal() {
  document.getElementById('admin-result-modal').classList.remove('active');
}

// Attach close handlers globally
document.addEventListener('DOMContentLoaded', function() {
  const modal = document.getElementById('admin-result-modal');
  if (modal) {
    modal.addEventListener('click', function(e) {
      if (e.target === modal) closeAdminModal();
    });
  }

  // Handle modal form submission with AJAX
  const adminForm = document.getElementById('admin-result-form');
  if (adminForm) {
    adminForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      const fd = new FormData(this);
      const submitBtn = this.querySelector('button[type="submit"]');
      const originalText = submitBtn.textContent;
      submitBtn.disabled = true;
      submitBtn.textContent = 'Salvando...';
      try {
        const res = await fetch(this.action, {
          method: 'POST',
          body: fd,
          headers: {'X-Requested-With': 'XMLHttpRequest'}
        });
        if(res.ok) {
          closeAdminModal();
          window.location.reload();
        } else {
          Toast.error('Erro ao salvar resultado');
          submitBtn.disabled = false;
          submitBtn.textContent = originalText;
        }
      } catch(err) { 
        console.error(err); 
        Toast.error('Erro na conexão');
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
      }
    });
  }
});

