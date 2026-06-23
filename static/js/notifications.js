let lastKnownCount = null;

async function checkNotifications() {
  try {
    const res = await fetch('/notificacoes/unread-count');
    if(res.ok) {
      const data = await res.json();
      const badge = document.getElementById('notification-badge');
      if(badge) {
        if(data.count > 0) {
          badge.textContent = data.count;
          badge.style.display = 'inline-block';
        } else {
          badge.style.display = 'none';
        }
      }
      
      // Se a contagem aumentou, mostra um toast para alertar o usuário
      if (lastKnownCount !== null && data.count > lastKnownCount) {
        const diff = data.count - lastKnownCount;
        if (typeof Toast !== 'undefined') {
          Toast.info(`Você tem ${diff} nova(s) notificação(ões)! Veja sua caixa de entrada.`);
        }
      }
      lastKnownCount = data.count;
    }
  } catch(e) {
    console.error(e);
  }
}

async function loadDropdown() {
  const content = document.getElementById('notif-content');
  if(!content) return;
  
  content.innerHTML = '<div style="padding: 1rem; text-align: center; opacity: 0.6;">Carregando...</div>';
  try {
    const res = await fetch('/notificacoes/recentes');
    if(res.ok) {
      const notifs = await res.json();
      if(notifs.length === 0) {
        content.innerHTML = '<div style="padding: 1.5rem 1rem; text-align: center; opacity: 0.6;">Nenhuma notificação recente.</div>';
      } else {
        content.innerHTML = notifs.map(n => `
          <a href="/notificacoes" class="dropdown-item ${n.read ? '' : 'unread'}">
            <h4>${n.title}</h4>
            <p>${n.body}</p>
          </a>
        `).join('');
      }
      // Zero the badge locally since we marked all as read
      const badge = document.getElementById('notification-badge');
      if(badge) {
        badge.textContent = '0';
        badge.style.display = 'none';
        lastKnownCount = 0;
      }
    }
  } catch(e) {
    console.error(e);
    content.innerHTML = '<div style="padding: 1rem; text-align: center; opacity: 0.6;">Erro ao carregar notificações.</div>';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  checkNotifications();
  setInterval(checkNotifications, 15000);
  
  // Dropdown Logic
  const toggle = document.getElementById('notif-toggle');
  const menu = document.getElementById('notif-menu');
  
  if(toggle && menu) {
    toggle.addEventListener('click', (e) => {
      e.stopPropagation();
      const isActive = menu.classList.contains('active');
      
      // Fecha outros menus se houver
      document.querySelectorAll('.dropdown-menu.active').forEach(m => m.classList.remove('active'));
      
      if(!isActive) {
        menu.classList.add('active');
        loadDropdown();
      }
    });
    
    // Fechar ao clicar fora
    document.addEventListener('click', (e) => {
      if(!menu.contains(e.target) && !toggle.contains(e.target)) {
        menu.classList.remove('active');
      }
    });
  }
});
