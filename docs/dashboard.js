'use strict';

const byId = id => document.getElementById(id);
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
}[char]));
const number = new Intl.NumberFormat('en', { maximumFractionDigits: 0 });
const compact = new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 });
const percent = new Intl.NumberFormat('en', { style: 'percent', maximumFractionDigits: 1 });
const score = value => value === '' || value == null ? '—' : Number(value).toFixed(3);
const signed = value => `${Number(value) > 0 ? '+' : ''}${score(value)}`;
const empty = message => `<p class="note">${escapeHtml(message)}</p>`;
const colors = ['#245ab4', '#a12d65', '#097268', '#a24a05', '#5d45ad'];
const sources = {
  github: { label: 'GitHub', metric: 'repos', unit: 'repository-query matches' },
  openalex: { label: 'OpenAlex', metric: 'papers', unit: 'work-query matches' },
  stackoverflow: { label: 'Stack Overflow', metric: 'questions', unit: 'question-tag matches' },
};
const modelLabels = {
  full: 'Full model',
  global_rate: 'Training positive rate',
  persistence: 'Field-label persistence',
  github_only: 'GitHub only',
  adoption_only: 'GitHub + Stack Overflow',
  research_plus_adoption: 'Engineering + OpenAlex',
  research_only: 'OpenAlex only',
  graph_only: 'Graph only',
};

function parseCSV(text) {
  const rows = [];
  let row = [], value = '', quoted = false;
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (char === '"') {
      if (quoted && text[i + 1] === '"') {
        value += char;
        i++;
      } else quoted = !quoted;
    } else if (char === ',' && !quoted) {
      row.push(value);
      value = '';
    } else if (char === '\n' && !quoted) {
      row.push(value.replace(/\r$/, ''));
      rows.push(row);
      row = [];
      value = '';
    } else value += char;
  }
  if (value || row.length) rows.push([...row, value.replace(/\r$/, '')]);
  const header = rows.shift() ?? [];
  return rows.filter(item => item.some(Boolean)).map(item => Object.fromEntries(
    header.map((key, index) => [key, item[index] ?? '']),
  ));
}

const embedded = JSON.parse(byId('embedded-run')?.textContent ?? 'null');

async function read(name) {
  const path = `data/${name}`;
  if (embedded) return embedded[path];
  const response = await fetch(path, { cache: 'no-store' });
  if (!response.ok) throw new Error(`${path} returned HTTP ${response.status}`);
  return response.text();
}
const csv = async name => parseCSV(await read(`${name}.csv`));
const json = async name => JSON.parse(await read(`${name}.json`));

function table(headers, rows, className = '') {
  return `<table class="${className}"><thead><tr>${headers.map(name => `<th scope="col">${escapeHtml(name)}</th>`).join('')}</tr></thead>
    <tbody>${rows.join('')}</tbody></table>`;
}

function svg(label, width, height, body) {
  return `<svg role="img" aria-label="${escapeHtml(label)}" viewBox="0 0 ${width} ${height}">${body}</svg>`;
}

