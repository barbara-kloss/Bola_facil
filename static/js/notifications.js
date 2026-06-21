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
    }
  } catch(e) {
    console.error(e);
  }
}

// Check on load and every 60 seconds
document.addEventListener('DOMContentLoaded', () => {
  checkNotifications();
  setInterval(checkNotifications, 60000);
});
