const canvas = document.querySelector("#pointsChart");

if (canvas) {
  const ctx = canvas.getContext("2d");
  const values = JSON.parse(canvas.dataset.values || "[0,0,0]");
  const labels = ["Bolões", "Palpites", "Pontos"];
  const max = Math.max(...values, 1);
  const width = canvas.width;
  const height = canvas.height;
  const barWidth = 120;
  const gap = 90;

  ctx.clearRect(0, 0, width, height);
  ctx.font = "600 16px Montserrat, Arial";
  values.forEach((value, index) => {
    const barHeight = Math.max(8, (value / max) * 210);
    const x = 80 + index * (barWidth + gap);
    const y = height - barHeight - 54;
    ctx.fillStyle = ["#00A651", "#1A55A0", "#FFD700"][index];
    ctx.fillRect(x, y, barWidth, barHeight);
    ctx.fillStyle = "#003087";
    ctx.fillText(String(value), x + 42, y - 12);
    ctx.fillText(labels[index], x + 16, height - 24);
  });
}
