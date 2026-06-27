/**
 * CV Agent JWT bridge for the career interview UI.
 * Re-installable — React Strict Mode unmount/remount must call install again.
 */
(function () {
  var nativeFetch = window.fetch.bind(window);

  function readConfig() {
    var params = new URLSearchParams(window.location.search);
    var cfg = window.__CV_INTERVIEW_CONFIG__ || {};
    return {
      token: params.get("token") || cfg.token || "",
      apiBase: (params.get("api") || cfg.api || "").replace(/\/+$/, ""),
    };
  }

  var API_PREFIXES = [
    "/start",
    "/session/",
    "/results/",
    "/answer/",
    "/transcribe",
    "/speak",
    "/recruiter/",
  ];

  function isApiPath(url) {
    if (!url.startsWith("/")) return false;
    if (url.startsWith("/interview/")) return false;
    return API_PREFIXES.some(function (prefix) {
      return url === prefix || url.startsWith(prefix);
    });
  }

  function resolveUrl(url, apiBase) {
    if (!apiBase || !isApiPath(url)) return url;
    return apiBase + url;
  }

  function installAuthBridge() {
    var cfg = readConfig();

    window.fetch = function (input, init) {
      init = init || {};
      var url =
        typeof input === "string"
          ? input
          : input instanceof Request
            ? input.url
            : String(input);
      var resolved = resolveUrl(url, cfg.apiBase);
      var attachAuth =
        !!cfg.token && (isApiPath(url) || (!cfg.apiBase && url.startsWith("/")));

      if (attachAuth) {
        var headers = new Headers(
          init.headers || (input instanceof Request ? input.headers : undefined),
        );
        if (!headers.has("Authorization")) {
          headers.set("Authorization", "Bearer " + cfg.token);
        }
        init = Object.assign({}, init, { headers: headers });
      }

      if (typeof input === "string") {
        return nativeFetch(resolved, init);
      }
      if (input instanceof Request && resolved !== url) {
        return nativeFetch(new Request(resolved, input), init);
      }
      return nativeFetch(input, init);
    };
  }

  window.__CV_INTERVIEW_AUTH_UNINSTALL__ = function () {
    window.fetch = nativeFetch;
    delete window.__CV_INTERVIEW_AUTH_UNINSTALL__;
    delete window.__CV_INTERVIEW_INSTALL_AUTH__;
  };

  window.__CV_INTERVIEW_INSTALL_AUTH__ = installAuthBridge;
  installAuthBridge();
})();
