/* DVE console: sign-in, data source connections, context, produced files,
 * production runs and the model they produce. The server keeps the sign-in
 * and the open connections; where the user stands is kept in localStorage. */
(function () {
  "use strict";

  var API = {
    session: "/api/session",
    csrfToken: "/api/csrf-token",
    login: "/api/login",
    logout: "/api/logout",
    projects: "/api/projects",
    units: "/api/units/",
    run: "/api/mdg/run",
    tasks: "/api/mdg/tasks/"
  };

  function unitVersionsUrl(unitName) {
    return API.units + encodeURIComponent(unitName) + "/versions";
  }

  function taskUrl(taskId, suffix) {
    var url = API.tasks + encodeURIComponent(taskId);
    return suffix ? url + "/" + suffix : url;
  }

  function selectionUrl(selection) {
    return (
      API.projects +
      "/" + encodeURIComponent(selection.project_id) +
      "/platforms/" + encodeURIComponent(selection.platform_id) +
      "/versions/" + encodeURIComponent(selection.version_id)
    );
  }

  /* Produced files are addressed by their selection and run id (req 5). */
  function mdgFilesUrl(selection, runId, suffix) {
    var base = selectionUrl(selection) + "/mdg-files";
    return runId ? base + "/" + encodeURIComponent(runId) + "/" + suffix : base;
  }

  /* The data sources this session must connect; `flag` is the field GET
   * /api/session reports the connection under. */
  var SOURCES = [
    {
      key: "config_mgmt_db",
      title: "Configuration Management DB",
      icon: "lucide-database",
      endpoint: "/api/data-sources/connect/config-mgmt-db",
      flag: "config_mgmt_db_connected",
      userKey: "dve.last-db-username"
    },
    {
      key: "source_code_repo",
      title: "Source Code Repository",
      icon: "lucide-file-code",
      endpoint: "/api/data-sources/connect/source-code-repo",
      flag: "source_code_repo_connected",
      userKey: "dve.last-repo-username"
    }
  ];

  // Per-card header: the product's name and logo, or the card's own title and glyph.
  var HEADERS = {
    login: { logo: true, subtitle: "Secure Access" },
    sources: { title: "Data Sources", icon: "lucide-hard-drive", subtitle: "Select a source to enter its credentials" },
    select: { title: "Project Context", icon: "lucide-network", subtitle: "Choose the project, platform and system version" },
    units: {
      title: "Software Unit Inventory",
      icon: "lucide-package",
      subtitle: "Select candidate versions, or produce with no change"
    },
    files: { title: "Model Setup Data", icon: "lucide-file-code", subtitle: "Open a previously produced file, upload one or produce a new one" },
    // The run card: the product's name over the context line and the console.
    run: { title: "Model Setup Data" },
    model: { title: "Core System Model" },
    // The graph stage: the mode's name as the title, which is the mode switch.
    graph: { title: "Software" }
  };

  // The graph stage's two pictures and the words the title shows for them.
  var GRAPH_TITLES = { sw: "Software", hw: "Hardware" };

  var PRODUCT_TITLE = "Digital System Model";

  // The stepper's stages, in order; boot and sign-in have none.
  var STAGES = ["sources", "select", "files", "units", "run", "model", "graph"];

  var VIEWS = ["boot", "login"].concat(STAGES);

  // Run states and how each reads on the run card.
  var RUN_STATES = {
    PENDING: { label: "Queued", tone: "busy" },
    STARTED: { label: "Running", tone: "busy" },
    SUCCESS: { label: "Successful", tone: "ok" },
    FAILURE: { label: "Failed", tone: "bad" },
    REVOKED: { label: "Cancelled", tone: "bad" }
  };
  var RUN_TERMINAL = { SUCCESS: true, FAILURE: true, REVOKED: true };

  var LAST_USER_KEY = "dve.last-username";
  var STATE_KEY_PREFIX = "dsm:state:";

  var state = {
    username: null,
    defaults: null,
    // Per source key: whether the server holds that connection.
    sources: {},
    selection: null,
    // The versions of the current project/platform as the database returned them.
    versions: null,
    // The saved {view, model_file} read on boot to choose the card to resume on.
    ui: null,
    // The graph stage's picture: "sw" the hierarchy tree, "hw" the networks and nodes.
    graphMode: "sw",
    // The run being tracked: {task_id, project_id, platform_id, version_id, candidates}.
    activeTask: null,
    // The last run that ended for this selection, {task_id, project_id, platform_id,
    // version_id, seen}; its console is rebuilt from the server on boot.
    lastRun: null,
    // The unit versions under evaluation, unit name to version (SRS DSM-MDG req 11).
    candidates: {},
    // The produced files of the selection, newest first; null until asked.
    files: null,
    // The produced file the model card shows, and that file once read.
    modelFile: null,
    model: null,
    view: "boot"
  };

  var el = {};

  function $(id) {
    return document.getElementById(id);
  }

  /* ---------------------------------------------------------------- http */

  // The session's CSRF token, which every state-changing request must carry in X-CSRFToken;
  // read once and kept until the server refuses it or the session ends.
  var csrfToken = null;

  function send(url, options) {
    return fetch(url, options).then(function (response) {
      if (response.status === 204) {
        return null;
      }
      return response
        .json()
        .catch(function () {
          return {};
        })
        .then(function (payload) {
          if (!response.ok) {
            var error = new Error(payload.error || "Request failed (" + response.status + ").");
            error.status = response.status;
            error.csrf = payload.csrf === true;
            throw error;
          }
          return payload;
        });
    });
  }

  // The sign-in form needs a token too, so an anonymous session is served one as well.
  function csrf() {
    if (csrfToken) {
      return Promise.resolve(csrfToken);
    }
    return send(API.csrfToken, { method: "GET", credentials: "same-origin" }).then(function (payload) {
      csrfToken = payload.csrf_token;
      return csrfToken;
    });
  }

  function request(method, url, body) {
    var options = { method: method, credentials: "same-origin", headers: {} };
    if (body !== undefined) {
      options.headers["Content-Type"] = "application/json";
      // A file goes as it is; anything else as JSON.
      options.body = body instanceof Blob ? body : JSON.stringify(body);
    }
    if (method === "GET" || method === "HEAD") {
      return send(url, options);
    }
    // A refused token, an hour-old one most often, is met with a fresh read and one retry.
    return csrf().then(function (token) {
      options.headers["X-CSRFToken"] = token;
      return send(url, options).catch(function (error) {
        if (!error.csrf) {
          throw error;
        }
        csrfToken = null;
        return csrf().then(function (fresh) {
          options.headers["X-CSRFToken"] = fresh;
          return send(url, options);
        });
      });
    });
  }

  // A 401 means the session is gone: start over at sign-in.
  function handleExpired(error) {
    if (error.status !== 401) {
      return false;
    }
    resetState();
    closeModal();
    showView("login");
    setMessage("login", "error", "Session expired. Sign in again.");
    return true;
  }

  /* --------------------------------------------------------------- views */

  function showView(name) {
    if (state.view === "units" && name !== "units") {
      unitScroll = el.unitList.scrollTop;
    }
    if (name !== state.view) {
      playCardIn();
    }
    state.view = name;
    VIEWS.forEach(function (view) {
      $("view-" + view).hidden = view !== name;
    });
    if (name === "graph") {
      renderGraphTitle();
    } else {
      renderHeader(HEADERS[name]);
    }
    renderStepper(name);
    el.card.setAttribute("data-view", name);
    el.shell.classList.toggle("shell--run", name === "run");
    el.shell.classList.toggle("shell--model", name === "model");
    el.shell.classList.toggle("shell--graph", name === "graph");
    document.body.classList.toggle("body--graph", name === "graph");
    document.body.classList.toggle("body--model", name === "model");
    document.body.classList.toggle("body--run", name === "run");
    renderSessionbar(STAGES.indexOf(name) !== -1);
    renderRunIndicator();

    var focusTarget = {
      login: el.username,
      sources: el.sourcesGrid.querySelector(".source__tile"),
      select: el.project
    }[name];
    if (focusTarget && !focusTarget.disabled) {
      focusTarget.focus();
    }
    saveUserState();
  }

  // Every change of view plays the card's entrance; a change mid-flight restarts it.
  function playCardIn() {
    playIn(el.card);
  }

  // Replays the card's entrance on an element: the same fade and rise the
  // graph stage plays when its picture changes. The class goes once the
  // animation ends: an element animating opacity stacks on its own, which
  // would hold the canvas's hover cards under the fixed search panel.
  function playIn(node) {
    node.classList.remove("card--in");
    void node.offsetWidth;
    node.classList.add("card--in");
    node.addEventListener(
      "animationend",
      function () {
        node.classList.remove("card--in");
      },
      { once: true }
    );
  }

  function renderStepper(name) {
    var current = STAGES.indexOf(name);
    el.stepper.hidden = current === -1;
    if (current === -1) {
      return;
    }
    var scoped = allConnected() && !!state.selection;
    el.stages.run.item.toggleAttribute("data-live", runIsLive());
    STAGES.forEach(function (key, index) {
      var drawn = index < current ? "done" : index === current ? "current" : "todo";
      el.stages[key].item.setAttribute("data-state", drawn);
      // Reachability: sources always, select once connected, the rest once a context is confirmed.
      var reachable =
        key === "sources" ||
        (key === "select" && allConnected()) ||
        (key === "model" || key === "graph" ? scoped && !!state.modelFile : scoped);
      el.stages[key].button.disabled = !reachable;
    });
  }

  function renderHeader(header) {
    el.title.textContent = header.title || PRODUCT_TITLE;
    el.subtitle.textContent = header.subtitle || "";
    el.subtitle.hidden = !header.subtitle;
    el.logo.hidden = !header.logo;
    el.brandIcon.hidden = !header.icon;
    if (header.icon) {
      el.brandIcon.className = "lucide " + header.icon + " brand-icon";
    }
  }

  function renderSessionbar(visible) {
    el.sessionbar.hidden = !visible;
    el.brandbar.hidden = !visible;
    if (visible) {
      el.sessionbarUser.textContent = state.username || "";
    }
  }

  /* ------------------------------------------------------------ messages */

  var MESSAGE_KINDS = {
    ok: { className: "message message--ok", icon: "lucide-circle-check" },
    info: { className: "message", icon: "lucide-network" },
    error: { className: "message message--error", icon: "lucide-triangle-alert" }
  };

  // kind: "ok", "info" or anything else for an error. Empty text clears the strip.
  function setMessage(view, kind, text) {
    var node = $(view + "-message");
    if (!node) {
      return;
    }
    var look = MESSAGE_KINDS[kind] || MESSAGE_KINDS.error;
    node.className = look.className;
    node.textContent = "";
    if (!text) {
      return;
    }
    var icon = document.createElement("i");
    icon.className = "lucide " + look.icon;
    node.appendChild(icon);
    node.appendChild(span("", text));
  }

  function setBusy(button, busy, busyLabel, restLabel) {
    button.disabled = busy;
    var label = button.querySelector(".submit__label");
    if (!label) {
      return;
    }
    label.textContent = "";
    if (busy) {
      label.appendChild(span("spinner", ""));
    }
    label.appendChild(document.createTextNode(busy ? busyLabel : restLabel));
  }

  function clearOnInput(inputs, view) {
    inputs.forEach(function (input) {
      input.addEventListener("input", function () {
        if ($(view + "-message").textContent) {
          setMessage(view, null, "");
        }
      });
    });
  }

  /* ------------------------------------------------------------- session */

  function adopt(session) {
    state.username = session.username;
    state.defaults = session.defaults;
    SOURCES.forEach(function (source) {
      state.sources[source.key] = !!session[source.flag];
    });
    var saved = loadUserState(session.username);
    state.selection = saved.selection || null;
    // A run that no longer matches the saved selection is not shown.
    state.activeTask = tracks(saved.active_task, state.selection) ? saved.active_task : null;
    state.lastRun = !state.activeTask && tracks(saved.last_run, state.selection) ? saved.last_run : null;
    runResultUnseen = !!state.lastRun && !state.lastRun.seen;
    state.ui = { view: saved.view || null, model_file: saved.model_file || null };
    state.graphMode = saved.graph_mode === "hw" ? "hw" : "sw";
    // A run in flight owns the candidates it evaluates (SRS DSM-MDG req 11).
    state.candidates = candidateMap(state.activeTask ? state.activeTask.candidates : savedCandidates(saved));
  }

  // Saved state from before several candidates were possible held one under `candidate`.
  function savedCandidates(saved) {
    return saved.candidates || (saved.candidate ? [saved.candidate] : []);
  }

  function candidateMap(list) {
    var map = {};
    (list || []).forEach(function (candidate) {
      if (candidate && candidate.unit_name && candidate.version) {
        map[candidate.unit_name] = candidate.version;
      }
    });
    return map;
  }

  // The candidates as the API takes them, in inventory order.
  function candidateList() {
    return Object.keys(state.candidates).map(function (unitName) {
      return { unit_name: unitName, version: state.candidates[unitName] };
    });
  }

  function tracks(task, selection) {
    return (
      !!task &&
      !!selection &&
      task.project_id === selection.project_id &&
      task.platform_id === selection.platform_id &&
      task.version_id === selection.version_id
    );
  }

  function resetState() {
    csrfToken = null;
    state.username = null;
    SOURCES.forEach(function (source) {
      state.sources[source.key] = false;
    });
    state.selection = null;
    state.versions = null;
    state.activeTask = null;
    state.lastRun = null;
    state.ui = null;
    candidateVersions = {};
    forgetContext();
    closeRunPoll();
  }

  /* Where the user stands, kept in the browser under their name (req 5). */
  function saveUserState() {
    if (!state.username || state.view === "boot" || state.view === "login") {
      return;
    }
    remember(
      STATE_KEY_PREFIX + state.username,
      JSON.stringify({
        selection: state.selection,
        active_task: state.activeTask,
        last_run: state.lastRun,
        view: state.view,
        model_file: state.modelFile ? state.modelFile.run_id : null,
        graph_mode: state.graphMode,
        candidates: candidateList()
      })
    );
  }

  function loadUserState(username) {
    try {
      return JSON.parse(window.localStorage.getItem(STATE_KEY_PREFIX + username)) || {};
    } catch (error) {
      return {};
    }
  }

  function allConnected() {
    return SOURCES.every(function (source) {
      return state.sources[source.key];
    });
  }

  function signOut() {
    request("POST", API.logout)
      .catch(function () {})
      .then(function () {
        resetState();
        closeModal();
        el.loginForm.reset();
        el.sourcePassword.value = "";
        restore(el.username, LAST_USER_KEY);
        showView("login");
      });
  }

  function boot() {
    request("GET", API.session)
      .then(function (session) {
        if (!session.authenticated) {
          restore(el.username, LAST_USER_KEY);
          showView("login");
          return;
        }
        adopt(session);
        ensureRunPoll();
        if (!allConnected()) {
          enterSources();
          return;
        }
        resumeContext();
      })
      .catch(function () {
        restore(el.username, LAST_USER_KEY);
        showView("login");
        setMessage("login", "error", "Unable to reach the server.");
      });
  }

  /* ------------------------------------------------------------- sources */

  function enterSources() {
    setMessage("sources", null, "");
    renderSources();
    showView("sources");
  }

  // One tile per source, rebuilt after every connect.
  function renderSources() {
    el.sourcesGrid.textContent = "";
    SOURCES.forEach(function (source) {
      var connected = !!state.sources[source.key];

      var icon = document.createElement("i");
      icon.className = "lucide " + source.icon + " source__icon";

      var tile = document.createElement("button");
      tile.type = "button";
      tile.className = "source__tile";
      tile.setAttribute("data-source", source.key);
      tile.setAttribute("aria-label", source.title + (connected ? ", connected" : ", not connected"));
      tile.appendChild(icon);
      tile.appendChild(span("source__name", source.title));
      tile.addEventListener("click", function () {
        openModal(source, tile);
      });

      var status = note("source__state", "");
      status.appendChild(span("source__dot", ""));
      status.appendChild(document.createTextNode(connected ? "Connected" : "Not connected"));

      var cell = document.createElement("div");
      cell.className = "source";
      cell.setAttribute("data-state", connected ? "on" : "off");
      cell.appendChild(tile);
      cell.appendChild(status);
      el.sourcesGrid.appendChild(cell);
    });
    el.sourcesSubmit.disabled = !allConnected();
  }

  /* ------------------------------------------------- connection details */

  // The source the modal collects details for, and the tile that opened it.
  var modalSource = null;
  var modalOpener = null;

  function openModal(source, opener) {
    modalSource = source;
    modalOpener = opener || null;
    setMessage("modal", null, "");
    el.modalIcon.className = "lucide " + source.icon + " brand-icon";
    el.modalTitle.textContent = source.title;
    el.sourceAddress.value = (state.defaults && state.defaults[source.key]) || "";
    el.sourceUsername.value = "";
    restore(el.sourceUsername, source.userKey);
    el.sourcePassword.value = "";
    setBusy(el.modalSubmit, false, "Connecting", "Connect");
    el.modal.hidden = false;
    (el.sourceUsername.value ? el.sourcePassword : el.sourceUsername).focus();
  }

  function closeModal() {
    if (el.modal.hidden) {
      return;
    }
    el.modal.hidden = true;
    el.sourcePassword.value = "";
    modalSource = null;
    if (modalOpener && document.contains(modalOpener)) {
      modalOpener.focus();
    }
    modalOpener = null;
  }

  function wireModal() {
    clearOnInput([el.sourceAddress, el.sourceUsername, el.sourcePassword], "modal");

    Array.prototype.forEach.call(el.modal.querySelectorAll("[data-modal-close]"), function (node) {
      node.addEventListener("click", closeModal);
    });

    document.addEventListener("keydown", function (event) {
      if (el.modal.hidden) {
        return;
      }
      if (event.key === "Escape") {
        closeModal();
      } else if (event.key === "Tab") {
        trapTab(event);
      }
    });

    el.modalForm.addEventListener("submit", function (event) {
      event.preventDefault();
      submitModal();
    });
  }

  // The modal is an overlay, not a <dialog>, so Tab is cycled by hand.
  function trapTab(event) {
    var focusable = el.modal.querySelectorAll("button:not(:disabled), input:not(:disabled)");
    if (!focusable.length) {
      return;
    }
    var first = focusable[0];
    var last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  function submitModal() {
    var source = modalSource;
    setMessage("modal", null, "");

    var fields = [el.sourceAddress, el.sourceUsername, el.sourcePassword];
    var blank = fields.filter(function (field) {
      return !field.value;
    })[0];
    if (blank) {
      setMessage("modal", "error", "Address, username and password are required.");
      blank.focus();
      return;
    }
    var credentials = {
      connection_address: el.sourceAddress.value,
      username: el.sourceUsername.value,
      password: el.sourcePassword.value
    };

    setBusy(el.modalSubmit, true, "Connecting", "Connect");
    request("POST", source.endpoint, credentials)
      .then(function () {
        state.sources[source.key] = true;
        if (source.key === "config_mgmt_db") {
          // A new database may not hold the saved selection.
          state.selection = null;
          forgetContext();
          saveUserState();
        } else {
          // A new repository may publish different versions.
          candidateVersions = {};
        }
        remember(source.userKey, credentials.username);
        setBusy(el.modalSubmit, false, "Connecting", "Connect");
        closeModal();
        renderSources();
        renderStepper(state.view);
        var next = allConnected()
          ? el.sourcesSubmit
          : el.sourcesGrid.querySelector('[data-source="' + source.key + '"]');
        if (next) {
          next.focus();
        }
        setMessage("sources", "ok", source.title + " connected.");
      })
      .catch(function (error) {
        setBusy(el.modalSubmit, false, "Connecting", "Connect");
        if (!handleExpired(error)) {
          setMessage("modal", "error", error.message);
          el.sourcePassword.value = "";
          el.sourcePassword.focus();
        }
      });
  }

  function wireSources() {
    el.sourcesSubmit.addEventListener("click", function () {
      if (allConnected()) {
        enterSelect();
      }
    });
  }

  /* ------------------------------------------------------------- context */

  /* Fills the pickers and puts the saved selection back; resolves true when
   * the pickers hold it. A selection that no longer resolves is dropped. */
  function fillSelect() {
    var saved = state.selection;
    return loadProjects().then(function () {
      if (!saved) {
        return false;
      }
      return restoreSelection(saved).then(function (complete) {
        if (complete) {
          return true;
        }
        state.selection = null;
        forgetContext();
        saveUserState();
        setMessage("select", "error", "The saved context is no longer available. Pick it again.");
        return false;
      });
    });
  }

  // Lands on the saved card after a refresh, as far as the selection still resolves.
  function resumeContext() {
    return fillSelect()
      .then(function (complete) {
        return complete ? resumeCard() : showView("select");
      })
      .catch(function (error) {
        if (!handleExpired(error)) {
          showView("select");
          setMessage("select", "error", error.message);
        }
      });
  }

  /* The card the record says the user was on; the produced file it names is
   * looked up in the listing rather than trusted. */
  function resumeCard() {
    var saved = state.ui || {};
    // The units stage was named "inventory" in records saved before 2026-11-01.
    if (saved.view === "inventory") {
      saved.view = "units";
    }
    if (saved.view === "sources") {
      return enterSources();
    }
    if (saved.view === "select") {
      return showView("select");
    }
    if (saved.view === "run") {
      return resumeRunOrFiles();
    }
    if (saved.model_file) {
      return loadFiles().then(function () {
        state.modelFile = fileByRun(saved.model_file);
        if (saved.view === "model" && state.modelFile) {
          return enterModel();
        }
        if (saved.view === "graph" && state.modelFile) {
          return enterGraph();
        }
        return saved.view === "units" ? enterInventory() : enterFiles();
      });
    }
    if (saved.view === "units") {
      return enterInventory();
    }
    if (saved.view === "files") {
      return enterFiles();
    }
    return resumeRunOrFiles();
  }

  // A tracked run outranks the landing card.
  function resumeRunOrFiles() {
    return state.activeTask || state.lastRun ? enterRunConsole() : enterFiles();
  }

  function fileByRun(runId) {
    var files = state.files || [];
    for (var i = 0; i < files.length; i++) {
      if (files[i].run_id === runId) {
        return files[i];
      }
    }
    return null;
  }

  // Stepping back to the pickers, refilled with the saved selection.
  function enterSelect() {
    return fillSelect()
      .then(function () {
        showView("select");
      })
      .catch(function (error) {
        if (!handleExpired(error)) {
          showView("select");
          setMessage("select", "error", error.message);
        }
      });
  }

  function fill(select, items, valueKey, textKey, placeholder) {
    select.textContent = "";
    select.appendChild(option("", placeholder));
    items.forEach(function (item) {
      select.appendChild(option(item[valueKey], item[textKey]));
    });
    select.value = "";
  }

  function setPickerEnabled(picker, select, enabled) {
    select.disabled = !enabled;
    picker.classList.toggle("picker--disabled", !enabled);
  }

  function loadProjects() {
    setMessage("select", null, "");
    return request("GET", API.projects).then(function (payload) {
      fill(el.project, payload.projects, "project_id", "name", "Select project");
      clearPlatform();
      return payload.projects;
    });
  }

  function loadPlatforms(projectId) {
    return request("GET", API.projects + "/" + encodeURIComponent(projectId) + "/platforms").then(
      function (payload) {
        fill(el.platform, payload.platforms, "platform_id", "name", "Select platform");
        setPickerEnabled(el.pickerPlatform, el.platform, true);
        return payload.platforms;
      }
    );
  }

  function loadVersions(projectId, platformId) {
    return request(
      "GET",
      API.projects +
        "/" + encodeURIComponent(projectId) +
        "/platforms/" + encodeURIComponent(platformId) +
        "/versions"
    ).then(function (payload) {
      state.versions = payload.versions;
      // The effective version is marked as current, the CMDB's own word for it.
      var versions = payload.versions.map(function (version) {
        return {
          version_id: version.version_id,
          label: version.is_effective ? version.label + "  ·  current" : version.label
        };
      });
      fill(el.version, versions, "version_id", "label", "Select version");
      setPickerEnabled(el.pickerVersion, el.version, true);
      return payload.versions;
    });
  }

  function clearPlatform() {
    fill(el.platform, [], "platform_id", "name", "Select platform");
    setPickerEnabled(el.pickerPlatform, el.platform, false);
    clearVersion();
  }

  function clearVersion() {
    fill(el.version, [], "version_id", "label", "Select version");
    setPickerEnabled(el.pickerVersion, el.version, false);
    syncSelectSubmit();
  }

  // Replays a saved selection through the cascade; false if any part is gone.
  function restoreSelection(selection) {
    if (!hasOption(el.project, selection.project_id)) {
      return Promise.resolve(false);
    }
    el.project.value = selection.project_id;
    return loadPlatforms(selection.project_id)
      .then(function () {
        if (!hasOption(el.platform, selection.platform_id)) {
          return false;
        }
        el.platform.value = selection.platform_id;
        return loadVersions(selection.project_id, selection.platform_id).then(function () {
          if (!hasOption(el.version, selection.version_id)) {
            return false;
          }
          el.version.value = selection.version_id;
          return true;
        });
      })
      .then(function (complete) {
        syncSelectSubmit();
        return complete;
      });
  }

  function hasOption(select, value) {
    for (var i = 0; i < select.options.length; i++) {
      if (select.options[i].value === value) {
        return true;
      }
    }
    return false;
  }

  function syncSelectSubmit() {
    el.selectSubmit.disabled = !(el.project.value && el.platform.value && el.version.value);
  }

  /* ----------------------------------------------------------- inventory */

  /* The Software Unit Version Inventory of the confirmed context (SRS DSM-MDG req 10). */

  // Every unit the database returned; the filter narrows what is drawn.
  var allUnits = null;
  // The list's scroll position when the card was last left.
  var unitScroll = 0;

  function enterInventory() {
    setMessage("units", null, "");
    renderUnits(allUnits);
    showView("units");
    el.unitList.scrollTop = unitScroll;
    return loadUnits()
      .then(function (units) {
        dropStrayCandidates();
        drawUnits();
        el.unitList.scrollTop = unitScroll;
      })
      .catch(function (error) {
        if (handleExpired(error)) {
          return;
        }
        renderUnits([]);
        setMessage("units", "error", error.message);
      });
  }

  function forgetInventory() {
    allUnits = null;
    unitScroll = 0;
    el.unitFilter.value = "";
  }

  // Everything that described one selection, dropped when the context changes.
  function forgetContext() {
    state.files = null;
    state.modelFile = null;
    state.model = null;
    state.candidates = {};
    forgetInventory();
    forgetFinishedRun();
  }

  // A finished run's console belongs to the selection it ran for.
  function forgetFinishedRun() {
    if (state.activeTask) {
      return;
    }
    runResultUnseen = false;
    state.lastRun = null;
    if (runState !== null) {
      resetConsole();
      setRunState(null, null);
    }
  }

  function loadUnits() {
    return request("GET", selectionUrl(state.selection) + "/units").then(function (payload) {
      renderUnits(payload.units);
      return payload.units;
    });
  }

  // A context cell shows its value; its tooltip names key and full value, so a
  // value cut by the ellipsis is still readable on hover.
  function fillContext(valueNode, text) {
    valueNode.textContent = text;
    var cell = valueNode.parentNode;
    var key = cell.querySelector(".context__key");
    cell.title = key ? key.textContent + ": " + text : text;
  }

  // units: null while in flight, [] for none recorded, otherwise the rows.
  function renderUnits(units) {
    allUnits = units;
    drawUnits();
  }

  function drawUnits() {
    el.unitList.textContent = "";

    if (allUnits === null) {
      el.unitCount.textContent = "";
      el.unitFilter.disabled = true;
      el.unitList.appendChild(emptyBlock("busy", null, "Reading inventory"));
      return;
    }

    el.unitFilter.disabled = !allUnits.length;

    var query = el.unitFilter.value.trim().toLowerCase();
    var shown = query
      ? allUnits.filter(function (unit) {
          return unit.unit_name.toLowerCase().indexOf(query) !== -1;
        })
      : allUnits;

    el.unitCount.textContent = !allUnits.length
      ? ""
      : query
      ? shown.length + " / " + allUnits.length
      : String(allUnits.length);

    if (!allUnits.length) {
      el.unitList.appendChild(
        emptyBlock("idle", "lucide-package", "Nothing here yet", "No software units recorded for this version.")
      );
      return;
    }

    if (!shown.length) {
      el.unitList.appendChild(
        emptyBlock("idle", "lucide-search", "No units match", "Nothing in this inventory matches that filter.")
      );
      return;
    }

    shown.forEach(function (unit) {
      // Candidates are overlaid at draw time, so allUnits stays the database's answer.
      var row = document.createElement("div");
      row.className = "units__row";
      row.setAttribute("data-unit", unit.unit_name);
      row.appendChild(span("units__name", unit.unit_name));
      if (candidateVersionOf(unit.unit_name) || unit.is_candidate) {
        row.appendChild(span("units__badge", "Candidate"));
      }
      row.appendChild(rowPicker(unit));
      el.unitList.appendChild(row);
      paintRowPicker(unit.unit_name);
    });
    summarizeCandidates();
  }

  function candidateVersionOf(unitName) {
    return state.candidates[unitName] || null;
  }

  /* ------------------------------------------------------- candidates */

  /* The unit versions being evaluated for installation, chosen per row
   * (SRS DSM-MDG req 11). The versions come from the source repository. */

  // Versions per unit as the repository last reported them; null when the request
  // failed. Read only when a row's dropdown is opened: each read is a git call.
  var candidateVersions = {};
  // The reads in flight, by unit name.
  var versionReads = {};

  function baselineVersion(unitName) {
    var row = unitRow(unitName);
    return row ? row.version : null;
  }

  function unitRow(unitName) {
    var units = allUnits || [];
    for (var i = 0; i < units.length; i++) {
      if (units[i].unit_name === unitName) {
        return units[i];
      }
    }
    return null;
  }

  // Candidates naming units outside this inventory are dropped once it has arrived.
  function dropStrayCandidates() {
    var dropped = false;
    Object.keys(state.candidates).forEach(function (unitName) {
      if (!unitRow(unitName)) {
        delete state.candidates[unitName];
        dropped = true;
      }
    });
    if (dropped) {
      saveUserState();
    }
  }

  function option(value, label) {
    var node = document.createElement("option");
    node.value = value;
    node.textContent = label;
    return node;
  }

  function setCandidateNote(text) {
    el.candidateNote.textContent = text;
  }

  // The note says how many units are at candidate versions.
  function summarizeCandidates() {
    var count = Object.keys(state.candidates).length;
    setCandidateNote(
      !count ? "" : count === 1 ? "1 unit at a candidate version." : count + " units at candidate versions."
    );
  }

  // The row's version control: the version and an edit icon until the unit's
  // versions are read; a native select holding them from then on.
  function rowPicker(unit) {
    var host = document.createElement("div");
    host.className = "vedit";
    host.setAttribute("data-unit", unit.unit_name);
    return host;
  }

  function unitRowNode(unitName) {
    var rows = el.unitList.querySelectorAll(".units__row");
    for (var i = 0; i < rows.length; i++) {
      if (rows[i].getAttribute("data-unit") === unitName) {
        return rows[i];
      }
    }
    return null;
  }

  // Rebuilds the row's control from what is known: the edit icon (spinning while
  // the read runs, red after a failure) or the select with the versions read.
  function paintRowPicker(unitName, focusSelect) {
    var row = unitRowNode(unitName);
    if (!row) {
      return;
    }
    var host = row.querySelector(".vedit");
    var versions = candidateVersions[unitName];
    host.textContent = "";
    host.classList.toggle("vedit--loading", !!versionReads[unitName]);
    host.classList.toggle("vedit--failed", versions === null);
    host.title = versions === null ? "The published versions of " + unitName + " could not be read. Click to retry." : "";

    if (!Array.isArray(versions)) {
      host.appendChild(span("vedit__value", candidateVersionOf(unitName) || baselineVersion(unitName)));
      var button = document.createElement("button");
      button.type = "button";
      button.className = "vedit__button";
      button.setAttribute("aria-label", "Choose a version for " + unitName);
      var pencil = document.createElement("i");
      pencil.className = "lucide lucide-pencil";
      button.appendChild(pencil);
      var spinner = span("spinner vedit__spinner", "");
      spinner.setAttribute("aria-label", "Reading published versions");
      button.appendChild(spinner);
      button.addEventListener("click", function () {
        readVersions(unitName);
      });
      host.appendChild(button);
      return;
    }

    var picker = document.createElement("div");
    picker.className = "picker picker--inline";
    var control = document.createElement("div");
    control.className = "picker__control";
    var select = document.createElement("select");
    select.setAttribute("aria-label", "Version of " + unitName);
    var baseline = baselineVersion(unitName);
    var chosen = candidateVersionOf(unitName);
    // Choosing the inventory's own version is how a candidate is taken back.
    select.appendChild(option(baseline, baseline));
    versions.forEach(function (version) {
      if (version !== baseline) {
        select.appendChild(option(version, version));
      }
    });
    // A chosen candidate the repository no longer publishes stays listed.
    if (chosen && !hasOption(select, chosen)) {
      select.appendChild(option(chosen, chosen));
    }
    select.value = chosen || baseline;
    select.addEventListener("change", function () {
      onRowVersionChange(unitName, select.value);
    });
    var chevron = document.createElement("i");
    chevron.className = "lucide lucide-chevron-down";
    control.appendChild(select);
    control.appendChild(chevron);
    picker.appendChild(control);
    host.appendChild(picker);

    var empty = !versions.length && !chosen;
    setPickerEnabled(picker, select, !empty);
    host.title = empty ? "The source repository publishes no versions for " + unitName + "." : "";
    if (focusSelect && !empty) {
      select.focus();
    }
  }

  // Reads a unit's published versions once, painting its row before and after.
  function readVersions(unitName) {
    if (versionReads[unitName]) {
      return versionReads[unitName];
    }
    // A failed read reports in the card's message strip, like any other error.
    setMessage("units", null, "");
    versionReads[unitName] = request("GET", unitVersionsUrl(unitName))
      .then(function (payload) {
        candidateVersions[unitName] = payload.versions || [];
      })
      .catch(function (error) {
        if (!handleExpired(error)) {
          candidateVersions[unitName] = null;
          setMessage("units", "error", error.message);
        }
      })
      .then(function () {
        delete versionReads[unitName];
        paintRowPicker(unitName, true);
        return candidateVersions[unitName];
      });
    paintRowPicker(unitName);
    return versionReads[unitName];
  }

  // The row's version was changed: the inventory's own version takes the candidate back.
  function onRowVersionChange(unitName, version) {
    if (!version || version === baselineVersion(unitName)) {
      delete state.candidates[unitName];
    } else {
      state.candidates[unitName] = version;
    }
    var row = unitRowNode(unitName);
    if (row) {
      var badge = row.querySelector(".units__badge");
      var unit = unitRow(unitName);
      var marked = !!candidateVersionOf(unitName) || !!(unit && unit.is_candidate);
      if (marked && !badge) {
        row.insertBefore(span("units__badge", "Candidate"), row.querySelector(".vedit"));
      } else if (!marked && badge) {
        row.removeChild(badge);
      }
    }
    summarizeCandidates();
    saveUserState();
  }

  /* ----------------------------------------------------------------- run */

  /* Model Setup Data production (req 6, 8): submit the run, then poll its
   * state and new log lines every RUN_POLL_MS until a terminal state. */
  var RUN_POLL_MS = 1000;
  // Consecutive failed polls tolerated before the card gives up.
  var POLL_MAX_CONSECUTIVE_FAILURES = 5;
  var runPollTaskId = null;
  var runPollTimer = null;
  // The run's state as the last poll said it.
  var runState = null;
  var runPollInFlight = false;
  var runPollFails = 0;
  // The status the card last drew, serialized, so unchanged status is not redrawn.
  var runPollLastStatus = null;
  // The index of the last line the console holds; null means replay from the top.
  var runPollLastId = null;
  // The last percent shown, for the indicator on other views.
  var runPercent = null;
  // A run ended while another view was showing, and its console has not been opened since.
  var runResultUnseen = false;
  // Elapsed seconds as the last poll measured them, and when (performance clock) they were measured.
  var runElapsedBase = null;
  var runElapsedAt = 0;
  var runElapsedTimer = null;
  // The cursor blinking at the log's end while the run goes.
  var consoleCursor = null;

  // The run card's context line: the selection as the pickers name it.
  function renderRunContext() {
    var version = selectedVersion();
    fillContext(el.runProject, selectedText(el.project));
    fillContext(el.runPlatform, selectedText(el.platform));
    fillContext(el.runVersion, version ? version.label : selectedText(el.version));
    el.runCurrent.hidden = !(version && version.is_effective);
  }

  function selectedText(select) {
    var chosen = select.options[select.selectedIndex];
    return chosen ? chosen.textContent : "";
  }

  function selectedVersion() {
    var id = el.version.value;
    var versions = state.versions || [];
    for (var i = 0; i < versions.length; i++) {
      if (versions[i].version_id === id) {
        return versions[i];
      }
    }
    return null;
  }

  // The Produce step: the tracked run's console, or the inventory that starts one.
  // The Produce step: the tracked run's console, the last finished run's console
  // while this selection holds, or the inventory that starts the first run.
  function enterProduce() {
    var finished = !!state.lastRun || (!!runState && RUN_TERMINAL[runState]);
    return state.activeTask || finished ? enterRunConsole() : enterInventory();
  }

  function enterFiles() {
    setMessage("files", null, "");
    showView("files");
    loadFiles();
  }

  function enterRunConsole() {
    renderRunContext();
    if (state.activeTask || state.lastRun) {
      // A poll already following or rebuilding this run keeps its console; otherwise one starts.
      ensureRunPoll();
    } else if (!(runState && RUN_TERMINAL[runState])) {
      setMessage("run", null, "");
      resetConsole();
      setRunState(null, null);
    }
    // A finished console stays as it ended: its lines, badges, message and outcome.
    runResultUnseen = false;
    if (state.lastRun && !state.lastRun.seen) {
      state.lastRun.seen = true;
      saveUserState();
    }
    showView("run");
  }

  // Follows the tracked run from any view, so the state is known everywhere.
  function ensureRunPoll() {
    // The run going, or else the run that last ended, whose console is rebuilt once.
    var task = state.activeTask || (state.lastRun && runState === null ? state.lastRun : null);
    if (!task || runPollTaskId === task.task_id) {
      return;
    }
    // Re-attaching: an empty cursor replays the run's lines from the store.
    setMessage("run", null, "");
    resetConsole();
    setRunState("PENDING", null);
    openRunPoll(task.task_id);
  }

  /* The files produced for this context, everyone's, read fresh on every visit (req 5). */
  function loadFiles() {
    var selection = state.selection;
    if (!selection) {
      return Promise.resolve();
    }
    renderFiles(state.files);
    return request("GET", mdgFilesUrl(selection))
      .then(function (payload) {
        if (state.selection !== selection) {
          return;
        }
        state.files = payload.files || [];
        renderFiles(state.files);
      })
      .catch(function (error) {
        if (!handleExpired(error)) {
          state.files = [];
          renderFiles([]);
          setMessage("files", "error", error.message);
        }
      });
  }

  // A file produced elsewhere joins this context's files and opens like a picked one.
  function uploadFile(file) {
    var selection = state.selection;
    if (!selection || !file) {
      return;
    }
    setMessage("files", null, "");
    setBusy(el.filesUpload, true, "Uploading", "Upload");
    request("POST", mdgFilesUrl(selection), file)
      .then(function (record) {
        setBusy(el.filesUpload, false, "Uploading", "Upload");
        if (state.selection !== selection) {
          return;
        }
        openFile(record);
      })
      .catch(function (error) {
        setBusy(el.filesUpload, false, "Uploading", "Upload");
        if (!handleExpired(error)) {
          setMessage("files", "error", error.message);
        }
      });
  }

  // files: null until asked, so the card never claims there are none too early.
  function renderFiles(files) {
    el.runFiles.textContent = "";
    el.runFilesPanel.hidden = files === null;
    if (files === null) {
      return;
    }
    el.runFilesEmpty.hidden = files.length > 0;
    files.forEach(function (file) {
      el.runFiles.appendChild(fileRow(file));
    });
  }

  // Picking a file opens the model card on it.
  function openFile(file) {
    state.modelFile = file;
    state.model = null;
    saveUserState();
    enterModel();
  }

  function fileRow(file) {
    var row = document.createElement("li");
    row.className = "filerow";

    var main = document.createElement("div");
    main.className = "filerow__main";
    main.appendChild(span("filerow__when", generatedAt(file.generated_at)));
    main.appendChild(span("filerow__by", file.produced_by || "unknown"));
    main.appendChild(span("filerow__scale", scaleSummary(file.scale)));
    // A file produced with candidates says which (SRS DSM-MDG req 11).
    (file.candidates || []).forEach(function (candidate) {
      main.appendChild(span("units__badge", candidate.unit_name + " " + candidate.version));
    });

    var go = document.createElement("i");
    go.className = "lucide lucide-arrow-right filerow__go";
    row.appendChild(main);
    row.appendChild(go);
    row.tabIndex = 0;
    row.setAttribute("role", "button");
    row.addEventListener("click", function () {
      openFile(file);
    });
    row.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openFile(file);
      }
    });
    return row;
  }

  // The same counts the model card's scale cells show, in their order.
  function scaleSummary(scale) {
    var parts = [];
    SCALE_CELLS.forEach(function (cell) {
      if (scale && scale[cell.key] !== undefined) {
        parts.push(scale[cell.key] + " " + cell.label.toLowerCase());
      }
    });
    return parts.join(" · ");
  }

  function wireRun() {
    el.runIndicator.addEventListener("click", enterProduce);
    el.filesPrimary.addEventListener("click", enterInventory);
    el.filesUpload.addEventListener("click", function () {
      el.filesUploadInput.click();
    });
    el.filesUploadInput.addEventListener("change", function () {
      var file = el.filesUploadInput.files[0];
      // Cleared so picking the same file again still fires.
      el.filesUploadInput.value = "";
      uploadFile(file);
    });
    el.runStart.addEventListener("click", startRun);
    el.runModel.addEventListener("click", enterModel);

    el.runCancel.addEventListener("click", function () {
      var task = state.activeTask;
      if (!task) {
        return;
      }
      // The button stays busy until a poll brings the revoked state.
      setBusy(el.runCancel, true, "Cancelling", "Cancel");
      request("POST", taskUrl(task.task_id, "cancel")).catch(function (error) {
        setBusy(el.runCancel, false, "Cancelling", "Cancel");
        if (!handleExpired(error)) {
          setMessage("run", "error", error.message);
        }
      });
    });
  }

  // A new run from the inventory card: the console opens as queued and submits.
  function startNewRun() {
    closeRunPoll();
    runResultUnseen = false;
    renderRunContext();
    setRunState("PENDING", null);
    showView("run");
    startRun();
  }

  function startRun() {
    setMessage("run", null, "");
    resetConsole();
    setBusy(el.runStart, true, "Submitting", "Start production");
    var body = {
      project_id: state.selection.project_id,
      platform_id: state.selection.platform_id,
      version_id: state.selection.version_id
    };
    var candidates = candidateList();
    if (candidates.length) {
      body.candidates = candidates;
    }
    request("POST", API.run, body)
      .then(function (payload) {
        state.lastRun = null;
        state.activeTask = {
          task_id: payload.task_id,
          project_id: state.selection.project_id,
          platform_id: state.selection.platform_id,
          version_id: state.selection.version_id,
          candidates: candidates
        };
        saveUserState();
        setBusy(el.runStart, false, "Submitting", "Start production");
        setRunState("PENDING", null);
        openRunPoll(payload.task_id);
      })
      .catch(function (error) {
        setBusy(el.runStart, false, "Submitting", "Start production");
        setRunState(null, null);
        if (!handleExpired(error)) {
          setMessage("run", "error", error.message);
        }
      });
  }

  // Starts following a run; the line cursor is the console's and is left alone.
  function openRunPoll(taskId) {
    closeRunPoll();
    runPollFails = 0;
    runPollLastStatus = null;
    runPollTaskId = taskId;
    pollRun();
  }

  /* One poll. The next tick is armed only once this one has answered, and
   * an answer for a task or cursor that has since moved on is dropped. */
  function pollRun() {
    if (!runPollTaskId || runPollInFlight) {
      return;
    }
    runPollInFlight = true;
    var taskId = runPollTaskId;
    var after = runPollLastId;
    var url = taskUrl(taskId);
    if (after !== null) {
      url += "?after=" + encodeURIComponent(after);
    }
    request("GET", url)
      .then(function (payload) {
        if (taskId !== runPollTaskId || after !== runPollLastId) {
          return;
        }
        runPollFails = 0;
        var lines = payload.lines || [];
        runPollLastId = (runPollLastId === null ? -1 : runPollLastId) + lines.length;
        appendConsoleBatch(lines);
        var status = JSON.stringify({
          state: payload.state,
          result: payload.result,
          error: payload.error,
          progress: payload.progress
        });
        // A finished run being rebuilt that the server no longer remembers (it reports an
        // unknown id as queued) is let go of.
        if (!state.activeTask && !RUN_TERMINAL[payload.state]) {
          closeRunPoll();
          state.lastRun = null;
          runResultUnseen = false;
          resetConsole();
          setRunState(null, null);
          saveUserState();
          return;
        }
        if (status !== runPollLastStatus) {
          runPollLastStatus = status;
          setRunState(payload.state, payload);
        }
        if (RUN_TERMINAL[payload.state]) {
          closeRunPoll();
          var tracked = state.activeTask;
          if (tracked) {
            // A finished run is no longer tracked, but stays the selection's last run.
            runResultUnseen = state.view !== "run";
            state.lastRun = {
              task_id: tracked.task_id,
              project_id: tracked.project_id,
              platform_id: tracked.platform_id,
              version_id: tracked.version_id,
              seen: !runResultUnseen
            };
            state.activeTask = null;
          }
          saveUserState();
          renderRunIndicator();
          return;
        }
        schedulePoll();
      })
      .catch(function (error) {
        if (handleExpired(error)) {
          return;
        }
        if (taskId !== runPollTaskId || after !== runPollLastId) {
          return;
        }
        runPollFails += 1;
        if (runPollFails >= POLL_MAX_CONSECUTIVE_FAILURES) {
          closeRunPoll();
          setMessage("run", "error", "Lost the connection to the run. Reload the page to continue.");
          return;
        }
        schedulePoll();
      })
      .then(function () {
        runPollInFlight = false;
        schedulePoll();
      });
  }

  function schedulePoll() {
    if (!runPollTaskId || runPollTimer !== null) {
      return;
    }
    runPollTimer = window.setTimeout(function () {
      runPollTimer = null;
      pollRun();
    }, RUN_POLL_MS);
  }

  // runPollInFlight is left to the request that owns it.
  function closeRunPoll() {
    if (runPollTimer !== null) {
      window.clearTimeout(runPollTimer);
      runPollTimer = null;
    }
    runPollTaskId = null;
  }

  // status: the poll payload, or null when there is nothing to report yet.
  function setRunState(taskState, status) {
    runState = taskState;
    var known = RUN_STATES[taskState] || null;
    var running = !!taskState && !RUN_TERMINAL[taskState];

    el.runStatus.setAttribute("data-tone", known ? known.tone : "idle");
    el.runStatusValue.textContent = known ? known.label : "Not started";

    var runId = status && status.result && status.result.run_id;
    var ready = taskState === "SUCCESS" && !!runId;
    var task = state.activeTask ? state.activeTask.task_id : null;

    // Start is the row's action until a run produces a file; then View Model takes its place.
    el.runStart.hidden = running || ready;
    setBusy(el.runStart, false, "Submitting", "Start production");
    el.runCancel.hidden = !running;
    setBusy(el.runCancel, false, "Cancelling", "Cancel");
    el.runModel.hidden = !ready;

    // A run that wrote a file makes it the one the model card shows; a newer run drops the old one.
    var shownRun = state.modelFile ? state.modelFile.run_id : null;
    if (ready ? shownRun !== runId : shownRun && shownRun !== task) {
      state.modelFile = ready
        ? { run_id: runId, produced_by: state.username, generated_at: null, scale: status.result.scale }
        : null;
      state.model = null;
      renderStepper(state.view);
      saveUserState();
    }
    if (ready) {
      loadFiles();
    }

    renderRunProgress(taskState, status);
    renderRunElapsed(taskState, status);
    renderConsoleTail(taskState);
    // Under the panel: the run's error alone; a success speaks through the
    // bar's tone and the View model action.
    if (status && status.error) {
      setMessage("run", "error", status.error);
    } else if (taskState === "SUCCESS") {
      setMessage("run", null, "");
    }
    renderRunIndicator();
  }

  function runIsLive() {
    return !!state.activeTask && !!runState && !RUN_TERMINAL[runState];
  }

  // The pill in the session bar and the pulse on the Produce step, on every view
  // but the console's: the run going, or how it ended until its console is opened.
  function renderRunIndicator() {
    var live = runIsLive();
    var finished = !live && runResultUnseen && !!runState && RUN_TERMINAL[runState];
    var shown = (live || finished) && state.view !== "run";
    el.runIndicator.hidden = !shown;
    el.runIndicatorDivider.hidden = !shown;
    if (shown) {
      var label = (RUN_STATES[runState] || {}).label || "Running";
      var suffix = live
        ? runPercent === null ? "" : " · " + runPercent + "%"
        : runElapsedBase === null ? "" : " · " + formatElapsed(runElapsedBase);
      el.runIndicatorText.textContent = label + suffix;
      el.runIndicator.setAttribute("data-tone", live ? "busy" : runState === "SUCCESS" ? "ok" : "bad");
      el.runIndicator.title = live ? "Open the production run" : "Open the finished run";
      el.runIndicatorSpinner.hidden = !live;
      el.runIndicatorIcon.hidden = live;
      el.runIndicatorIcon.className = "lucide " + (runState === "SUCCESS" ? "lucide-circle-check" : "lucide-circle-x");
    }
    renderStepper(state.view);
  }

  // The log's tail: a blinking cursor while the run goes, gone once it has ended.
  function renderConsoleTail(taskState) {
    if (taskState === "STARTED" && !el.console.classList.contains("console--empty")) {
      showConsoleCursor();
    } else {
      hideConsoleCursor();
    }
  }

  function showConsoleCursor() {
    if (!consoleCursor) {
      consoleCursor = document.createElement("div");
      consoleCursor.className = "console__cursor";
      consoleCursor.setAttribute("aria-hidden", "true");
    }
    // Always the last thing in the log.
    el.console.appendChild(consoleCursor);
  }

  function hideConsoleCursor() {
    if (consoleCursor && consoleCursor.parentNode) {
      consoleCursor.parentNode.removeChild(consoleCursor);
    }
  }

  /* Elapsed time: measured by the server's clock at each poll (start to finish,
   * or start to now), ticked locally in between while the run is going. */
  function renderRunElapsed(taskState, status) {
    stopElapsedTicker();
    var startedAt = status && status.started_at;
    if (!startedAt) {
      el.runElapsed.hidden = true;
      el.runElapsed.textContent = "";
      return;
    }
    var until = status.finished_at || status.now || startedAt;
    runElapsedBase = Math.max(0, until - startedAt);
    runElapsedAt = performance.now();
    el.runElapsed.hidden = false;
    el.runElapsed.textContent = formatElapsed(runElapsedBase);
    if (taskState === "STARTED") {
      runElapsedTimer = window.setInterval(function () {
        el.runElapsed.textContent = formatElapsed(runElapsedBase + (performance.now() - runElapsedAt) / 1000);
      }, 1000);
    }
  }

  function stopElapsedTicker() {
    if (runElapsedTimer !== null) {
      window.clearInterval(runElapsedTimer);
      runElapsedTimer = null;
    }
  }

  // "22 s", "1 m 05 s", "1 h 02 m".
  function formatElapsed(seconds) {
    var total = Math.max(0, Math.floor(seconds));
    var hours = Math.floor(total / 3600);
    var minutes = Math.floor((total % 3600) / 60);
    var rest = total % 60;
    var two = function (n) {
      return (n < 10 ? "0" : "") + n;
    };
    if (hours) {
      return hours + " h " + two(minutes) + " m";
    }
    if (minutes) {
      return minutes + " m " + two(rest) + " s";
    }
    return rest + " s";
  }

  // The task's percent; kept at its last value once the run ends, 100 on success.
  function renderRunProgress(taskState, status) {
    if (taskState === "SUCCESS") {
      showRunProgress(100);
      return;
    }
    if (RUN_TERMINAL[taskState]) {
      return;
    }
    var percent = status && status.progress && status.progress.percent;
    if (percent === undefined || percent === null) {
      // Running without a report yet: the bar starts at zero rather than absent.
      if (taskState === "STARTED" && el.runPercent.hidden) {
        showRunProgress(0);
      }
      return;
    }
    showRunProgress(percent);
  }

  function showRunProgress(percent) {
    percent = Math.max(0, Math.min(100, Math.round(percent)));
    el.runProgress.hidden = false;
    el.runProgress.setAttribute("aria-valuenow", String(percent));
    el.runProgress.style.transform = "scaleX(" + percent / 100 + ")";
    el.runPercent.hidden = false;
    el.runPercent.textContent = percent + "%";
    runPercent = percent;
  }

  // The task log's "%(asctime)s %(levelname)-8s %(message)s" line; anything else is rendered whole.
  var LOG_LINE = /^(\d{2}:\d{2}:\d{2})\s+(DEBUG|INFO|WARNING|ERROR|CRITICAL)(\s+)([\s\S]*)$/;

  // How many rows the console keeps; older ones are counted in a marker at the top.
  var CONSOLE_MAX_ROWS = 1000;
  var consoleRows = 0;
  var consoleTrimmed = 0;

  // Empties the console, its progress strip and the poll cursor.
  function resetConsole() {
    consoleRows = 0;
    consoleTrimmed = 0;
    runPollLastId = null;
    el.runProgress.hidden = true;
    el.runProgress.removeAttribute("aria-valuenow");
    el.runProgress.style.transform = "scaleX(0)";
    el.runPercent.hidden = true;
    el.runPercent.textContent = "";
    runPercent = null;
    stopElapsedTicker();
    el.runElapsed.hidden = true;
    el.runElapsed.textContent = "";
    consoleCursor = null;
    el.console.textContent = "";
    el.console.appendChild(
      emptyBlock("idle", "lucide-rocket", "Awaiting launch", "Start a production to watch it here.")
    );
    el.console.classList.add("console--empty");
    el.console.hidden = false;
  }

  // Appends a poll's lines in one fragment and follows the tail only if already at it.
  function appendConsoleBatch(lines) {
    if (!lines.length) {
      return;
    }
    if (el.console.classList.contains("console--empty")) {
      el.console.textContent = "";
      el.console.classList.remove("console--empty");
    }

    var atBottom = el.console.scrollTop + el.console.clientHeight >= el.console.scrollHeight - 4;

    var fragment = document.createDocumentFragment();
    lines.forEach(function (line) {
      fragment.appendChild(consoleLine(line));
    });
    el.console.appendChild(fragment);
    consoleRows += lines.length;
    enforceConsoleCap();
    if (runState === "STARTED") {
      showConsoleCursor();
    }

    if (atBottom) {
      el.console.scrollTop = el.console.scrollHeight;
    }
  }

  function consoleLine(line) {
    var row = document.createElement("div");
    row.className = "console__line";

    var parts = LOG_LINE.exec(line);
    if (parts) {
      row.setAttribute("data-level", parts[2]);
      row.appendChild(span("console__time", parts[1]));
      var level = span("console__level", parts[2]);
      level.setAttribute("data-level", parts[2]);
      row.appendChild(level);
      row.appendChild(span("console__text", (parts[3] + parts[4]).replace(/^\s+/, "")));
    } else {
      row.className += " console__line--plain";
      row.textContent = line;
    }
    return row;
  }

  // Drops the oldest rows past the cap and names how many in the marker.
  function enforceConsoleCap() {
    if (consoleRows <= CONSOLE_MAX_ROWS) {
      return;
    }
    var marker = el.console.firstElementChild;
    var row;
    if (marker && marker.classList.contains("console__trimmed")) {
      row = marker.nextElementSibling;
    } else {
      row = marker;
      marker = note("console__trimmed", "");
      el.console.insertBefore(marker, el.console.firstChild);
    }
    while (consoleRows > CONSOLE_MAX_ROWS && row) {
      var next = row.nextElementSibling;
      el.console.removeChild(row);
      consoleRows -= 1;
      consoleTrimmed += 1;
      row = next;
    }
    marker.textContent = "… " + consoleTrimmed + " earlier lines trimmed";
  }

  /* --------------------------------------------------------------- model */

  /* The Model Setup Data file read back a panel at a time (req 8); fetched
   * once per run and kept. */

  // What the writer leaves where a source had nothing to give.
  var MISSING = "NOT_FOUND";

  // The file read back once and kept (req 8); resolves with nothing when
  // another file took the card meanwhile. Errors are the caller's to show.
  function loadModel(runId) {
    if (state.model) {
      return Promise.resolve(state.model);
    }
    return request("GET", mdgFilesUrl(state.selection, runId, "model")).then(function (model) {
      if (!state.modelFile || state.modelFile.run_id !== runId) {
        return undefined;
      }
      state.model = model;
      return model;
    });
  }

  function enterModel() {
    setMessage("model", null, "");
    if (!state.modelFile) {
      enterFiles();
      return;
    }
    var runId = state.modelFile.run_id;
    el.modelDownload.href = mdgFilesUrl(state.selection, runId, "download");
    showView("model");

    if (state.model) {
      renderModel(state.model);
      return;
    }
    el.modelContext.hidden = true;
    el.modelGrid.hidden = true;
    el.modelLoading.hidden = false;
    loadModel(runId)
      .then(function (model) {
        el.modelLoading.hidden = true;
        if (model) {
          renderModel(model);
        }
      })
      .catch(function (error) {
        el.modelLoading.hidden = true;
        if (!handleExpired(error)) {
          setMessage("model", "error", error.message);
        }
      });
  }

  function renderModel(model) {
    renderModelContext(model);
    renderModelScale(model);
    renderModelInventory((model.inventory || {}).units || []);
    renderModelLog(model);
    renderModelErrors(model);
    el.modelGrid.hidden = false;
  }

  function renderModelContext(model) {
    fillModelContext(model, {
      line: el.modelContext,
      project: el.modelProject,
      platform: el.modelPlatform,
      version: el.modelVersion,
      current: el.modelCurrent,
      generated: el.modelGenerated
    });
  }

  // The file's context line (req 4, 16) into one view's cells; the model
  // card and the graph stage each have a set.
  function fillModelContext(model, cells) {
    var context = model.context || {};
    var version = context.version || {};
    fillContext(cells.project, shown((context.project || {}).name));
    fillContext(cells.platform, shown((context.platform || {}).name));
    fillContext(cells.version, shown(version.label));
    cells.current.hidden = !version.is_effective;
    fillContext(cells.generated, generatedAt(model.generated_at));
    cells.line.hidden = false;
  }

  // The counts the file's metadata carries. The model card lays them out
  // in two rows of three: Nodes, Applications and Topics on top, Networks,
  // Libraries and Messages below.
  var SCALE_CELLS = [
    { key: "nodes", label: "Nodes" },
    { key: "apps", label: "Applications" },
    { key: "topics", label: "Topics" },
    { key: "networks", label: "Networks" },
    { key: "libraries", label: "Libraries" },
    { key: "messages", label: "Messages" }
  ];
  var SCALE_ROWS = [
    { cls: "scale__row--three", keys: ["nodes", "apps", "topics"] },
    { cls: "scale__row--three", keys: ["networks", "libraries", "messages"] }
  ];
  var cellByKey = {};
  SCALE_CELLS.forEach(function (cell) {
    cellByKey[cell.key] = cell;
  });

  function renderModelScale(model) {
    var scale = ((model.graph || {}).metadata || {}).scale || {};
    el.modelScale.textContent = "";
    SCALE_ROWS.forEach(function (row) {
      var wrap = document.createElement("div");
      wrap.className = "scale__row " + row.cls;
      row.keys.forEach(function (key) {
        var cell = cellByKey[key];
        var box = document.createElement("div");
        box.className = "scale__cell";
        var count = scale[key];
        box.appendChild(span("scale__value", count === undefined ? "—" : String(count)));
        box.appendChild(span("scale__label", cell.label));
        wrap.appendChild(box);
      });
      el.modelScale.appendChild(wrap);
    });
  }

  function renderModelInventory(units) {
    setPanelCount(el.modelUnitCount, units.length);
    if (!units.length) {
      emptyPanel(el.modelUnits, "lucide-package", "Nothing here yet", "No software units in this inventory.");
      return;
    }
    el.modelUnits.textContent = "";
    units.forEach(function (unit) {
      var built = modelRow(el.modelUnits);
      built.head.appendChild(span("mrow__name", shown(unit.unit_name)));
      if (unit.is_candidate) {
        built.head.appendChild(span("units__badge", "Candidate"));
      }
      built.head.appendChild(span("mrow__value", shown(unit.version)));
    });
  }

  // One row per file obtained (SRS DSM-MDG req 14).
  function renderModelLog(model) {
    var files = model.acquired_files || [];
    setPanelCount(el.modelLogCount, files.length);
    if (!files.length) {
      emptyPanel(el.modelLog, "lucide-hard-drive", "Nothing acquired", "No files were obtained for this model.");
      return;
    }
    el.modelLog.textContent = "";
    files.forEach(function (file) {
      var built = modelRow(el.modelLog);
      var name = span("mrow__name", shown(file.file_name));
      name.title = file.file_path || shown(file.file_name);
      built.head.appendChild(name);
      built.head.appendChild(span("mrow__value", shown(file.unit_name)));
      detailLine(built.row).appendChild(
        document.createTextNode(shown(file.package_version) + " · " + generatedAt(file.updated_at))
      );
    });
  }

  // The file's error records: status, reason, source and project/platform (SRS DSM-MDG req 18).
  function renderModelErrors(model) {
    var errors = model.errors || [];
    setPanelCount(el.modelErrorCount, errors.length);
    if (!errors.length) {
      clearPanel(el.modelErrors, "No Errors", "Every source this model was built from was acquired and passed the checks.");
      return;
    }
    el.modelErrors.textContent = "";
    errors.forEach(function (error) {
      var built = modelRow(el.modelErrors);
      built.head.appendChild(dot(error.status, words(error.status)));
      built.head.appendChild(span("mrow__name", shown(error.reason)));
      built.head.appendChild(chip(words(error.status), error.status));
      detailLine(built.row).appendChild(
        document.createTextNode(
          shown(error.source_name) + " · " + words(error.source_type) + " · " + shown(error.project_platform)
        )
      );
    });
  }

  /* --------------------------------------------------------------- graph */

  /* The model card's file drawn as the system hierarchy by static/graph.js
   * (SRS DSM-DVE req 43). The model is fetched once (req 8), shared with the
   * model card, and redrawn only when another file takes the card. */

  // The model the picture on screen was drawn from, and in which mode.
  var graphModel = null;
  var graphDrawnMode = null;

  function enterGraph() {
    setMessage("graph", null, "");
    if (!state.modelFile) {
      enterFiles();
      return;
    }
    var runId = state.modelFile.run_id;
    showView("graph");
    if (state.model) {
      renderGraph(state.model);
      return;
    }
    el.graphContext.hidden = true;
    el.graphLoading.hidden = false;
    loadModel(runId)
      .then(function (model) {
        if (model) {
          renderGraph(model);
        }
      })
      .catch(function (error) {
        el.graphLoading.hidden = true;
        if (!handleExpired(error)) {
          setMessage("graph", "error", error.message);
        }
      });
  }

  function renderGraph(model) {
    // The tree's model named under the title (req 4, 16), as the model card does.
    fillModelContext(model, {
      line: el.graphContext,
      project: el.graphProject,
      platform: el.graphPlatform,
      version: el.graphVersion,
      current: el.graphCurrent,
      generated: el.graphGenerated
    });
    renderGraphMode();
    if (graphModel === model && graphDrawnMode === state.graphMode) {
      // Back on the card: the canvas may have been hidden while the window changed.
      DsmHierarchyGraph.resize();
      return;
    }
    var graph = model.graph || {};
    if (state.graphMode === "hw" && !(graph.nodes || []).length && !(graph.networks || []).length) {
      setMessage("graph", "error", "This model has no nodes or networks to draw.");
    }
    el.graphLoading.hidden = false;
    // The canvas has its size only once the card is shown; let that settle.
    setTimeout(function () {
      var drawing = state.graphMode;
      DsmHierarchyGraph.load(model, drawing)
        .then(function () {
          graphModel = model;
          graphDrawnMode = drawing;
          el.graphLoading.hidden = true;
          // The new picture enters as a card does on a change of view.
          playIn(el.graphCanvas);
        })
        .catch(function (error) {
          el.graphLoading.hidden = true;
          setMessage("graph", "error", error && error.message ? error.message : String(error));
        });
    }, 30);
  }

  // The title and chips follow the mode.
  function renderGraphMode() {
    renderGraphTitle();
    el.graphSearch.setAttribute("data-mode", state.graphMode);
  }

  // The stage's title is the model deck's; a segmented switch beside it
  // picks the picture. Built with DOM calls, as the header otherwise sets
  // text only.
  function renderGraphTitle() {
    renderHeader({ title: "" });
    // An empty title falls back to the product's name; the row takes its place.
    el.title.textContent = "";
    var row = document.createElement("span");
    row.className = "title__row";
    var word = document.createElement("span");
    word.className = "title__word";
    word.textContent = "Core System Model";
    row.appendChild(word);
    var group = document.createElement("span");
    group.className = "modeswitch";
    group.setAttribute("role", "group");
    group.setAttribute("aria-label", "View mode");
    ["sw", "hw"].forEach(function (mode) {
      var on = mode === state.graphMode;
      var option = document.createElement("button");
      option.type = "button";
      option.className = "modeswitch__option";
      option.setAttribute("data-mode", mode);
      option.setAttribute("aria-pressed", on ? "true" : "false");
      option.title = on ? GRAPH_TITLES[mode] + " view, on show" : "Show the " + GRAPH_TITLES[mode].toLowerCase() + " view";
      option.textContent = GRAPH_TITLES[mode];
      group.appendChild(option);
    });
    row.appendChild(group);
    el.title.appendChild(row);
  }

  function wireGraph() {
    DsmHierarchyGraph.mount(el.graphCanvas, el.graphSearch);
    // The model card's way on to the view step (req 43).
    el.modelView.addEventListener("click", enterGraph);
    // The switch's other segment redraws the loaded model as that picture.
    el.title.addEventListener("click", function (event) {
      var option = event.target.closest ? event.target.closest(".modeswitch__option") : null;
      var mode = option && option.getAttribute("data-mode");
      // No change while a picture is still being drawn: two renders would overlap.
      if (!mode || mode === state.graphMode || state.view !== "graph" || !el.graphLoading.hidden) {
        return;
      }
      state.graphMode = mode;
      saveUserState();
      setMessage("graph", null, "");
      if (graphModel) {
        renderGraph(graphModel);
      } else {
        renderGraphMode();
      }
    });
  }

  function modelRow(host) {
    var row = document.createElement("div");
    row.className = "mrow";
    var head = document.createElement("div");
    head.className = "mrow__head";
    row.appendChild(head);
    host.appendChild(row);
    return { row: row, head: head };
  }

  function detailLine(row) {
    var line = document.createElement("div");
    line.className = "mrow__detail";
    row.appendChild(line);
    return line;
  }

  // textContent throughout: nothing from the server or the file is parsed as markup.
  function span(className, text) {
    var node = document.createElement("span");
    node.className = className;
    node.textContent = text;
    return node;
  }

  function chip(text, status) {
    var node = span("chip", text);
    node.setAttribute("data-status", status);
    return node;
  }

  function dot(level, title) {
    var node = span("dot", "");
    node.setAttribute("data-level", String(level || "").toLowerCase());
    if (title) {
      node.title = title;
    }
    return node;
  }

  // The one empty state: a sealed glyph or spinner, a verdict, an optional note.
  function emptyBlock(tone, glyph, title, text) {
    var box = document.createElement("div");
    box.className = "empty" + (tone !== "idle" ? " empty--" + tone : "");
    var seal = span("empty__seal", "");
    if (tone === "busy") {
      seal.appendChild(span("spinner", ""));
    } else {
      var icon = document.createElement("i");
      icon.className = "lucide " + glyph;
      seal.appendChild(icon);
    }
    box.appendChild(seal);
    box.appendChild(note("empty__title", title));
    if (text) {
      box.appendChild(note("empty__note", text));
    }
    return box;
  }

  function emptyPanel(host, glyph, title, text) {
    host.textContent = "";
    host.appendChild(emptyBlock("idle", glyph, title, text));
  }

  // A panel empty because the run found nothing to report, which is the good outcome.
  function clearPanel(host, title, text) {
    host.textContent = "";
    host.appendChild(emptyBlock("ok", "lucide-circle-check", title, text));
  }

  function note(className, text) {
    var node = document.createElement("p");
    node.className = className;
    node.textContent = text;
    return node;
  }

  function setPanelCount(node, count) {
    node.textContent = count ? String(count) : "";
  }

  // A dash for an absent value.
  function shown(value) {
    return value === 0 || (value && value !== MISSING) ? String(value) : "—";
  }

  // SCREAMING_SNAKE enums as words; the stylesheet uppercases the chips.
  function words(value) {
    return shown(value).replace(/_/g, " ");
  }

  // An ISO timestamp in the reader's clock, or as written if it does not parse.
  function generatedAt(value) {
    if (!value) {
      return "—";
    }
    var when = new Date(value);
    return isNaN(when.getTime()) ? value : when.toLocaleString();
  }

  /* ------------------------------------------------------------ remember */

  // Usernames only, to prefill a field.
  function remember(key, value) {
    try {
      window.localStorage.setItem(key, value);
    } catch (error) {
      // Storage may be blocked; the prefill is optional.
    }
  }

  function restore(input, key) {
    var saved = null;
    try {
      saved = window.localStorage.getItem(key);
    } catch (error) {
      saved = null;
    }
    if (saved) {
      input.value = saved;
    }
  }

  /* ------------------------------------------------------------- wire-up */

  function wireReveal() {
    document.addEventListener("click", function (event) {
      var button = event.target.closest("[data-reveal]");
      if (!button) {
        return;
      }
      var input = $(button.getAttribute("data-reveal"));
      var icon = button.querySelector(".lucide");
      var revealed = input.type === "text";
      input.type = revealed ? "password" : "text";
      icon.className = revealed ? "lucide lucide-eye-off" : "lucide lucide-eye";
      button.setAttribute("aria-label", revealed ? "Show password" : "Hide password");
      input.focus();
    });
  }

  function wireStepper() {
    var enter = {
      sources: enterSources,
      files: enterFiles,
      units: enterInventory,
      run: enterProduce,
      model: enterModel,
      graph: enterGraph
    };
    STAGES.forEach(function (key) {
      el.stages[key].button.addEventListener("click", function () {
        if (key === state.view) {
          return;
        }
        if (enter[key]) {
          enter[key]();
        } else if (STAGES.indexOf(state.view) > STAGES.indexOf("select")) {
          // The pickers still hold this selection.
          showView("select");
        } else {
          enterSelect();
        }
      });
    });
  }

  function wireSignOut() {
    Array.prototype.forEach.call(document.querySelectorAll("[data-signout]"), function (button) {
      button.addEventListener("click", signOut);
    });
  }

  function wireLogin() {
    clearOnInput([el.username, el.password], "login");

    el.loginForm.addEventListener("submit", function (event) {
      event.preventDefault();
      setMessage("login", null, "");

      if (!el.username.value || !el.password.value) {
        setMessage("login", "error", "Username and password are required.");
        (el.username.value ? el.password : el.username).focus();
        return;
      }

      setBusy(el.loginSubmit, true, "Authenticating", "Authenticate");
      request("POST", API.login, { username: el.username.value, password: el.password.value })
        .then(function (payload) {
          state.username = payload.username;
          state.defaults = payload.defaults;
          remember(LAST_USER_KEY, payload.username);
          el.password.value = "";
          setBusy(el.loginSubmit, false, "Authenticating", "Authenticate");
          enterSources();
        })
        .catch(function (error) {
          setBusy(el.loginSubmit, false, "Authenticating", "Authenticate");
          setMessage("login", "error", error.message);
          el.password.value = "";
          el.password.focus();
        });
    });
  }

  function wireSelect() {
    el.project.addEventListener("change", function () {
      setMessage("select", null, "");
      clearPlatform();
      syncSelectSubmit();
      if (!el.project.value) {
        return;
      }
      loadPlatforms(el.project.value).catch(function (error) {
        if (!handleExpired(error)) {
          setMessage("select", "error", error.message);
        }
      });
    });

    el.platform.addEventListener("change", function () {
      setMessage("select", null, "");
      clearVersion();
      syncSelectSubmit();
      if (!el.platform.value) {
        return;
      }
      loadVersions(el.project.value, el.platform.value).catch(function (error) {
        if (!handleExpired(error)) {
          setMessage("select", "error", error.message);
        }
      });
    });

    el.version.addEventListener("change", syncSelectSubmit);

    el.selectForm.addEventListener("submit", function (event) {
      event.preventDefault();
      setMessage("select", null, "");
      var selection = {
        project_id: el.project.value,
        platform_id: el.platform.value,
        version_id: el.version.value
      };
      var changed = !tracks(state.selection, selection);
      state.selection = selection;
      if (changed) {
        forgetContext();
      }
      if (!tracks(state.activeTask, state.selection)) {
        state.activeTask = null;
        closeRunPoll();
      }
      saveUserState();
      enterFiles();
    });
  }

  function wireInventory() {
    el.unitFilter.addEventListener("input", drawUnits);

    // A tracked run is re-attached to; otherwise a new one is submitted.
    el.unitsNext.addEventListener("click", function () {
      if (state.activeTask) {
        enterRunConsole();
      } else {
        startNewRun();
      }
    });
  }

  // Every element with an id, under its camel-cased id; the stepper items under their stage.
  function collect() {
    Array.prototype.forEach.call(document.querySelectorAll("[id]"), function (node) {
      var name = node.id.replace(/-([a-z0-9])/g, function (_, letter) {
        return letter.toUpperCase();
      });
      el[name] = node;
    });
    el.stages = {};
    STAGES.forEach(function (key) {
      var item = $("stepper-" + key);
      el.stages[key] = { item: item, button: item.querySelector(".stepper__button") };
    });
  }

  collect();
  wireReveal();
  wireSignOut();
  wireStepper();
  wireGraph();
  wireLogin();
  wireSources();
  wireModal();
  wireSelect();
  wireInventory();
  wireRun();
  el.card.addEventListener("animationend", function (event) {
    if (event.target === el.card) {
      el.card.classList.remove("card--in");
    }
  });
  boot();
})();
