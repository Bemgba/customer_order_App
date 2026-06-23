<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>FoodVendor — My Orders</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="assets/tw-config.js"></script>
<link href="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.min.css" rel="stylesheet" type="text/css" />
<link rel="stylesheet" href="assets/styles.css" />
<script src="assets/app.js" defer></script>
</head>
<body class="font-body text-ink-900 bg-sand-50 min-h-screen">

<header class="sticky top-0 z-30 bg-sand-50/95 backdrop-blur border-b border-ink-100">
  <div class="max-w-3xl mx-auto px-4 md:px-8 h-16 flex items-center justify-between">
    <a href="menu.html" class="font-display font-bold text-xl text-palm-800 tracking-tight">FoodVendor<span class="text-leaf-600">.</span></a>
    <a href="account-settings.html" class="text-sm font-semibold text-ink-600 hover:text-ink-900">Chiamaka O.</a>
  </div>
</header>

<main class="max-w-3xl mx-auto px-4 md:px-8 py-10">
  <h1 class="font-display font-bold text-3xl mb-1">My Orders</h1>
  <p class="text-ink-500 mb-8">Your order history with Port Harcourt · GRA Branch</p>

  <div class="space-y-5">

    <!-- ============ OUT FOR DELIVERY — dual confirmation ============ -->
    <article class="bg-white rounded-2xl shadow-card border border-violet-200 overflow-hidden">
      <div class="flex items-center justify-between flex-wrap gap-3 p-5 border-b border-ink-100">
        <div>
          <p class="font-mono font-bold text-sm">ORD-3F7A2B1C9D</p>
          <p class="text-xs text-ink-400 mt-0.5">Placed today, 12:40 PM</p>
        </div>
        <div class="twin-rail">
          <span class="rail-pill fill-outfordel">Out for Delivery</span>
          <svg class="rail-link" viewBox="0 0 20 14" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="1" y="3" width="8" height="8" rx="4" stroke="#B3ADA0" stroke-width="1.6"/><rect x="11" y="3" width="8" height="8" rx="4" stroke="#B3ADA0" stroke-width="1.6"/></svg>
          <span class="rail-pill fill-pending">Pending</span>
        </div>
      </div>
      <div class="p-5">
        <p class="text-sm text-ink-600">Native Jollof Rice & Chicken, Beef Suya Platter, Fried Plantain x3</p>
        <p class="font-mono font-bold text-jollof-700 mt-1">₦13,300.00</p>
      </div>

      <!-- COD alert -->
      <div class="mx-5 mb-4 bg-jollof-50 border border-jollof-200 rounded-xl p-4 flex items-start gap-3">
        <span class="w-2 h-2 rounded-full bg-jollof-600 pulse-dot mt-1.5 shrink-0"></span>
        <p class="text-sm text-jollof-900"><span class="font-bold">Have ₦13,300.00 cash ready</span> — this is a Cash on Delivery order.</p>
      </div>

      <!-- DUAL CONFIRMATION -->
      <div class="mx-5 mb-5 bg-violet-50 border border-violet-200 rounded-xl p-5">
        <p class="text-sm font-bold text-violet-900 mb-4">Confirm your delivery</p>
        <div class="grid grid-cols-2 gap-4 mb-4">
          <div class="flex items-center gap-2.5">
            <span class="w-7 h-7 rounded-full bg-violet-600 flex items-center justify-center shrink-0">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5"/></svg>
            </span>
            <div><p class="text-xs font-semibold text-violet-900">Dispatcher</p><p class="text-xs text-violet-600">Confirmed, 1:55 PM</p></div>
          </div>
          <div class="flex items-center gap-2.5">
            <span class="w-7 h-7 rounded-full border-2 border-violet-300 bg-white shrink-0"></span>
            <div><p class="text-xs font-semibold text-violet-900">You</p><p class="text-xs text-violet-500">Awaiting your confirmation</p></div>
          </div>
        </div>
        <p class="text-xs text-violet-700 mb-3">Order moves to "Delivered" once both sides confirm. Only confirm after you've received your food.</p>
        <button class="btn w-full bg-violet-600 hover:bg-violet-700 border-none text-white rounded-xl font-semibold normal-case">Confirm I received my order</button>
      </div>
    </article>

    <!-- ============ PREPARING ============ -->
    <article class="bg-white rounded-2xl shadow-card border border-ink-100 overflow-hidden">
      <div class="flex items-center justify-between flex-wrap gap-3 p-5 border-b border-ink-100">
        <div>
          <p class="font-mono font-bold text-sm">ORD-A19DE44210</p>
          <p class="text-xs text-ink-400 mt-0.5">Placed yesterday, 7:10 PM</p>
        </div>
        <div class="twin-rail">
          <span class="rail-pill fill-preparing">Preparing</span>
          <svg class="rail-link" viewBox="0 0 20 14" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="1" y="3" width="8" height="8" rx="4" stroke="#B3ADA0" stroke-width="1.6"/><rect x="11" y="3" width="8" height="8" rx="4" stroke="#B3ADA0" stroke-width="1.6"/></svg>
          <span class="rail-pill fill-paid">Paid</span>
        </div>
      </div>
      <div class="p-5 flex items-center justify-between">
        <div>
          <p class="text-sm text-ink-600">Egusi Soup & Pounded Yam, Chapman x1</p>
          <p class="font-mono font-bold text-jollof-700 mt-1">₦7,200.00</p>
        </div>
        <a href="track.html" class="text-sm font-semibold text-leaf-700 hover:text-leaf-800">Track →</a>
      </div>
    </article>

    <!-- ============ DELIVERED ============ -->
    <article class="bg-white rounded-2xl shadow-card border border-ink-100 overflow-hidden opacity-90">
      <div class="flex items-center justify-between flex-wrap gap-3 p-5 border-b border-ink-100">
        <div>
          <p class="font-mono font-bold text-sm">ORD-7C2EB098F1</p>
          <p class="text-xs text-ink-400 mt-0.5">Delivered Jun 18, 1:32 PM</p>
        </div>
        <div class="twin-rail">
          <span class="rail-pill fill-delivered">Delivered</span>
          <svg class="rail-link" viewBox="0 0 20 14" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="1" y="3" width="8" height="8" rx="4" stroke="#B3ADA0" stroke-width="1.6"/><rect x="11" y="3" width="8" height="8" rx="4" stroke="#B3ADA0" stroke-width="1.6"/></svg>
          <span class="rail-pill fill-paid">Paid</span>
        </div>
      </div>
      <div class="p-5 flex items-center justify-between">
        <div>
          <p class="text-sm text-ink-600">Banga Soup & Starch x1</p>
          <p class="font-mono font-bold text-jollof-700 mt-1">₦5,000.00</p>
        </div>
        <button class="text-sm font-semibold text-ink-500 hover:text-ink-800">Reorder</button>
      </div>
    </article>

    <!-- ============ CANCELLED ============ -->
    <article class="bg-white rounded-2xl shadow-card border border-ink-100 overflow-hidden opacity-75">
      <div class="flex items-center justify-between flex-wrap gap-3 p-5">
        <div>
          <p class="font-mono font-bold text-sm">ORD-115BB6CC02</p>
          <p class="text-xs text-ink-400 mt-0.5">Cancelled Jun 15, 6:02 PM</p>
        </div>
        <div class="twin-rail">
          <span class="rail-pill fill-cancelled">Cancelled</span>
          <svg class="rail-link" viewBox="0 0 20 14" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="1" y="3" width="8" height="8" rx="4" stroke="#B3ADA0" stroke-width="1.6"/><rect x="11" y="3" width="8" height="8" rx="4" stroke="#B3ADA0" stroke-width="1.6"/></svg>
          <span class="rail-pill fill-refunded">Refunded</span>
        </div>
      </div>
    </article>

  </div>
</main>

</body>
</html>