// FoodVendor prototype — shared helpers (no framework, kept deliberately simple)

function fvQty(el, delta) {
  const input = el.parentElement.querySelector('[data-qty-input]');
  let val = parseInt(input.value || '1', 10) + delta;
  if (val < 1) val = 1;
  input.value = val;
  if (input.dataset.priceEach) {
    const lineTotalEl = document.querySelector(input.dataset.lineTotalTarget);
    if (lineTotalEl) {
      const total = (parseFloat(input.dataset.priceEach) * val).toLocaleString('en-NG', {minimumFractionDigits: 2, maximumFractionDigits: 2});
      lineTotalEl.textContent = '₦' + total;
    }
  }
}

function fvCopy(text, btn) {
  navigator.clipboard?.writeText(text);
  if (!btn) return;
  const original = btn.textContent;
  btn.textContent = 'Copied';
  setTimeout(() => { btn.textContent = original; }, 1400);
}

function fvToggle(id) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle('hidden');
}