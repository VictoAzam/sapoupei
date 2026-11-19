const deleteDialog = document.querySelector("[data-delete-dialog]");

document.querySelectorAll("form").forEach((form) => {
  form.addEventListener("submit", (event) => {
    if (form.method === "dialog") return;
    if (!form.checkValidity()) return;
    const submitter = event.submitter;
    if (submitter?.matches("[data-delete-cancel], [data-delete-trigger]")) return;
    if (submitter instanceof HTMLButtonElement) {
      submitter.disabled = true;
      submitter.classList.add("is-submitting");
      submitter.setAttribute("aria-busy", "true");
    }
  });
});

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("/service-worker.js"));
}

if (deleteDialog) {
  let pendingDeleteForm = null;
  const description = deleteDialog.querySelector("#delete-dialog-description");
  const title = deleteDialog.querySelector("#delete-dialog-title");

  document.querySelectorAll("[data-delete-trigger]").forEach((button) => {
    button.addEventListener("click", () => {
      pendingDeleteForm = button.closest("[data-delete-form]");
      const entity = pendingDeleteForm.dataset.deleteEntity || "movimentação";
      const subject = pendingDeleteForm.dataset.deleteSubject || "A movimentação";
      title.textContent = `Excluir ${entity}?`;
      description.textContent = `${subject} "${pendingDeleteForm.dataset.description}" será removida. Esta ação não pode ser desfeita.`;
      deleteDialog.showModal();
    });
  });

  deleteDialog.querySelector("[data-delete-cancel]").addEventListener("click", () => {
    deleteDialog.close();
    pendingDeleteForm = null;
  });

  deleteDialog.querySelector("[data-delete-confirm]").addEventListener("click", () => {
    pendingDeleteForm?.requestSubmit();
  });

  deleteDialog.addEventListener("close", () => {
    pendingDeleteForm = null;
  });
}