function trendChart(rows, domains, years) {
  const container = byId('trend');
  const source = sources[byId('trend-source').value];
  const logarithmic = byId('trend-scale').value === 'log';
  const width = Math.max(250, container.clientWidth);
  const height = width < 500 ? 260 : 345;
  const left = 52, right = width - 18, top = 35, bottom = height - 31;
  const maxCount = Math.max(1, ...rows.map(row => Number(row[source.metric])));
  const power = 10 ** Math.floor(Math.log10(maxCount / 5));
  const step = [1, 2, 5, 10].find(multiplier => multiplier * power >= maxCount / 5) * power;
  const linearMax = Math.ceil(maxCount / step) * step;
  const ticks = logarithmic
    ? [0, ...Array.from({ length: Math.floor(Math.log10(maxCount)) + 1 }, (_, i) => 10 ** i)]
    : Array.from({ length: Math.round(linearMax / step) + 1 }, (_, i) => i * step);
  const transform = logarithmic ? Math.log10 : value => value;
  const offset = logarithmic ? 1 : 0;
  const upper = logarithmic ? maxCount : linearMax;
  const y = count => bottom - (bottom - top) * transform(count + offset) / transform(upper + offset);
  const first = years[0], last = years.at(-1);
  const x = year => left + (right - left) * (last === first ? 0.5 : (year - first) / (last - first));
  const stride = Math.max(1, Math.ceil((last - first) / Math.max(1, Math.floor((right - left) / 55))));
  const unit = `${source.unit[0].toUpperCase()}${source.unit.slice(1)}`;
  const grid = ticks.map(tick => `<line class="grid-line" x1="${left}" x2="${right}" y1="${y(tick)}" y2="${y(tick)}"/>
    <text text-anchor="end" x="${left - 8}" y="${y(tick) + 4}">${compact.format(tick)}</text>`).join('');
  const yearLabels = years.filter(year => year === last || ((year - first) % stride === 0 && last - year >= stride))
    .map(year => `<text text-anchor="middle" x="${x(year)}" y="${height - 8}">${year}</text>`).join('');
  const series = domains.map(domain => {
    const points = rows.filter(row => row.field === domain.id).sort((a, b) => a.year - b.year);
    const path = points.map((row, index) => {
      const command = index && Number(row.year) - Number(points[index - 1].year) === 1 ? 'L' : 'M';
      return `${command}${x(row.year)} ${y(Number(row[source.metric]))}`;
    }).join(' ');
    const marks = points.map(row => `<circle class="chart-point" cx="${x(row.year)}" cy="${y(Number(row[source.metric]))}" r="3.3" fill="${domain.color}">
      <title>${escapeHtml(domain.label)} · ${Number(row.year)} · ${number.format(row[source.metric])} ${source.unit}</title></circle>`).join('');
    return `<path d="${path}" fill="none" stroke="${domain.color}" stroke-width="2.3"/>${marks}`;
  }).join('');
  const label = `${unit} by domain and calendar year, ${logarithmic ? 'logarithmic' : 'linear'} scale. Values are available in the panel CSV.`;
  container.innerHTML = svg(label, width, height, `<text x="${left}" y="17">${unit}</text>${grid}${yearLabels}${series}`);
}

function renderCoverage(observations, domains, years) {
  if (!observations.length) {
    byId('coverage-content').innerHTML = empty('This run has no source-query observations.');
    byId('coverage-year').disabled = true;
    return;
  }
  const records = new Map();
  for (const row of observations) {
    const key = `${row.year}:${row.field}:${row.source}`;
    if (!records.has(key)) records.set(key, []);
    records.get(key).push({ query: row.query, count: Number(row.count) });
  }
  for (const rows of records.values()) rows.sort((a, b) => b.count - a.count || a.query.localeCompare(b.query));
  const yearSelect = byId('coverage-year');
  yearSelect.innerHTML = [...years].reverse().map(year => `<option>${year}</option>`).join('');
  const heatmap = byId('heatmap');
  let selected = { field: domains[0].id, source: 'openalex' };
  const queryRows = (field, source) => records.get(`${yearSelect.value}:${field}:${source}`) ?? [];
  const total = rows => rows.reduce((sum, row) => sum + row.count, 0);
  function renderDetail() {
    const { field, source } = selected;
    const domain = domains.find(item => item.id === field);
    const rows = queryRows(field, source);
    const sum = total(rows);
    const heading = `${domain.label} · ${sources[source].label}`;
    byId('query-detail').innerHTML = `<h3>${escapeHtml(heading)}</h3>
      <p class="note">${Number(yearSelect.value)} · ${number.format(sum)} matches across ${rows.length} queries · ${rows.filter(row => row.count > 0).length} returned matches</p>
      <ul class="query-list">${rows.map(row => `<li><div class="query-label"><span>${escapeHtml(row.query)}</span><span class="num">${number.format(row.count)}</span></div>
        <div class="track" aria-hidden="true"><div class="fill" style="width:${sum ? row.count / sum * 100 : 0}%"></div></div></li>`).join('')}</ul>`;
    for (const button of heatmap.querySelectorAll('button')) {
      button.setAttribute('aria-pressed', String(button.dataset.field === field && button.dataset.source === source));
    }
  }
  function renderYear() {
    const rows = domains.map(domain => `<tr><th scope="row">${escapeHtml(domain.label)}</th>${Object.keys(sources).map(source => {
      const queries = queryRows(domain.id, source);
      if (!queries.length) return '<td>—</td>';
      const sum = total(queries);
      const share = sum ? queries[0].count / sum : null;
      const text = share === null ? 'Zero' : percent.format(share);
      const label = `${domain.label}, ${sources[source].label}, ${share === null ? 'zero matches' : `${text} from the largest query`}`;
      return `<td><button type="button" data-field="${escapeHtml(domain.id)}" data-source="${source}" aria-label="${escapeHtml(label)}" aria-pressed="false"
        style="--heat:rgba(59,113,198,${share === null ? 0.04 : 0.08 + 0.24 * share})">${text}</button></td>`;
    }).join('')}</tr>`);
    heatmap.innerHTML = table(['Domain', ...Object.values(sources).map(source => source.label)], rows, 'heatmap');
    renderDetail();
  }
  heatmap.addEventListener('click', event => {
    const button = event.target.closest('button[data-field]');
    if (!button) return;
    selected = { field: button.dataset.field, source: button.dataset.source };
    renderDetail();
  });
  yearSelect.addEventListener('change', renderYear);
  renderYear();
}

