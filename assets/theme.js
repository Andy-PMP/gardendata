// Light/dark theme toggle. The initial theme is set by an inline script in
// app.py's index_string before first paint; this only reports and flips it.
window.dash_clientside = Object.assign({}, window.dash_clientside, {
  garden: {
    toggleTheme: function (nClicks) {
      var root = document.documentElement;
      var theme = root.getAttribute("data-theme") === "dark" ? "dark" : "light";
      if (nClicks) {
        theme = theme === "dark" ? "light" : "dark";
        root.setAttribute("data-theme", theme);
        root.setAttribute("data-bs-theme", theme);
        try { localStorage.setItem("garden-theme", theme); } catch (e) {}
      }
      return theme;
    },
  },
});
