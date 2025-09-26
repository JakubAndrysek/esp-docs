(function() {
  "use strict";

  function setActionsVisibility(root) {
    // Show actions only if active panel is a Wokwi panel (has data-viewer-url)
    var bar = root.querySelector('.wokwi-tabsbar');
    if (!bar) return;
    var actions = bar.querySelector('.wokwi-actions[data-wokwi-only="true"]');
    if (!actions) return;
    var active = root.querySelector('.wokwi-panel[data-active="true"]');
    var hasWokwi = !!(active && active.getAttribute('data-viewer-url'));
    actions.style.display = hasWokwi ? "" : "none";
  }

  function updateLaunchpadUrl(root, selectedBtn) {
    var launchpadBtn = root.querySelector('.wokwi-launchpad-btn');
    if (!launchpadBtn) return;

    var baseHref = launchpadBtn.getAttribute('data-base-href');
    if (!baseHref) return;

    var chip = selectedBtn.getAttribute('data-chip');
    if (chip) {
      // Add chip parameter to launchpad URL
      var separator = baseHref.includes('?') ? '&' : '?';
      var newHref = baseHref + separator + 'chip=' + encodeURIComponent(chip);
      launchpadBtn.setAttribute('href', newHref);
    } else {
      // Use base href for non-chip tabs (source code)
      launchpadBtn.setAttribute('href', baseHref);
    }
  }

  function onTabClick(e) {
    var btn = e.target.closest('.wokwi-tab');
    if (!btn) return;
    var root = btn.closest('.wokwi-tabs');
    if (!root) return;

    root.querySelectorAll('.wokwi-tab').forEach(function(b) {
      b.setAttribute('aria-selected', String(b === btn));
    });

    var id = btn.getAttribute('data-target');
    root.querySelectorAll('.wokwi-panel').forEach(function(p) {
      p.dataset.active = String(p.id === id);
    });

    // Update launchpad URL based on selected chip
    updateLaunchpadUrl(root, btn);

    setActionsVisibility(root);
  }

  function buildModal(url) {
    var modal = document.createElement('div');
    modal.className = 'wokwi-modal';
    modal.innerHTML = '' +
      '<button class="wokwi-modal__close" title="Close">✕</button>' +
      '<div class="wokwi-modal__inner">' +
      '  <iframe class="wokwi-modal__frame" allowfullscreen></iframe>' +
      '</div>';

    var frame = modal.querySelector('iframe');
    frame.src = url;

    modal.addEventListener('click', function(ev) {
      if (ev.target.classList.contains('wokwi-modal')) {
        document.body.removeChild(modal);
      }
    });

    modal.querySelector('.wokwi-modal__close').addEventListener('click', function() {
      try { document.body.removeChild(modal); } catch (_) {}
    });

    document.addEventListener('keydown', function esc(ev) {
      if (ev.key === 'Escape') {
        try { document.body.removeChild(modal); } catch (_) {}
        document.removeEventListener('keydown', esc);
      }
    });

    return modal;
  }

  function openFullscreenFrom(root) {
    var panel = root.querySelector('.wokwi-panel[data-active="true"]');
    var url = panel ? panel.getAttribute('data-viewer-url') : null;
    if (!url) {
      var iframe = root.querySelector('iframe');
      if (iframe && iframe.src) url = iframe.src;
    }
    if (!url) return;
    document.body.appendChild(buildModal(url));
  }

  function onFullscreenClick(e) {
    var fsBtn = e.target.closest('.wokwi-fullscreen-btn');
    if (!fsBtn) return;
    e.preventDefault();
    var root = fsBtn.closest('.wokwi-tabs') || fsBtn.closest('.wokwi-frame');
    if (!root) return;
    openFullscreenFrom(root);
  }

  document.addEventListener('click', onTabClick);
  document.addEventListener('click', onFullscreenClick);

  document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.wokwi-tabs').forEach(function(root) {
      setActionsVisibility(root);

      // Initialize launchpad URL for the active tab
      var activeTab = root.querySelector('.wokwi-tab[aria-selected="true"]');
      if (activeTab) {
        updateLaunchpadUrl(root, activeTab);
      }
    });
  });
})();
