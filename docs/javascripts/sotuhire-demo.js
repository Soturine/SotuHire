(() => {
  const counters = document.querySelectorAll("[data-sotu-count]");

  counters.forEach((counter) => {
    const target = Number(counter.getAttribute("data-sotu-count") || "0");

    if (!Number.isFinite(target) || target <= 0) {
      return;
    }

    let value = 0;
    const step = Math.max(1, Math.round(target / 18));
    const timer = window.setInterval(() => {
      value = Math.min(target, value + step);
      counter.textContent = String(value);

      if (value >= target) {
        window.clearInterval(timer);
      }
    }, 28);
  });
})();