function renderBrier(summary) {
  const rows = summary.filter(row => row.metric === 'brier' && row.mean !== '').sort((a, b) => a.mean - b.mean);
  byId('brier').innerHTML = rows.length ? `<ul class="score-list">${rows.map(row => {
    const highlight = ['adoption_only', 'research_plus_adoption'].includes(row.model) ? ' class="highlight"' : '';
    const interval = `Descriptive interval ${score(row.lo)} to ${score(row.hi)} across ${Number(row.n_folds)} annual folds`;
    return `<li${highlight}><span>${escapeHtml(modelLabels[row.model] ?? row.model)}</span>
      <span class="score-track" title="${interval}"><span class="score-interval" style="left:${row.lo * 100}%;width:${(row.hi - row.lo) * 100}%"></span>
      <span class="score-dot" style="left:${row.mean * 100}%"></span></span><span class="num">${score(row.mean)}</span></li>`;
  }).join('')}</ul><div class="score-axis" aria-hidden="true"><span></span><span><span>0</span><span>0.5</span><span>1</span></span></div>`
    : empty('No eligible test folds.');
}

function renderIncrement(comparisons, increment) {
  const container = byId('increment');
  if (!increment?.n_folds || !Number(increment.n_folds)) {
    container.innerHTML = empty('No paired test folds.');
    return;
  }
  const reference = new Map(comparisons.filter(row => row.model === increment.reference).map(row => [row.year, Number(row.brier)]));
  const differences = comparisons.filter(row => row.model === increment.model && reference.has(row.year))
    .map(row => ({ year: Number(row.year), delta: Number(row.brier) - reference.get(row.year) }))
    .sort((a, b) => a.year - b.year);
  const bound = Math.max(0.001, ...differences.map(row => Math.abs(row.delta)));
  container.innerHTML = `<p class="delta-summary">${signed(increment.mean)} mean change in Brier</p>
    <p class="note">${Number(increment.n_folds)} paired years · descriptive 95% interval ${signed(increment.lo)} to ${signed(increment.hi)}</p>
    <ul class="delta-list">${differences.map(({ year, delta }) => `<li><span>${year}</span><span class="delta-track" aria-hidden="true">
      <span class="delta-fill" style="left:${50 + 50 * Math.min(0, delta / bound)}%;width:${50 * Math.abs(delta / bound)}%;--bar:var(--${delta < 0 ? 'good' : 'bad'})"></span></span>
      <span class="num">${signed(delta)}</span></li>`).join('')}</ul>
    <p class="note">Negative values favor adding OpenAlex. This comparison is exploratory on the current snapshot.</p>`;
}

