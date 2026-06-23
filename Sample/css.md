@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600;700&display=swap');

html { scroll-behavior: smooth; }
body { background-color: #FEFCF8; color: #1C1A16; }

::selection { background: #AFDFC0; color: #0B2218; }

/* ---------- The Link ----------
   FoodVendor's signature component: order status and payment status are
   tracked completely independently in the data model, but a manager must
   never be able to see one without the other. Every place a status shows,
   it shows as a coupled pair — two pills literally clasped by a link glyph
   — never a lone badge. */
.twin-rail { display: inline-flex; align-items: center; }
.twin-rail .rail-pill {
  padding: 0.3rem 0.7rem; font-size: 0.72rem; font-weight: 700;
  letter-spacing: .015em; border-radius: 999px; line-height: 1; white-space: nowrap;
}
.twin-rail .rail-link { width: 20px; height: 14px; margin: 0 -4px; flex-shrink: 0; position: relative; z-index: 1; }
.twin-rail.lg .rail-pill { padding: .55rem 1.1rem; font-size: .9rem; }
.twin-rail.lg .rail-link { width: 28px; height: 20px; }
.twin-rail.sm .rail-pill { padding: .18rem .5rem; font-size: .64rem; }
.twin-rail.sm .rail-link { width: 16px; height: 11px; margin: 0 -3px; }

/* status fills */
.fill-pending   { background:#FCF5E6; color:#825416; }
.fill-confirmed { background:#EFF8F1; color:#1D6840; }
.fill-preparing { background:#EAF1FD; color:#1D4ED8; }
.fill-outfordel { background:#F3EEFC; color:#6D28D9; }
.fill-delivered { background:#E7FAF3; color:#047857; }
.fill-cancelled { background:#FDEEEA; color:#B83A16; }
.fill-paid      { background:#EFF8F1; color:#1D6840; }
.fill-failed    { background:#FDEEEA; color:#B83A16; }
.fill-refunded  { background:#E5FAFB; color:#0E7490; }

/* Ankara-inspired diamond texture — used sparingly on dark surfaces only */
.pattern-ankara {
  background-image:
    linear-gradient(45deg, rgba(255,255,255,.05) 25%, transparent 25%, transparent 75%, rgba(255,255,255,.05) 75%),
    linear-gradient(45deg, rgba(255,255,255,.05) 25%, transparent 25%, transparent 75%, rgba(255,255,255,.05) 75%);
  background-size: 30px 30px;
  background-position: 0 0, 15px 15px;
}

@keyframes pulseDot { 0%,100%{opacity:1} 50%{opacity:.3} }
.pulse-dot { animation: pulseDot 1.6s ease-in-out infinite; }

.scroll-thin::-webkit-scrollbar { height: 6px; width: 6px; }
.scroll-thin::-webkit-scrollbar-thumb { background: #D1CDC4; border-radius: 999px; }
.scroll-thin::-webkit-scrollbar-track { background: transparent; }

.tap-highlight { -webkit-tap-highlight-color: transparent; }

/* card lift on hover, used for product & order cards */
.lift { transition: transform .18s ease, box-shadow .18s ease; }
.lift:hover { transform: translateY(-3px); }