const cropForm = document.getElementById("crop-form");
const cropResult = document.getElementById("crop-result");
const diseaseForm = document.getElementById("disease-form");
const diseaseResult = document.getElementById("disease-result");
const yieldForm = document.getElementById("yield-form");
const yieldResult = document.getElementById("yield-result");
const weatherForm = document.getElementById("weather-form");
const weatherResult = document.getElementById("weather-result");

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

yieldForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  yieldResult.innerHTML = "Predicting…";
  setLoading(yieldForm, true);

  const formData = new FormData(yieldForm);
  const payload = Object.fromEntries(formData.entries());
  payload.Year = Number(payload.Year);
  payload.average_rain_fall_mm_per_year = Number(payload.average_rain_fall_mm_per_year);
  payload.pesticides_tonnes = Number(payload.pesticides_tonnes);
  payload.avg_temp = Number(payload.avg_temp);

  try {
    const res = await fetch("/api/yield/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Request failed");
    const data = await res.json();

    const warnings = data.warnings.length
      ? `<p class="hint">⚠ ${data.warnings.join(" ")}</p>`
      : "";

    yieldResult.innerHTML = `
      <div class="result-box">
        <strong>Predicted yield: ${data.predicted_yield_tonnes_per_ha} tonnes/ha</strong>
        (${data.predicted_yield_kg_per_ha} kg/ha)
        <p class="hint">Model: ${data.model_used} (R² = ${data.model_r2})</p>
        ${warnings}
      </div>`;
  } catch (err) {
    yieldResult.innerHTML = `<p class="error">${err.message}</p>`;
  } finally {
    setLoading(yieldForm, false);
  }
});

weatherForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  weatherResult.innerHTML = "Fetching forecast…";
  setLoading(weatherForm, true);

  const formData = new FormData(weatherForm);
  const params = new URLSearchParams({
    location: formData.get("location"),
    days: formData.get("days"),
  });

  try {
    const res = await fetch(`/api/weather/alerts?${params}`);
    if (!res.ok) throw new Error((await res.json()).detail || "Request failed");
    const data = await res.json();

    const alertItems = data.alerts.length
      ? data.alerts
          .map((a) => `<li><strong>${a.date}</strong> — [${a.severity}] ${a.message}</li>`)
          .join("")
      : "<li>No weather alerts for this period.</li>";

    weatherResult.innerHTML = `
      <div class="result-box">
        <strong>${data.location.name}${data.location.country ? ", " + data.location.country : ""}</strong>
        <ul class="alt-list" style="display:block">${alertItems}</ul>
      </div>`;
  } catch (err) {
    weatherResult.innerHTML = `<p class="error">${err.message}</p>`;
  } finally {
    setLoading(weatherForm, false);
  }
});