function calibrationChart(rows) {
  const container = byId('calibration');
  if (!rows.length) {
    container.innerHTML = empty('No predictions to calibrate.');
    return;
  }
  const width = Math.max(250, container.clientWidth);
  const height = 250, left = 42, right = width - 14, top = 24, bottom = 194;
  const x = probability => left + probability * (right - left);
  const y = rate => bottom - rate * (bottom - top);
  const ticks = [0, 0.25, 0.5, 0.75, 1];
  const axes = ticks.map(tick => `<line class="grid-line" x1="${left}" x2="${right}" y1="${y(tick)}" y2="${y(tick)}"/>
    <text text-anchor="end" x="34" y="${y(tick) + 4}">${percent.format(tick)}</text>
    <text text-anchor="middle" x="${x(tick)}" y="${bottom + 20}">${percent.format(tick)}</text>`).join('');
  const points = rows.map(row => {
    const n = Number(row.n), px = x(row.mean_probability), py = y(row.observed_rate);
    const title = `${n} field-years · predicted ${percent.format(row.mean_probability)} · observed ${percent.format(row.observed_rate)}`;
    const anchor = Number(row.mean_probability) > 0.7 ? 'end' : 'start';
    return `<circle class="chart-point" cx="${px}" cy="${py}" r="5" fill="#245ab4"><title>${title}</title></circle>
      <text x="${px + (anchor === 'end' ? -9 : 9)}" y="${py + 4}" text-anchor="${anchor}">n=${n}</text>`;
  }).join('');
  const label = `Observed rates versus mean predicted probabilities. ${rows.map(row => `${row.n} field-years: predicted ${percent.format(row.mean_probability)}, observed ${percent.format(row.observed_rate)}.`).join(' ')}`;
  container.innerHTML = svg(label, width, height, `${axes}<line class="axis-line" stroke-dasharray="4 4" x1="${left}" y1="${bottom}" x2="${right}" y2="${top}"/>
    <text x="${left}" y="14">Observed rate</text><text x="${(left + right) / 2}" y="${height - 10}" text-anchor="middle">Mean predicted probability</text>${points}`);
}

function renderFolds(folds, nulls) {
  byId('folds').innerHTML = folds.length ? `<div class="table-scroll">${table(['Year', 'Train n', 'Last train outcome', 'Test n', 'Positive rate'], folds.map(row =>
    `<tr><th scope="row">${Number(row.year)}</th><td>${Number(row.n_train)}</td><td>${Number(row.train_outcome_end)}</td><td>${Number(row.n_test)}</td><td>${percent.format(row.positive_rate)}</td></tr>`,
  ))}</div>` : empty('No eligible test folds.');
  const row = nulls[0];
  if (row?.null_mean_brier) {
    byId('nulls').textContent = `${Number(row.n_repeats)} within-year label permutations. Mean Brier ${score(row.null_mean_brier)}, with empirical 2.5–97.5% quantiles ${score(row.null_brier_q025)} to ${score(row.null_brier_q975)}. The observed full-model score was ${score(row.observed_mean_brier)}.`;
  } else byId('nulls').hidden = true;
}

