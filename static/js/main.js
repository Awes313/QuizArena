 /* -- QuizArena — Global JavaScript
       static/js/main.js   -- */

document.addEventListener("DOMContentLoaded", () => {

  /* Flash auto-dismiss (4 sec) */
  const fw = document.getElementById("flashWrap");
  if (fw) {
    setTimeout(() => {
      fw.style.transition = "opacity 0.5s";
      fw.style.opacity = "0";
      setTimeout(() => fw.remove(), 500);
    }, 4000);
  }

  /* Mobile hamburger */
  const ham  = document.getElementById("hamburger");
  const menu = document.getElementById("mobileMenu");
  if (ham && menu) {
    ham.addEventListener("click", () => {
      menu.classList.toggle("open");
      const icon = ham.querySelector("i");
      if (icon) icon.className = menu.classList.contains("open") ? "bi bi-x-lg" : "bi bi-list";
    });
    // Close menu when clicking a link
    menu.querySelectorAll("a").forEach(a => a.addEventListener("click", () => menu.classList.remove("open")));
  }

  /* Active nav link */
  document.querySelectorAll(".qa-nav-link, .qa-mobile-link").forEach(link => {
    if (link.href === window.location.href) link.classList.add("active");
  });

  /* Animate data-width bars (XP, category bars) */
  document.querySelectorAll("[data-width]").forEach(el => {
    const target = el.getAttribute("data-width");
    el.style.width = "0%";
    requestAnimationFrame(() => {
      setTimeout(() => {
        el.style.transition = "width 1.2s ease";
        el.style.width = target + "%";
      }, 300);
    });
  });

});
