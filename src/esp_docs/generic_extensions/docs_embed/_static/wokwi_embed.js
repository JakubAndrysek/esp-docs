(function() {
  "use strict";

  function setActionsVisibility(root) {
    var active = root.querySelector('.wokwi-panel[data-active="true"]');
    var hasWokwi = !!(active && active.getAttribute('data-viewer-url'));
    
    var fullscreenBtn = root.querySelector('.wokwi-fullscreen-btn[data-wokwi-only="true"]');
    if (fullscreenBtn) {
      fullscreenBtn.style.display = hasWokwi ? "" : "none";
    }
  }

  function updateLaunchpadUrl(root) {
    var launchpadBtn = root.querySelector('.wokwi-launchpad-btn');
    if (!launchpadBtn) return;

    var baseHref = launchpadBtn.getAttribute('data-base-href');
    if (baseHref) {
      launchpadBtn.setAttribute('href', baseHref);
    }
  }

  function onTabClick(e) {
    var btn = e.target.closest('.wokwi-tab');
    if (!btn) return;
    var root = btn.closest('.wokwi-tabs');
    if (!root) return;

    // Update tab selection
    root.querySelectorAll('.wokwi-tab').forEach(function(b) {
      b.setAttribute('aria-selected', String(b === btn));
    });

    // Update panel visibility
    var id = btn.getAttribute('data-target');
    root.querySelectorAll('.wokwi-panel').forEach(function(p) {
      p.dataset.active = String(p.id === id);
    });

    updateLaunchpadUrl(root);
    setActionsVisibility(root);
  }

  function buildModal(url) {
    var modal = document.createElement('div');
    modal.className = 'wokwi-modal';
    modal.innerHTML = 
      '<button class="wokwi-modal__close" title="Close">✕</button>' +
      '<div class="wokwi-modal__inner">' +
      '<iframe class="wokwi-modal__frame" allowfullscreen></iframe>' +
      '</div>';

    modal.querySelector('iframe').src = url;

    function closeModal() {
      try { 
        document.body.removeChild(modal); 
      } catch (_) {}
    }

    modal.addEventListener('click', function(ev) {
      if (ev.target.classList.contains('wokwi-modal')) {
        closeModal();
      }
    });

    modal.querySelector('.wokwi-modal__close').addEventListener('click', closeModal);

    document.addEventListener('keydown', function escHandler(ev) {
      if (ev.key === 'Escape') {
        closeModal();
        document.removeEventListener('keydown', escHandler);
      }
    });

    return modal;
  }

  function openFullscreen(root) {
    var panel = root.querySelector('.wokwi-panel[data-active="true"]');
    var url = panel ? panel.getAttribute('data-viewer-url') : null;
    
    if (!url) {
      var iframe = root.querySelector('iframe');
      if (iframe && iframe.src) url = iframe.src;
    }
    
    if (url) {
      document.body.appendChild(buildModal(url));
    }
  }

  function onFullscreenClick(e) {
    var btn = e.target.closest('.wokwi-fullscreen-btn');
    if (!btn) return;
    
    e.preventDefault();
    var root = btn.closest('.wokwi-tabs') || btn.closest('.wokwi-frame');
    if (root) {
      openFullscreen(root);
    }
  }

  // Event listeners
  document.addEventListener('click', onTabClick);
  document.addEventListener('click', onFullscreenClick);

  document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.wokwi-tabs').forEach(function(root) {
      setActionsVisibility(root);
      updateLaunchpadUrl(root);
    });
  });
})();