async function loadDashboard() {
  const [run, manifest, panel, folds, summary, comparisons, increment, calibration, nulls] = await Promise.all([
    json('run'), json('manifest'), csv('panel'), csv('walk_forward'), csv('metric_summary'),
    csv('model_comparison'), csv('research_increment'), csv('calibration'), csv('null_summary'),
  ]);
  const synthetic = run.dataset_kind === 'synthetic';
  const observations = synthetic ? [] : await csv('source_observations');
  const years = [...new Set(panel.map(row => Number(row.year)))].sort((a, b) => a - b);
  const fields = [...new Set(panel.map(row => row.field))];
  const metadata = new Map((run.taxonomy?.domains ?? []).map(domain => [domain.id, domain]));
  const domains = [...metadata.keys(), ...fields.filter(field => !metadata.has(field))].filter(field => fields.includes(field))
    .map((id, index) => ({ ...metadata.get(id), id, label: metadata.get(id)?.label ?? id, color: colors[index % colors.length] }));
  if (!years.length) throw new Error('The panel contains no observations.');

  const vintages = observations.map(row => row.retrieved_at.slice(0, 10)).sort();
  const vintage = vintages[0] === vintages.at(-1) ? vintages[0] : `${vintages[0]} to ${vintages.at(-1)}`;
  const count = folds.reduce((sum, fold) => sum + Number(fold.n_test), 0);
  const yearRange = `${run.start_year}–${run.end_year}`;
  byId('snapshot').textContent = synthetic ? `Synthetic fixture · ${yearRange}` : `Live API snapshot · ${yearRange} · Retrieved ${vintage}`;
  byId('evidence').textContent = synthetic
    ? `${folds.length} eligible test years and ${count} field-year forecasts from the synthetic fixture.`
    : `${folds.length} eligible test years and ${count} field-year forecasts. Historical counts use current source records and topic assignments. The outcome measures GitHub engineering activity.`;
  byId('evidence').hidden = false;
  byId('summary').innerHTML = [
    ['Domain-year observations', panel.length], ['Known outcomes', run.n_labeled_rows],
    ['Unknown outcomes', panel.length - run.n_labeled_rows], ['Source-query-year observations', observations.length],
  ].map(([label, value]) => `<div><dt>${label}</dt><dd>${number.format(value)}</dd></div>`).join('');
  byId('target').textContent = `Target event: at least ${percent.format(run.target.growth_threshold)} growth in GitHub repository-query counts over ${run.target.horizon_years} calendar years, with a positive starting count.`;
  byId('trend-legend').innerHTML = domains.map(domain => `<li><span class="swatch" style="--series:${domain.color}"></span>${escapeHtml(domain.label)}</li>`).join('');
  const cards = domains.filter(domain => domain.description || domain.boundary);
  byId('domain-cards').innerHTML = cards.length ? cards.map(domain => `<article>
    <p class="kind">${escapeHtml(domain.kind)}</p><h3>${escapeHtml(domain.label)}</h3>
    <p class="note">${escapeHtml(domain.description)}</p><p class="note">${escapeHtml(domain.boundary)}</p></article>`).join('')
    : empty('Domain boundary descriptions are unavailable for this run.');
  byId('dashboard').hidden = false;
  renderCoverage(observations, domains, years);
  renderBrier(summary);
  renderIncrement(comparisons, increment[0]);
  renderFolds(folds, nulls);
  const redrawTrend = () => trendChart(panel, domains, years);
  redrawTrend();
  calibrationChart(calibration);
  byId('trend-source').addEventListener('change', redrawTrend);
  byId('trend-scale').addEventListener('change', redrawTrend);
  const chartResize = new ResizeObserver(() => {
    redrawTrend();
    calibrationChart(calibration);
  });
  chartResize.observe(byId('trend'), { box: 'border-box' });
  byId('snapshot').title = `Artifacts generated ${manifest.generated_at_utc}`;
  for (const link of document.querySelectorAll('footer [href^="data/"]')) {
    const path = link.getAttribute('href');
    if (synthetic && ['data/source_observations.csv', 'data/coverage.csv'].includes(path)) link.hidden = true;
    if (embedded && !link.hidden) {
      link.href = URL.createObjectURL(new Blob([embedded[path]], { type: path.endsWith('.csv') ? 'text/csv' : 'application/json' }));
      link.download = path.split('/').at(-1);
    }
  }
}

loadDashboard().catch(error => {
  byId('snapshot').textContent = `Could not load monitoring data. ${error.message}`;
  byId('dashboard').hidden = true;
});
