document.querySelectorAll('.btn-3d').forEach(btn => {
    btn.addEventListener('mouseover', () => {
        btn.style.boxShadow = "0 12px 32px rgba(250, 105, 60, 0.43)";
    });
    btn.addEventListener('mouseout', () => {
        btn.style.boxShadow = "0 6px 18px rgba(250, 105, 60, 0.27), 0 1px 0 #fff inset";
    });
});

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/service-worker.js');
}