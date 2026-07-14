const cropForm = document.getElementById("crop-form");
const cropResult = document.getElementById("crop-result");
const diseaseForm = document.getElementById("disease-form");
const diseaseResult = document.getElementById("disease-result");

function setLoading(el, isLoading) {
  const btn = el.querySelector("button");
  btn.disabled = isLoading;
}

cropForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  cropResult.innerHTML = "Loading…";
  setLoading(cropForm, true);

  const formData = new FormData(cropForm);
  const payload = {};
  for (const [key, value] of formData.entries()) {
    payload[key] = Number(value);
  }

  try {
    const res = await fetch("/api/crop/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Request failed");
    const data = await res.json();

    const altItems = data.alternatives
      .map(
        (a) => `<li><span>${a.crop}</span><span>${(a.confidence * 100).toFixed(1)}%</span></li>`
      )
      .join("");

    cropResult.innerHTML = `
      <div class="result-box">
        <strong>Recommended crop: ${data.top_recommendation}</strong>
        (${(data.confidence * 100).toFixed(1)}% confidence, model: ${data.model_used})
        <ul class="alt-list">${altItems}</ul>
      </div>`;
  } catch (err) {
    cropResult.innerHTML = `<p class="error">${err.message}</p>`;
  } finally {
    setLoading(cropForm, false);
  }
});

diseaseForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  diseaseResult.innerHTML = "Analyzing…";
  setLoading(diseaseForm, true);

  const formData = new FormData(diseaseForm);

  try {
    const res = await fetch("/api/disease/detect", {
      method: "POST",
      body: formData,
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Request failed");
    const data = await res.json();

    diseaseResult.innerHTML = `
      <div class="result-box">
        <strong>Status: ${data.status.replace(/_/g, " ")}</strong><br />
        Severity: ${data.severity_percent}% &middot; Confidence: ${(data.confidence * 100).toFixed(0)}%
        <p>${data.message}</p>
        <p class="hint">Method: ${data.method}</p>
      </div>`;
  } catch (err) {
    diseaseResult.innerHTML = `<p class="error">${err.message}</p>`;
  } finally {
    setLoading(diseaseForm, false);
  }
});
