/* DVE console: sign-in, data source connections, context, produced files,
 * production runs and the model they produce. The server keeps the sign-in
 * and the open connections; where the user stands is kept in localStorage. */
(function () {
  "use strict";

  var API = {
    session: "/api/session",
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
  function msdFilesUrl(selection, runId, suffix) {
    var base = selectionUrl(selection) + "/mdg-files";
    return runId ? base + "/" + encodeURIComponent(runId) + "/" + suffix : base;
  }

  /* The data sources this session must connect; `flag` is the field GET
   * /api/session reports the connection under. */
  var SOURCES = [
    {
      key: "config_mgmt_db",
      name: "CMDB Data",
      title: "Configuration Management DB",
      icon: "lucide-database",
      endpoint: "/api/data-sources/connect/config-mgmt-db",
      flag: "config_mgmt_db_connected",
      userKey: "dve.last-db-username"
    },
    {
      key: "source_code_repo",
      name: "SW Units & Scripts",
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
    sources: { title: "Data Sources", icon: "lucide-hard-drive", subtitle: "Connect Sources" },
    select: { title: "Project Context", icon: "lucide-network", subtitle: "Select Scope" },
    inventory: { title: "Software Unit Inventory", icon: "lucide-package" },
    files: { title: "Model Setup Data", icon: "lucide-file-code", subtitle: "Produced Files" },
    run: { title: "Model Setup Data", subtitle: "Production Run" },
    model: { title: "Core System Model" }
  };

  var PRODUCT_TITLE = "Digital System Model";

  // The stepper's stages, in order; boot and sign-in have none.
  var STAGES = ["sources", "select", "files", "inventory", "run", "model"];

  var VIEWS = ["boot", "login"].concat(STAGES);

  // Celery states and how each reads on the run card.
  var RUN_STATES = {
    PENDING: { label: "Queued", tone: "busy" },
    RETRY: { label: "Retrying", tone: "busy" },
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
    // The run being tracked: {task_id, project_id, platform_id, version_id, candidate}.
    activeTask: null,
    // The unit version under evaluation, {unit_name, version}, or null (SRS DSM-MDG req 11).
    candidate: null,
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

  function request(method, url, body) {
    var options = { method: method, credentials: "same-origin" };
    if (body !== undefined) {
      options.headers = { "Content-Type": "application/json" };
      options.body = JSON.stringify(body);
    }
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
            throw error;
          }
          return payload;
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
    if (state.view === "inventory" && name !== "inventory") {
      unitScroll = el.unitList.scrollTop;
    }
    state.view = name;
    VIEWS.forEach(function (view) {
      $("view-" + view).hidden = view !== name;
    });
    renderHeader(HEADERS[name]);
    renderStepper(name);
    el.card.setAttribute("data-view", name);
    el.shell.classList.toggle("shell--run", name === "run");
    el.shell.classList.toggle("shell--model", name === "model");
    renderSessionbar(STAGES.indexOf(name) !== -1);

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

  function renderStepper(name) {
    var current = STAGES.indexOf(name);
    el.stepper.hidden = current === -1;
    if (current === -1) {
      return;
    }
    var scoped = allConnected() && !!state.selection;
    STAGES.forEach(function (key, index) {
      var drawn = index < current ? "done" : index === current ? "current" : "todo";
      el.stages[key].item.setAttribute("data-state", drawn);
      // Reachability: sources always, select once connected, the rest once a context is confirmed.
      var reachable =
        key === "sources" ||
        (key === "select" && allConnected()) ||
        (key === "model" ? scoped && !!state.modelFile : scoped);
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
    state.ui = { view: saved.view || null, model_file: saved.model_file || null };
    // A run in flight owns the candidate it evaluates (SRS DSM-MDG req 11).
    state.candidate = state.activeTask ? state.activeTask.candidate || null : saved.candidate || null;
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
    state.username = null;
    SOURCES.forEach(function (source) {
      state.sources[source.key] = false;
    });
    state.selection = null;
    state.versions = null;
    state.activeTask = null;
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
        view: state.view,
        model_file: state.modelFile ? state.modelFile.run_id : null,
        candidate: state.candidate || null
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
      tile.setAttribute("aria-label", source.name + (connected ? ", connected" : ", not connected"));
      tile.appendChild(icon);
      tile.appendChild(span("source__name", source.name));
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
        setMessage("sources", "ok", source.name + " connected.");
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
        return saved.view === "inventory" ? enterInventory() : enterFiles();
      });
    }
    if (saved.view === "inventory") {
      return enterInventory();
    }
    if (saved.view === "files") {
      return enterFiles();
    }
    return resumeRunOrFiles();
  }

  // A tracked run outranks the landing card.
  function resumeRunOrFiles() {
    return state.activeTask ? enterRunConsole() : enterFiles();
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

  function selectedText(select) {
    var chosen = select.options[select.selectedIndex];
    return chosen ? chosen.textContent : "";
  }

  /* ----------------------------------------------------------- inventory */

  /* The Software Unit Version Inventory of the confirmed context (SRS DSM-MDG req 10). */

  // Every unit the database returned; the filter narrows what is drawn.
  var allUnits = null;
  // The list's scroll position when the card was last left.
  var unitScroll = 0;

  function enterInventory() {
    setMessage("inventory", null, "");
    renderContextLine();
    renderUnits(allUnits);
    drawCandidateControl();
    showView("inventory");
    el.unitList.scrollTop = unitScroll;
    return loadUnits()
      .then(function () {
        drawCandidateControl();
        el.unitList.scrollTop = unitScroll;
      })
      .catch(function (error) {
        if (handleExpired(error)) {
          return;
        }
        renderUnits([]);
        drawCandidateControl();
        setMessage("inventory", "error", error.message);
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
    state.candidate = null;
    forgetInventory();
  }

  function loadUnits() {
    return request("GET", selectionUrl(state.selection) + "/units").then(function (payload) {
      renderUnits(payload.units);
      return payload.units;
    });
  }

  // The confirmed context as a labelled strip above the list.
  function renderContextLine() {
    var version = selectedVersion();
    el.contextProject.textContent = selectedText(el.project);
    el.contextPlatform.textContent = selectedText(el.platform);
    el.contextVersion.textContent = version ? version.label : selectedText(el.version);
    el.contextCurrent.hidden = !(version && version.is_effective);
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
      // The candidate is overlaid at draw time, so allUnits stays the database's answer.
      var candidate = candidateFor(unit.unit_name);
      var row = document.createElement("div");
      row.className = "units__row";
      row.appendChild(span("units__name", unit.unit_name));
      if (candidate || unit.is_candidate) {
        row.appendChild(span("units__badge", "Candidate"));
      }
      row.appendChild(span("units__version", candidate ? candidate.version : unit.version));
      el.unitList.appendChild(row);
    });
  }

  function candidateFor(unitName) {
    return state.candidate && state.candidate.unit_name === unitName ? state.candidate : null;
  }

  /* ------------------------------------------------------- candidate */

  /* The unit version being evaluated for installation, one unit at a time
   * (SRS DSM-MDG req 11). Its versions come from the source repository. */

  // Versions per unit as the repository last reported them.
  var candidateVersions = {};

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

  function drawCandidateControl() {
    var units = allUnits || [];
    // A candidate naming a unit outside this inventory is dropped once the inventory has arrived.
    if (allUnits && state.candidate && !unitRow(state.candidate.unit_name)) {
      state.candidate = null;
    }

    el.candidateUnit.textContent = "";
    el.candidateUnit.appendChild(option("", "—"));
    units.forEach(function (unit) {
      el.candidateUnit.appendChild(option(unit.unit_name, unit.unit_name));
    });
    el.candidateUnit.disabled = !units.length;
    el.candidateUnit.value = state.candidate ? state.candidate.unit_name : "";

    if (!el.candidateUnit.value) {
      clearVersionPicker();
      return;
    }
    fillVersionPicker(el.candidateUnit.value);
  }

  function option(value, label) {
    var node = document.createElement("option");
    node.value = value;
    node.textContent = label;
    return node;
  }

  function clearVersionPicker() {
    el.candidateVersion.textContent = "";
    el.candidateVersion.appendChild(option("", "—"));
    setPickerEnabled(el.pickerCandidateVersion, el.candidateVersion, false);
    setVersionPickerLoading(false);
    setCandidateNote("");
  }

  function setVersionPickerLoading(loading) {
    el.pickerCandidateVersion.classList.toggle("picker--loading", !!loading);
  }

  function setCandidateNote(text, isError) {
    el.candidateNote.textContent = text;
    el.candidateNote.classList.toggle("candidate__note--error", !!isError);
  }

  // Offers the inventory's version alongside the ones the repository publishes.
  function fillVersionPicker(unitName) {
    var known = candidateVersions[unitName];
    if (known) {
      paintVersionPicker(unitName, known);
      return Promise.resolve(known);
    }
    el.candidateVersion.textContent = "";
    el.candidateVersion.appendChild(option("", "—"));
    setPickerEnabled(el.pickerCandidateVersion, el.candidateVersion, false);
    setCandidateNote("");
    setVersionPickerLoading(true);
    return request("GET", unitVersionsUrl(unitName))
      .then(function (payload) {
        candidateVersions[unitName] = payload.versions || [];
        // The user may have moved on while this was in flight.
        if (el.candidateUnit.value === unitName) {
          paintVersionPicker(unitName, candidateVersions[unitName]);
        }
        return candidateVersions[unitName];
      })
      .catch(function (error) {
        if (!handleExpired(error) && el.candidateUnit.value === unitName) {
          setVersionPickerLoading(false);
          setCandidateNote(error.message, true);
        }
        return [];
      });
  }

  function paintVersionPicker(unitName, versions) {
    var baseline = baselineVersion(unitName);
    var candidate = candidateFor(unitName);

    el.candidateVersion.textContent = "";
    // Choosing the inventory's own version is how a candidate is taken back.
    el.candidateVersion.appendChild(option(baseline, baseline + " · no change"));
    versions.forEach(function (version) {
      if (version !== baseline) {
        el.candidateVersion.appendChild(option(version, version));
      }
    });
    // A chosen candidate the repository no longer publishes stays listed.
    if (candidate && !hasOption(el.candidateVersion, candidate.version)) {
      el.candidateVersion.appendChild(option(candidate.version, candidate.version));
    }

    el.candidateVersion.value = candidate ? candidate.version : baseline;
    setVersionPickerLoading(false);
    setPickerEnabled(el.pickerCandidateVersion, el.candidateVersion, true);
    setCandidateNote(versions.length ? "" : "The source repository publishes no versions for " + unitName + ".");
  }

  function onCandidateUnitChange() {
    var unitName = el.candidateUnit.value;
    // Switching units drops the candidate.
    if (!state.candidate || state.candidate.unit_name !== unitName) {
      state.candidate = null;
      drawUnits();
      saveUserState();
    }
    if (!unitName) {
      clearVersionPicker();
      return;
    }
    fillVersionPicker(unitName);
  }

  function onCandidateVersionChange() {
    var unitName = el.candidateUnit.value;
    var version = el.candidateVersion.value;
    state.candidate =
      unitName && version && version !== baselineVersion(unitName)
        ? { unit_name: unitName, version: version }
        : null;
    drawUnits();
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

  // The Produce step: the tracked run's console, or the inventory that starts one.
  function enterProduce() {
    return state.activeTask ? enterRunConsole() : enterInventory();
  }

  function enterFiles() {
    var live = !!state.activeTask && runState !== null && !RUN_TERMINAL[runState];
    setMessage("files", null, live ? "A production run is already in progress." : "");
    showView("files");
    loadFiles();
  }

  function enterRunConsole() {
    setMessage("run", null, "");
    var task = state.activeTask;
    resetConsole();
    if (!task) {
      setRunState(null, null);
      showView("run");
      return;
    }
    // Re-attaching: an empty cursor replays the run's lines from the store.
    setRunState("PENDING", null);
    showView("run");
    openRunPoll(task.task_id);
  }

  /* The files produced for this context, everyone's, read fresh on every visit (req 5). */
  function loadFiles() {
    var selection = state.selection;
    if (!selection) {
      return Promise.resolve();
    }
    renderFiles(state.files);
    return request("GET", msdFilesUrl(selection))
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
    // A file produced with a candidate says which (SRS DSM-MDG req 11).
    if (file.candidate) {
      main.appendChild(span("units__badge", file.candidate.unit_name + " " + file.candidate.version));
    }

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

  // The same four counts the model card's scale cells show.
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
    el.filesPrimary.addEventListener("click", enterInventory);
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
    if (state.candidate) {
      body.candidate = state.candidate;
    }
    request("POST", API.run, body)
      .then(function (payload) {
        state.activeTask = {
          task_id: payload.task_id,
          project_id: state.selection.project_id,
          platform_id: state.selection.platform_id,
          version_id: state.selection.version_id,
          candidate: state.candidate
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
        if (status !== runPollLastStatus) {
          runPollLastStatus = status;
          setRunState(payload.state, payload);
        }
        if (RUN_TERMINAL[payload.state]) {
          closeRunPoll();
          // A finished run is no longer tracked: the next "Produce data" starts fresh.
          state.activeTask = null;
          saveUserState();
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

    if (status && status.error) {
      setMessage("run", "error", status.error);
    } else if (taskState === "SUCCESS") {
      setMessage("run", "ok", "Model Setup Data produced.");
    }
  }

  // The worker's percent; kept at its last value once the run ends, 100 on success.
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
  }

  // The worker's "%(asctime)s %(levelname)-8s %(message)s" line; anything else is rendered whole.
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

  function enterModel() {
    setMessage("model", null, "");
    if (!state.modelFile) {
      enterFiles();
      return;
    }
    var runId = state.modelFile.run_id;
    el.modelDownload.href = msdFilesUrl(state.selection, runId, "download");
    showView("model");

    if (state.model) {
      renderModel(state.model);
      return;
    }
    el.modelContext.hidden = true;
    el.modelGrid.hidden = true;
    el.modelLoading.hidden = false;
    request("GET", msdFilesUrl(state.selection, runId, "model"))
      .then(function (model) {
        el.modelLoading.hidden = true;
        // Another file may own the card by now.
        if (!state.modelFile || state.modelFile.run_id !== runId) {
          return;
        }
        state.model = model;
        renderModel(model);
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
    var context = model.context || {};
    var version = context.version || {};
    el.modelProject.textContent = shown((context.project || {}).name);
    el.modelPlatform.textContent = shown((context.platform || {}).name);
    el.modelVersion.textContent = shown(version.label);
    el.modelCurrent.hidden = !version.is_effective;
    el.modelGenerated.textContent = generatedAt(model.generated_at);
    el.modelContext.hidden = false;
  }

  // The counts the file's own metadata carries.
  var SCALE_CELLS = [
    { key: "apps", label: "Applications" },
    { key: "topics", label: "Topics" },
    { key: "nodes", label: "Nodes" },
    { key: "libraries", label: "Libraries" }
  ];

  function renderModelScale(model) {
    var scale = ((model.graph || {}).metadata || {}).scale || {};
    el.modelScale.textContent = "";
    SCALE_CELLS.forEach(function (cell) {
      var box = document.createElement("div");
      box.className = "scale__cell";
      var count = scale[cell.key];
      box.appendChild(span("scale__value", count === undefined ? "—" : String(count)));
      box.appendChild(span("scale__label", cell.label));
      el.modelScale.appendChild(box);
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
      inventory: enterInventory,
      run: enterProduce,
      model: enterModel
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
    el.candidateUnit.addEventListener("change", onCandidateUnitChange);
    el.candidateVersion.addEventListener("change", onCandidateVersionChange);

    // A tracked run is re-attached to; otherwise a new one is submitted.
    el.inventoryNext.addEventListener("click", function () {
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
  wireLogin();
  wireSources();
  wireModal();
  wireSelect();
  wireInventory();
  wireRun();
  boot();
})();
