const money = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });

async function loadDashboard() {
  const status = document.querySelector('#status');
  try {
    const [healthResponse, dashboardResponse] = await Promise.all([
      fetch('/health'),
      fetch('/api/analytics/dashboard?days=30'),
    ]);
    if (!healthResponse.ok || !dashboardResponse.ok) throw new Error('service unavailable');
    const health = await healthResponse.json();
    const data = await dashboardResponse.json();

    status.classList.add('ok');
    status.lastChild.textContent = ` All systems operational · ${Object.keys(health.dependencies).length} data services`;
    document.querySelector('#views').textContent = data.funnel.product_views.toLocaleString();
    document.querySelector('#carts').textContent = data.funnel.add_to_carts.toLocaleString();
    document.querySelector('#purchases').textContent = data.funnel.purchases.toLocaleString();
    document.querySelector('#view-rate').textContent = `${data.funnel.view_to_cart_rate}% of views`;
    document.querySelector('#purchase-rate').textContent = `${data.funnel.cart_to_purchase_rate}% of carts`;
    document.querySelector('#cache').textContent = `CACHE ${data.funnel.cache.toUpperCase()}`;

    const totalRevenue = data.revenue.reduce((sum, point) => sum + point.revenue, 0);
    document.querySelector('#revenue').textContent = money.format(totalRevenue);
    renderChart(data.revenue);
    renderProducts(data.top_products);
    document.querySelector('#updated').textContent = `Updated ${new Date().toLocaleTimeString()}`;
  } catch (error) {
    status.lastChild.textContent = ' Start the data services with docker compose up --build';
    document.querySelector('#chart').innerHTML = '<p class="empty">Dashboard data appears when the API is running.</p>';
  }
}

function renderChart(points) {
  const chart = document.querySelector('#chart');
  if (!points.length) return;
  const max = Math.max(...points.map((point) => point.revenue));
  chart.innerHTML = points.map((point) => {
    const height = Math.max(4, point.revenue / max * 100);
    const label = new Date(`${point.day}T00:00:00`).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    return `<div class="bar-wrap" title="${label}: ${money.format(point.revenue)}"><div class="bar" style="height:${height}%"></div><small>${label}</small></div>`;
  }).join('');
}

function renderProducts(products) {
  const list = document.querySelector('#products');
  if (!products.length) return;
  list.innerHTML = products.map((product, index) => `
    <li><span class="rank">0${index + 1}</span><span class="product-name">${product.name}</span><span class="sales">${product.units_sold} SOLD</span></li>
  `).join('');
}

loadDashboard();

