const form = document.getElementById("form");
const statusEl = document.getElementById("status");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  statusEl.textContent = "Uploading + analyzing...";

  const fd = new FormData(form);

  try {
    const resp = await fetch("/api/analyze", {
      method: "POST",
      body: fd,
    });

    if (!resp.ok) {
      const msg = await resp.text();
      statusEl.textContent = "Error:\n" + msg;
      return;
    }

    // This endpoint returns a file directly
    const blob = await resp.blob();

    // Try to read filename from header
    const cd = resp.headers.get("Content-Disposition") || "";
    let filename = "result";
    const match = cd.match(/filename="([^"]+)"/);
    if (match) filename = match[1];

    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);

    statusEl.textContent = "Done. Download should have started.";
  } catch (err) {
    statusEl.textContent = "Request failed:\n" + err;
  }
});