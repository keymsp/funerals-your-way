/* Mobile navigation: panel toggle + accordion groups */
(function () {
  var toggle = document.getElementById('navToggle');
  var panel = document.getElementById('mobileNav');
  if (toggle && panel) {
    toggle.addEventListener('click', function () {
      var open = panel.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      toggle.textContent = open ? '✕' : '☰';
    });
  }
  document.querySelectorAll('.mobile-nav .m-group > button').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var group = btn.parentElement;
      var open = group.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      var plus = btn.querySelector('span');
      if (plus) plus.textContent = open ? '–' : '＋';
    });
  });
  // Close mobile panel when a link is tapped
  document.querySelectorAll('.mobile-nav a').forEach(function (a) {
    a.addEventListener('click', function () {
      panel.classList.remove('open');
      if (toggle) { toggle.setAttribute('aria-expanded', 'false'); toggle.textContent = '☰'; }
    });
  });
})();
