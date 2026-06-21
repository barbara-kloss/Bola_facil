const rankingTable = document.querySelector(".ranking-table");

if (rankingTable) {
  const currentUserId = rankingTable.dataset.currentUserId;
  const currentRow = rankingTable.querySelector(`[data-user-id="${currentUserId}"]`);
  if (currentRow) {
    currentRow.classList.add("current-user");
  }
}
