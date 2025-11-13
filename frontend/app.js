const API_BASE = '/api';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || 'Request failed');
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

function renderEmptyState(container, message) {
  container.innerHTML = '';
  const div = document.createElement('div');
  div.className = 'empty-state';
  div.textContent = message;
  container.appendChild(div);
}

function formatMacros(macronutrients) {
  const entries = Object.entries(macronutrients || {});
  if (!entries.length) {
    return 'Macros: not provided';
  }
  return `Macros: ${entries.map(([key, value]) => `${key} ${Number(value).toFixed(1)}g`).join(' • ')}`;
}

function renderScanResults(results) {
  const container = document.getElementById('scan-results');
  container.innerHTML = '';

  if (!results.items.length) {
    renderEmptyState(container, 'No AI matches yet. Try a different description.');
    return;
  }

  const template = document.getElementById('scan-item-template');

  results.items.forEach(({ food, confidence }) => {
    const fragment = template.content.cloneNode(true);
    fragment.querySelector('.scan-title').textContent = food.name;
    fragment.querySelector('.scan-serving').textContent = `Serving: ${food.serving_size}`;
    fragment.querySelector('.scan-calories').textContent = `${food.calories} kcal`;
    fragment.querySelector('.scan-confidence').textContent = `Confidence: ${(confidence * 100).toFixed(0)}%`;

    const quantityInput = fragment.querySelector('.scan-quantity');
    const logButton = fragment.querySelector('.log-button');

    logButton.addEventListener('click', async () => {
      logButton.disabled = true;
      try {
        const quantity = Number(quantityInput.value) || 1;
        await request('/entries', {
          method: 'POST',
          body: JSON.stringify({ food, quantity }),
        });
        await Promise.all([loadEntries(), loadSummary()]);
      } catch (error) {
        alert(error.message);
      } finally {
        logButton.disabled = false;
      }
    });

    container.appendChild(fragment);
  });
}

function renderEntries(entries) {
  const container = document.getElementById('log-entries');
  container.innerHTML = '';

  if (!entries.items.length) {
    renderEmptyState(container, 'No foods logged yet. Scan or add one to get started.');
    return;
  }

  entries.items.forEach((entry) => {
    const card = document.createElement('article');
    card.className = 'log-entry';

    const title = document.createElement('h3');
    title.textContent = entry.food.name;

    const calories = document.createElement('p');
    calories.innerHTML = `<span class="badge">${entry.calories.toFixed(0)} kcal</span> — Qty ${entry.quantity}`;

    const serving = document.createElement('p');
    serving.textContent = `Serving: ${entry.food.serving_size}`;

    const macros = document.createElement('p');
    macros.textContent = formatMacros(entry.macronutrients);

    const timestamp = document.createElement('p');
    const date = new Date(entry.timestamp);
    timestamp.textContent = `Logged at ${date.toLocaleString()}`;

    card.append(title, calories, serving, macros, timestamp);
    container.appendChild(card);
  });
}

function renderSummary(summary) {
  const container = document.getElementById('summary');
  container.innerHTML = '';

  if (!summary.days.length) {
    renderEmptyState(container, 'Once you have entries we will show daily totals here.');
    return;
  }

  summary.days.forEach((day) => {
    const card = document.createElement('article');
    card.className = 'summary-day';

    const title = document.createElement('h3');
    const date = new Date(day.day);
    title.textContent = date.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });

    const calories = document.createElement('p');
    calories.innerHTML = `<span class="badge">${day.total_calories.toFixed(0)} kcal</span>`;

    const macros = document.createElement('p');
    macros.textContent = formatMacros(day.total_macronutrients);

    card.append(title, calories, macros);
    container.appendChild(card);
  });
}

async function loadEntries() {
  try {
    const entries = await request('/entries');
    renderEntries(entries);
  } catch (error) {
    console.error(error);
  }
}

async function loadSummary() {
  try {
    const summary = await request('/summary');
    renderSummary(summary);
  } catch (error) {
    console.error(error);
  }
}

function collectMacros(form) {
  const macros = {};
  const protein = Number(form['manual-protein'].value);
  const carbs = Number(form['manual-carbs'].value);
  const fat = Number(form['manual-fat'].value);

  if (!Number.isNaN(protein) && form['manual-protein'].value) macros.protein = protein;
  if (!Number.isNaN(carbs) && form['manual-carbs'].value) macros.carbs = carbs;
  if (!Number.isNaN(fat) && form['manual-fat'].value) macros.fat = fat;

  return macros;
}

async function setupScanForm() {
  const form = document.getElementById('scan-form');
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const input = form.querySelector('#scan-query');
    const query = input.value.trim();
    if (!query) return;

    form.querySelector('button').disabled = true;
    try {
      const results = await request(`/foods/search?query=${encodeURIComponent(query)}`, {
        method: 'GET',
        headers: {},
      });
      renderScanResults(results);
    } catch (error) {
      alert(error.message);
    } finally {
      form.querySelector('button').disabled = false;
    }
  });
}

async function setupManualForm() {
  const form = document.getElementById('manual-form');
  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const data = {
      name: form['manual-name'].value.trim(),
      serving_size: form['manual-serving'].value.trim(),
      calories: Number(form['manual-calories'].value),
      macronutrients: collectMacros(form),
      aliases: [],
    };
    const quantity = Number(form['manual-quantity'].value) || 1;
    const saveToLibrary = form['manual-save'].checked;

    try {
      await request('/entries', {
        method: 'POST',
        body: JSON.stringify({ food: data, quantity }),
      });
      if (saveToLibrary) {
        await request('/foods', { method: 'POST', body: JSON.stringify(data) });
      }
      form.reset();
      form['manual-quantity'].value = '1';
      await Promise.all([loadEntries(), loadSummary()]);
    } catch (error) {
      alert(error.message);
    }
  });
}

async function init() {
  await Promise.all([loadEntries(), loadSummary()]);
  setupScanForm();
  setupManualForm();
}

init();
