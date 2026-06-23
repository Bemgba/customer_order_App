<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>FoodVendor — Track Order</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="assets/tw-config.js"></script>
<link href="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.min.css" rel="stylesheet" type="text/css" />
<link rel="stylesheet" href="assets/styles.css" />
<script src="assets/app.js" defer></script>
<style>
  .steps .step:before { background-color: #E8E6E1 !important; }
  .steps .step-leaf:before, .steps .step-leaf:after { background-color: #257F4D !important; color: #fff !important; }
</style>
</head>
<body class="font-body text-ink-900 bg-sand-50 min-h-screen">

<header class="bg-sand-50 border-b border-ink-100">
  <div class="max-w-3xl mx-auto px-4 md:px-8 h-16 flex items-center">
    <a href="menu.html" class="font-display font-bold text-xl text-palm-800 tracking-tight">FoodVendor<span class="text-leaf-600">.</span></a>
  </div>
</header>

<main class="max-w-3xl mx-auto px-4 md:px-8 py-12">

  <!-- SEARCH -->
  <div class="bg-white rounded-2xl shadow-card border border-ink-100 p-6 md:p-8 text-center">
    <h1 class="font-display font-bold text-2xl mb-1">Track your order</h1>
    <p class="text-ink-500 text-sm mb-6">No account needed — just your order reference.</p>
    <form class="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
      <input type="text" value="ORD-3F7A2B1C9D" placeholder="ORD-XXXXXXXXXX" class="input input-bordered rounded-xl border-ink-200 focus:border-leaf-400 focus:outline-none font-mono flex-1" />
      <button class="btn bg-leaf-600 hover:bg-leaf-700 border-none text-white rounded-xl font-semibold normal-case px-6">Track Order</button>
    </form>
  </div>

  <!-- RESULT -->
  <div class="bg-white rounded-2xl shadow-card border border-ink-100 p-6 md:p-8 mt-6">
    <div class="flex items-center justify-between flex-wrap gap-3 mb-8">
      <div>
        <p class="font-mono font-bold text-lg">ORD-3F7A2B1C9D</p>
        <p class="text-xs text-ink-400 mt-0.5">Estimated arrival: 1:15 – 1:30 PM</p>
      </div>
      <div class="twin-rail">
        <span class="rail-pill fill-outfordel">Out for Delivery</span>
        <svg class="rail-link" viewBox="0 0 20 14" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="1" y="3" width="8" height="8" rx="4" stroke="#B3ADA0" stroke-width="1.6"/><rect x="11" y="3" width="8" height="8" rx="4" stroke="#B3ADA0" stroke-width="1.6"/></svg>
        <span class="rail-pill fill-pending">Pending</span>
      </div>
    </div>

    <!-- step progress -->
    <ul class="steps steps-vertical sm:steps-horizontal w-full text-xs">
      <li class="step step-leaf font-semibold">Pending</li>
      <li class="step step-leaf font-semibold">Confirmed</li>
      <li class="step step-leaf font-semibold">Preparing</li>
      <li class="step step-leaf font-semibold text-violet-700">Out for Delivery</li>
      <li class="step text-ink-400">Delivered</li>
    </ul>

    <div class="mt-8 bg-sand-50 rounded-xl p-5 flex items-start gap-3">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-leaf-600 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15.59 14.37a6 6 0 0 1-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 0 0 6.16-12.12A14.98 14.98 0 0 0 9.631 8.41m5.96 5.96a14.926 14.926 0 0 1-5.841 2.58m-.119-8.54a6 6 0 0 0-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 0 0-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 0 1-2.448-2.448 14.9 14.9 0 0 1 .06-.312m-2.24 2.39a4.493 4.493 0 0 0-1.757 4.306 4.493 4.493 0 0 0 4.306-1.758M16.5 9a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0Z"/></svg>
      <p class="text-sm text-ink-600">Your rider, <span class="font-semibold text-ink-900">Emeka</span>, is on the way from GRA Branch. He'll call you on arrival.</p>
    </div>
  </div>

</main>

</body>
</html>