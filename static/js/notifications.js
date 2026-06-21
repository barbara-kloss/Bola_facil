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

// Verificar ao carregar e a cada 15 segundos
document.addEventListener('DOMContentLoaded', () => {
  checkNotifications();
  setInterval(checkNotifications, 15000);
});
