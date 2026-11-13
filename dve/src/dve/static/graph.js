/* The two pictures of a Model Setup Data file on a vendored AntV G6 canvas:
 * the software view, a tree CSMS > CSS > CSCI > CSC > CSU with one relation
 * card per CSU (SRS DSM-SMM req 6, 7), and the hardware view, the networks
 * as switches in a cabinet, each with a bus line, and the nodes in their
 * cabinets tapping the lines. app.js drives both through
 * window.DsmHierarchyGraph; the search panel finds, opens, centres and
 * lights a box, row, switch or bus (SRS DSM-DVE req 43). */
(function () {
  "use strict";

  // The vendored G6 build asks for Object.hasOwn behind a feature check;
  // Firefox 90 has none, so an equivalent is supplied before the check.
  if (typeof Object.hasOwn !== "function") {
    Object.defineProperty(Object, "hasOwn", {
      configurable: true,
      writable: true,
      value: function hasOwn(object, key) {
        if (object === null || object === undefined) {
          throw new TypeError("Cannot convert undefined or null to object");
        }
        return Object.prototype.hasOwnProperty.call(Object(object), key);
      }
    });
  }

  // What the writer leaves where a source had nothing to give.
  var MISSING = "NOT_FOUND";

  // A hex colour at the given opacity.
  function withAlpha(hex, alpha) {
    var n = parseInt(hex.slice(1), 16);
    return "rgba(" + (n >> 16) + ", " + ((n >> 8) & 255) + ", " + (n & 255) + ", " + alpha + ")";
  }

  // The lines of both views share one hand: corner radius, rest width and
  // opacity, and the size of the dot where a tap meets its bus; the hover
  // and find states are set once in makeGraph. The hardware view's trunk lines alone draw at
  // full hue, 2px, with a glow.
  var LINE_RADIUS = 8;
  var LINE_WIDTH = 1.25;
  var LINE_ALPHA = 0.7;
  var END_MARK = 6;

  var COLOR = {
    cyan: "#22e6f5",
    line: withAlpha("#22e6f5", LINE_ALPHA)
  };

  // The hardware view's networks each take a hue, dealt in bus order, so a
  // line, its switch's lamp, its chip and its taps read as one network at
  // a glance: the app's cyan first, then nine softened instrument hues
  // (lavender, amber, aqua, gold, coral, green, indigo, tan, blue), warm
  // and cool alternating at varied brightness so neighbours in the order
  // never look alike: every adjacent pair clears the colour-blind
  // separation floor (OKLab, protan and deutan simulated) and the
  // normal-vision floor on the page's dark surface.
  var HUES = ["#22e6f5", "#aa95e8", "#f2a618", "#3ce8ce", "#e3cb53", "#e6867a", "#7ae78d", "#7d8bdb", "#de8f57", "#6ba5fb"];

  function hueOf(k) {
    return HUES[k % HUES.length];
  }

  // The containment levels above a CSU, top down (SRS DSM-SMM req 6): the
  // hierarchy field naming each and the tag its box carries.
  var LEVELS = [
    { key: "csms", field: "csms_name", tag: "CSMS" },
    { key: "css", field: "css_name", tag: "CSS" },
    { key: "csci", field: "csci_name", tag: "CSCI" },
    { key: "csc", field: "csc_name", tag: "CSC" }
  ];

  // The relation cards under a CSU (SRS DSM-SMM req 7): the relationships
  // key, the card label, the kind listed and the graph list holding it.
  var GROUPS = [
    { key: "runs_on", label: "RUNS ON", kind: "node", list: "nodes" },
    { key: "publishes_to", label: "PUB TO", kind: "topic", list: "topics" },
    { key: "subscribes_to", label: "SUB TO", kind: "topic", list: "topics" },
    { key: "sends", label: "SENDS", kind: "message", list: "messages" },
    { key: "receives", label: "RECEIVES", kind: "message", list: "messages" },
    { key: "uses", label: "USES", kind: "lib", list: "libraries" }
  ];

  var KIND_NAMES = { app: "CSU", node: "Node", topic: "Topic", message: "Message", lib: "Library", network: "Network", switch: "Switch" };

  // el.graph is the container app.js hands over; el.rowTip the hover card of the rows.
  var el = {};
  var graph = null;
  // The tree last built: its G6 data, the cards per entity id and the search index.
  var tree = null;
  // The model last loaded, for Collapse all to rebuild from.
  var lastModel = null;
  // The hardware view's filter: the networks and node groups picked in
  // the panel, by id and by name; none picked in a set means every one.
  var filter = { networks: {}, groups: {} };
  // The search's one lit target { nodeId, ref } (req 43), ref null for a box
  // alone; rowsHtml reads it so a re-render keeps the row lit.
  var lit = null;
  // Expansions queue on this promise, since G6 drops an expandElement call
  // while another is in flight.
  var pending = Promise.resolve();
  // Which picture is drawn: "sw" the system hierarchy tree, "hw" the
  // networks with their nodes (see the hardware section).
  var mode = "sw";
  // Each picture's state kept across a switch to the other, for the model
  // it was drawn from: the view's zoom and position, the boxes opened in
  // the tree, the filter and the pinned card of the hardware view. Taken
  // by snapshot() as the picture is left, spent by render() on its return.
  var kept = { sw: null, hw: null };
  var keptModel = null;

  /* ---------------------------------------------------------------- tree */

  function indexById(list) {
    var index = {};
    (list || []).forEach(function (item) {
      index[item.id] = item;
    });
    return index;
  }

  function shown(value) {
    return value === undefined || value === null || value === "" || value === MISSING ? "—" : String(value);
  }

  // A connection's bandwidth, in the Gb/s the file carries it on the link; the
  // writer's -1 for a source that had none reads as the dash the other missing
  // values take.
  function bandwidthText(value) {
    return typeof value !== "number" || !isFinite(value) || value <= 0 ? "—" : value + " Gb/s";
  }

  function compareText(a, b) {
    return a < b ? -1 : a > b ? 1 : 0;
  }

  function byLabel(a, b) {
    return compareText(a.data.label, b.data.label);
  }

  // The file's graph as G6 tree data (SRS DSM-SMM req 6, 7), open on the top
  // two levels; `open` starts every level above the units open instead.
  function buildTree(msd, open) {
    var g = msd.graph || {};
    var entities = {
      node: indexById(g.nodes),
      topic: indexById(g.topics),
      message: indexById(g.messages),
      lib: indexById(g.libraries)
    };
    var relationships = g.relationships || {};

    // Per application id, per relation key, the target ids.
    var targets = {};
    GROUPS.forEach(function (group) {
      (relationships[group.key] || []).forEach(function (edge) {
        var bucket = targets[edge.from] || (targets[edge.from] = {});
        (bucket[group.key] || (bucket[group.key] = [])).push(edge.to);
      });
    });

    var copies = {};
    var roots = [];
    var index = {};
    // For the search (req 43): each box's parent and label for a result's
    // path, the entries to match, and the first row seen per entity.
    var parents = {};
    var labels = {};
    var entries = [];
    var seen = {};

    function ensure(siblings, id, make) {
      if (!index[id]) {
        index[id] = make();
        siblings.push(index[id]);
      }
      return index[id];
    }

    (g.applications || []).forEach(function (app) {
      var hierarchy = app.system_hierarchy || {};
      var siblings = roots;
      var path = "";
      var parentId = null;
      LEVELS.forEach(function (level) {
        var name = hierarchy[level.field];
        if (!name || name === MISSING) {
          name = "Unassigned";
        }
        path += (path ? "/" : "") + name;
        var id = level.key + ":" + path;
        var node = ensure(siblings, id, function () {
          var made = { id: id, data: { level: level.key, tag: level.tag, label: name, count: 0 }, children: [] };
          // Every level under the system starts closed, unless opening all.
          if (level.key !== "csms") {
            made.style = { collapsed: !open };
          }
          parents[id] = parentId;
          labels[id] = name;
          entries.push({ type: "hierarchy", tag: level.tag, glyph: GLYPHS[level.key], id: id, label: name, text: name.toLowerCase() });
          return made;
        });
        node.data.count += 1;
        siblings = node.children;
        parentId = id;
      });

      var csu = {
        id: app.id,
        data: { level: "csu", tag: "CSU", kind: "app", ref: app.id, label: app.name, attrs: app },
        style: { collapsed: true },
        children: []
      };
      GROUPS.forEach(function (group) {
        var ids = (targets[app.id] || {})[group.key] || [];
        if (!ids.length) {
          return;
        }
        var groupNode = {
          id: app.id + "/" + group.key,
          data: { level: "group", label: group.label, kind: group.kind, count: ids.length, items: [] }
        };
        groupNode.data.items = ids.map(function (targetId) {
          var entity = entities[group.kind][targetId];
          (copies[targetId] || (copies[targetId] = [])).push(groupNode.id);
          var label = entity ? entity.name : targetId;
          if (!seen[targetId]) {
            seen[targetId] = { kind: group.kind, label: label };
          }
          return { ref: targetId, kind: group.kind, label: label, attrs: entity || {} };
        });
        parents[groupNode.id] = app.id;
        labels[groupNode.id] = group.label;
        // "pub", "pub to", "publishes to" and "runs on" all find the card.
        entries.push({
          type: "relation",
          tag: "Relation",
          glyph: GLYPHS[group.kind],
          id: groupNode.id,
          label: group.label,
          text: (group.label + " " + group.key.replace(/_/g, " ")).toLowerCase()
        });
        groupNode.data.items.sort(function (a, b) {
          return compareText(a.label, b.label);
        });
        csu.children.push(groupNode);
      });
      siblings.push(csu);
      (copies[app.id] || (copies[app.id] = [])).push(app.id);
      parents[app.id] = parentId;
      labels[app.id] = app.name;
      entries.push({ type: "csu", tag: "CSU", glyph: GLYPHS.csu, id: app.id, label: String(app.name), text: String(app.name).toLowerCase() });
    });

    // One search entry per entity with the cards listing it (req 43); an
    // entity used by no CSU is on no card, so it is off the tree.
    Object.keys(seen).forEach(function (ref) {
      var first = seen[ref];
      var cards = copies[ref].filter(function (id) {
        return id.indexOf("/") !== -1;
      });
      entries.push({
        type: first.kind,
        tag: KIND_NAMES[first.kind] || first.kind,
        glyph: GLYPHS[first.kind],
        ref: ref,
        label: String(first.label),
        text: String(first.label).toLowerCase(),
        copies: cards
      });
    });

    Object.keys(index).forEach(function (id) {
      index[id].children.sort(byLabel);
    });

    var root = roots.length === 1 ? roots[0] : { id: "root", data: { level: "root", tag: "DSM", label: "Systems" }, children: roots };
    if (roots.length > 1) {
      labels.root = "Systems";
      roots.forEach(function (top) {
        parents[top.id] = "root";
      });
    }
    var data = G6.treeToGraphData(root, {
      getEdgeData: function (source, target) {
        return { id: source.id + "->" + target.id, source: source.id, target: target.id };
      }
    });
    return { data: data, copies: copies, entities: entities, parents: parents, labels: labels, index: entries };
  }

  /* ------------------------------------------------------------ hardware */

  /* The hardware view: every network a switch, the switches stacked like
   * rack units in one network cabinet at the left of the picture, the
   * fullest network's at the top. From each switch's right side a stub
   * runs into the gutter beside the cabinet to its bus bar, a vertical
   * line down the picture in the network's hue; the bottom switch's bar
   * stands innermost, so the fullest bus stands outermost, nearest the
   * node cabinets, and no stub crosses a bar (those it passes start
   * lower). Every node on a network stands right of the bars by group,
   * the groups side by side in order, as many to a row as the stage is
   * wide: a group's headless nodes (no display) in a server cabinet,
   * stacked inside it like rack units, and its nodes with a display as
   * console cards in a column to the cabinet's left. From each card one
   * tap runs to every bus it is on, in its own lane and never under a
   * card: out of the card's side into a gutter beside its column (the
   * servers' to the right of the cabinet, the consoles' to their left),
   * down to the channel under its row, and along it leftwards to its bar
   * (the port names stay in the hover card). A stack of more than
   * UNITS_PER_COLUMN units splits into balanced columns (the switches
   * never do, their stack being the key to the bars): in a cabinet the
   * columns stand side by side behind one head and an inner column's taps
   * run under the next column to the gutter, hidden by the cabinet's back;
   * console columns each take their own gutter. Each column's taps leave a
   * little lower than the column before, so no two share a height, and
   * the lanes of a gutter are dealt lowest tap innermost, so no tap's run
   * across the gutter crosses another's run down it. The first row is at
   * least the network cabinet's height, so every channel runs under every
   * stub. Each node is drawn once. Positions are computed here, so the
   * graph runs with no layout. */

  var CONTENT_X = 24; // from the picture's left edge to the network cabinet
  var BUS_PITCH = 18; // from one bar to the next
  var BUS_W = BUS_PITCH; // a bar's node: the hover band, and the name tag that rides the line
  var LINE_X = BUS_W / 2; // the line's offset from the node's left: its middle
  var TAG_PAD = 6; // a tag's clearance from the bar's ends
  var TAG_STAGGER = 28; // every other bar's tag rides this much lower, so the row of tags breathes
  var RACK_RULE = 32; // the cabinet's head: the group's name and unit count over a rule
  var RACK_HEAD = RACK_RULE + 8; // the head and the clearance under its rule, to the first unit
  var RACK_PAD = 9; // the cabinet's rails: from its frame to the servers
  var RACK_FOOT = 8; // from the last unit to the cabinet's bottom rim
  var UNIT_GAP = 3; // between the stacked servers
  var UNITS_PER_COLUMN = 8; // the most units in one column before a stack splits
  var COLUMN_GAP = 6; // between the columns of a cabinet
  var TAP_SHIFT = 1.5; // each column's taps leave this much lower than the column before
  var CONSOLE_GAP = 12; // between a cabinet and its group's consoles, and between stacked consoles
  var RACK_GAP = 28; // between groups, and between rows of them
  var LANE_PITCH = 6; // between the taps running down a gutter
  var LANE_PAD = 10; // from a column's edge to its first lane, and past its last
  var GRID_GAP = 56; // from the last bar to the first cabinet
  var END_PAD = 40; // the bars' run past the last row's channel; LANE_PAD holds LINE_RADIUS
  var MIN_RUN = 160; // the shortest line down a bar (no node on any network)

  function hardwareIndex(msd) {
    var g = msd.graph || {};
    var nodes = indexById(g.nodes);
    var networks = indexById(g.networks);
    var relationships = g.relationships || {};
    var members = {};
    var homes = {};
    var units = {};
    (relationships.connects_to || []).forEach(function (link) {
      // A node on a network, as the writer emits it; anything else is skipped.
      if (nodes[link.from] && networks[link.to]) {
        (members[link.to] || (members[link.to] = [])).push({ node: link.from, device: link.device, dev_raw: link.dev_raw, bandwidth: link.bandwidth });
        (homes[link.from] || (homes[link.from] = [])).push({ network: link.to, device: link.device, dev_raw: link.dev_raw, bandwidth: link.bandwidth });
      }
    });
    (relationships.runs_on || []).forEach(function (edge) {
      units[edge.to] = (units[edge.to] || 0) + 1;
    });
    return { nodes: nodes, networks: networks, members: members, homes: homes, units: units };
  }

  function groupOf(node) {
    var group = (node || {}).group;
    return !group || group === MISSING ? "" : String(group);
  }

  // Whether a node has a display: a console rather than a rack server.
  // "none" is what the inventory says for a headless node.
  function hasDisplay(node) {
    var display = (node || {}).display;
    return !!display && display !== MISSING && String(display).toLowerCase() !== "none";
  }

  // A node's tap in words: the network's name, and the device in brackets when known.
  function linkLabel(link) {
    return link.name + (link.device && link.device !== MISSING ? " (" + link.device + ")" : "");
  }

  // A node's search entry; its path lists the networks it taps.
  function nodeEntry(nodeId, node, links) {
    return {
      type: "node",
      tag: "Node",
      glyph: GLYPHS.node,
      id: nodeId,
      label: String(node.name),
      text: String(node.name).toLowerCase(),
      path: links.map(linkLabel).join(" \u00b7 ")
    };
  }

  // The buses top to bottom: the fullest first (the shortest taps), the
  // empty ones last, names breaking ties.
  function orderBuses(index) {
    return Object.keys(index.networks).sort(function (a, b) {
      return (index.members[b] || []).length - (index.members[a] || []).length || compareText(index.networks[a].name, index.networks[b].name);
    });
  }

  // A stack of cards split into balanced columns of at most
  // UNITS_PER_COLUMN, filled top to bottom, then left to right.
  function columnsOf(cards) {
    var count = Math.ceil(cards.length / UNITS_PER_COLUMN);
    var per = count ? Math.ceil(cards.length / count) : 0;
    var columns = [];
    for (var c = 0; c < count; c += 1) {
      columns.push(cards.slice(c * per, (c + 1) * per));
    }
    return columns;
  }

  // Whether a set of picks lets the key through: every key when none is picked.
  function picked(set, key) {
    return !Object.keys(set).length || !!set[key];
  }

  // The hardware picture as G6 graph data with positions set (see above),
  // narrowed to the networks and groups picked (see filter).
  function buildHardware(msd, picks) {
    var index = hardwareIndex(msd);
    var labels = {};
    var entries = [];
    var nodes = [];
    var edges = [];
    picks = picks || { networks: {}, groups: {} };

    // The buses shown, in order, and the taps to them alone. A network's
    // hue follows its place in the full order, so a filter that drops
    // some never repaints the rest (the chips keep the same hues).
    var allBuses = orderBuses(index);
    var busIds = allBuses.filter(function (id) {
      return picked(picks.networks, id);
    });
    var shownBus = {};
    busIds.forEach(function (id) {
      shownBus[id] = true;
    });

    // The cards: every node of a picked group on a shown network, in group
    // order (the ungrouped last) and by name within a group.
    var cardIds = Object.keys(index.nodes)
      .filter(function (id) {
        return (
          picked(picks.groups, groupOf(index.nodes[id])) &&
          (index.homes[id] || []).some(function (link) {
            return shownBus[link.network];
          })
        );
      })
      .sort(function (a, b) {
        var ga = groupOf(index.nodes[a]);
        var gb = groupOf(index.nodes[b]);
        // The ungrouped nodes' cabinet comes last.
        return (ga === "") - (gb === "") || compareText(ga, gb) || compareText(index.nodes[a].name, index.nodes[b].name);
      });

    // A tap with its network's name in place of the id.
    function namedLink(link) {
      return { name: (index.networks[link.network] || {}).name || link.network, device: link.device, dev_raw: link.dev_raw };
    }

    // One port per tap on each bus: { key, y }.
    var busPorts = {};
    busIds.forEach(function (id) {
      busPorts[id] = [];
    });

    // A row of groups ends where it would pass the stage's width at the
    // opening zoom (the root scale).
    var wrapRight = Math.max(MIN_RUN, (el.graph ? el.graph.clientWidth : 0) / uiScale() - PADDING_HW[1] - PADDING_HW[3]);

    // The network cabinet: a switch unit per shown bus, in bus order, in
    // one column however many (the stack is the key to the bars); the
    // cabinet as wide as its switches or its head.
    var switches = busIds.map(function (busId) {
      var network = index.networks[busId];
      return {
        id: busId,
        data: {
          level: "switch",
          tag: "Switch",
          kind: "network",
          ref: busId,
          label: network.name,
          attrs: network,
          unit: true,
          count: (index.members[busId] || []).length,
          color: hueOf(allBuses.indexOf(busId))
        }
      };
    });
    var switchColumns = switches.length ? [switches] : [];
    var switchW = switches.reduce(function (widest, datum) {
      return Math.max(widest, widthOf(datum));
    }, MIN_WIDTH);
    var switchRackW = busIds.length
      ? Math.max(switchColumns.length * switchW + (switchColumns.length - 1) * COLUMN_GAP + 2 * RACK_PAD, rackHeadWidth("network", busIds.length, "switch"))
      : 0;
    switchW = busIds.length ? (switchRackW - 2 * RACK_PAD - (switchColumns.length - 1) * COLUMN_GAP) / switchColumns.length : 0;
    var switchRackH = busIds.length ? RACK_HEAD + switchColumns[0].length * BOX_HEIGHT + (switchColumns[0].length - 1) * UNIT_GAP + RACK_FOOT : 0;
    if (busIds.length) {
      // The cabinet first, so it draws under its switches.
      nodes.push({
        id: "rack:network",
        data: { level: "rack", label: "network", word: "switch", count: busIds.length, w: switchRackW, h: switchRackH },
        style: { x: CONTENT_X + switchRackW / 2, y: switchRackH / 2, zIndex: 0 }
      });
    }

    // The bars in the gutter right of the cabinet, each from its switch's
    // stub down: the lowest stub's innermost, so no stub crosses a bar
    // (those it passes start lower); the top (fullest) switch's stands
    // outermost, nearest the node cabinets (see above).
    var gutterX = CONTENT_X + switchRackW;
    var barX = {};
    var barTop = {};
    var hues = {};
    switchColumns.forEach(function (column, c) {
      column.forEach(function (datum, r) {
        var top = RACK_HEAD + r * (BOX_HEIGHT + UNIT_GAP);
        var exit = BOX_HEIGHT / 2 + c * TAP_SHIFT;
        datum.data.w = switchW;
        datum.data.ports = [{ key: "out", placement: [1, exit / BOX_HEIGHT] }];
        datum.style = { x: CONTENT_X + RACK_PAD + c * (switchW + COLUMN_GAP) + switchW / 2, y: top + BOX_HEIGHT / 2, zIndex: 1 };
        nodes.push(datum);
        barTop[datum.id] = top + exit;
        hues[datum.id] = datum.data.color;
      });
    });
    busIds
      .slice()
      .sort(function (a, b) {
        return barTop[b] - barTop[a];
      })
      .forEach(function (busId, lane) {
        barX[busId] = gutterX + LANE_PAD + lane * BUS_PITCH + BUS_W / 2;
      });

    // The cards grouped into cabinets, in group order.
    var cabinets = [];
    cardIds.forEach(function (nodeId) {
      var group = groupOf(index.nodes[nodeId]);
      var last = cabinets[cabinets.length - 1];
      if (!last || last.group !== group) {
        last = { group: group, ids: [] };
        cabinets.push(last);
      }
      last.ids.push(nodeId);
    });

    // The groups start past the bars.
    var startX = busIds.length ? gutterX + LANE_PAD + (busIds.length - 1) * BUS_PITCH + BUS_W + GRID_GAP : CONTENT_X;

    var x = startX;
    var rowTop = 0;
    // The first row is at least the network cabinet's height (see above).
    var rowH = switchRackH;
    // The rows of groups, each with the taps its cards drop:
    // { key, nodeId, i, network, exitY, laneX, node }.
    var rows = [{ top: 0, taps: [] }];
    function row() {
      return rows[rows.length - 1];
    }
    cabinets.forEach(function (cabinet) {
      // The group's cards: the servers as wide as the widest of them, the
      // consoles likewise.
      var serverW = MIN_WIDTH;
      var consoleW = MIN_WIDTH;
      var servers = [];
      var consoles = [];
      cabinet.ids.forEach(function (nodeId) {
        var node = index.nodes[nodeId];
        var console_ = hasDisplay(node);
        // Its taps to the shown buses, in bus order.
        var links = (index.homes[nodeId] || [])
          .filter(function (link) {
            return shownBus[link.network];
          })
          .sort(function (a, b) {
            return busIds.indexOf(a.network) - busIds.indexOf(b.network);
          });
        var datum = {
          id: nodeId,
          data: {
            level: "node",
            tag: "Node",
            kind: "node",
            ref: nodeId,
            label: node.name,
            attrs: node,
            unit: !console_,
            console: console_,
            units: index.units[nodeId] || 0,
            networks: links.map(namedLink)
          }
        };
        var card = { datum: datum, node: node, links: links };
        if (console_) {
          consoleW = Math.max(consoleW, widthOf(datum));
          consoles.push(card);
        } else {
          serverW = Math.max(serverW, widthOf(datum));
          servers.push(card);
        }
      });
      var count = servers.length;
      var serverColumns = columnsOf(servers);
      var consoleColumns = columnsOf(consoles);
      // The cabinet is as wide as its columns, or its head when that is longer.
      var rackW = count
        ? Math.max(serverColumns.length * serverW + (serverColumns.length - 1) * COLUMN_GAP + 2 * RACK_PAD, rackHeadWidth(cabinet.group || "ungrouped", count))
        : 0;
      serverW = count ? (rackW - 2 * RACK_PAD - (serverColumns.length - 1) * COLUMN_GAP) / serverColumns.length : 0;
      var rackH = count ? RACK_HEAD + serverColumns[0].length * BOX_HEIGHT + (serverColumns[0].length - 1) * UNIT_GAP + RACK_FOOT : 0;
      var consolesH = consoles.length ? consoleColumns[0].length * BOX_HEIGHT + (consoleColumns[0].length - 1) * CONSOLE_GAP : 0;
      // A gutter: a lane for every tap the cards beside it drop.
      function gutterWidth(cards) {
        var taps = cards.reduce(function (sum, card) {
          return sum + card.links.length;
        }, 0);
        return taps ? LANE_PAD * 2 + (taps - 1) * LANE_PITCH : 0;
      }
      // The consoles leave to the left when a cabinet stands at their
      // right, to the right otherwise, each column into its own gutter;
      // the servers always to the right of the cabinet.
      var consolesLeft = count > 0 && consoles.length > 0;
      var consolesW = consoleColumns.reduce(function (sum, column, c) {
        return sum + (c ? CONSOLE_GAP : 0) + gutterWidth(column) + consoleW;
      }, 0);
      var rightGutter = count ? gutterWidth(servers) : 0;
      var groupW = consolesW + (consolesLeft ? CONSOLE_GAP : 0) + rackW + rightGutter;
      var groupH = Math.max(rackH, consolesH);
      if (x > startX && x + groupW > wrapRight) {
        // A new row, under the channel the row above needs for its taps.
        row().bottom = rowTop + rowH;
        rowTop += rowH + Math.max(RACK_GAP, LANE_PAD * 2 + row().taps.length * LANE_PITCH);
        rowH = 0;
        x = startX;
        rows.push({ top: rowTop, taps: [] });
      }
      rowH = Math.max(rowH, groupH);

      // Cards placed ({ card, left, width, top, shift }), their taps
      // leaving the side `side` ("left" or "right") into the gutter that
      // starts at `gutterX`: a tap leaves at its own height, the first
      // bus's highest, `shift` lower in a later column; the lanes are
      // dealt from the gutter's near edge outward, lowest tap first.
      function placeCards(placements, side, gutterX) {
        var taps = [];
        placements.forEach(function (placement) {
          var card = placement.card;
          var datum = card.datum;
          var nodeId = datum.id;
          datum.data.w = placement.width;
          datum.data.ports = [];
          datum.style = { x: placement.left + placement.width / 2, y: placement.top + BOX_HEIGHT / 2, zIndex: 1 };
          nodes.push(datum);
          card.links.forEach(function (link, i) {
            var exit = (BOX_HEIGHT * (i + 1)) / (card.links.length + 1) + placement.shift;
            datum.data.ports.push({ key: "tap" + i, placement: [side === "right" ? 1 : 0, exit / BOX_HEIGHT] });
            taps.push({
              key: "tap:" + nodeId + ":" + i,
              nodeId: nodeId,
              i: i,
              network: link.network,
              link: link,
              node: card.node,
              exitY: placement.top + exit
            });
          });
          labels[nodeId] = card.node.name;
          entries.push(nodeEntry(nodeId, card.node, datum.data.networks));
        });
        taps.sort(function (a, b) {
          return b.exitY - a.exitY;
        });
        taps.forEach(function (tap, lane) {
          tap.laneX = side === "right" ? gutterX + LANE_PAD + lane * LANE_PITCH : gutterX - LANE_PAD - lane * LANE_PITCH;
          row().taps.push(tap);
        });
      }

      // A console column's placements down from the row's top.
      function consolePlacements(column, left) {
        return column.map(function (card, j) {
          return { card: card, left: left, width: consoleW, top: rowTop + j * (BOX_HEIGHT + CONSOLE_GAP), shift: 0 };
        });
      }

      var cursor = x;
      if (consolesLeft) {
        consoleColumns.forEach(function (column, c) {
          cursor += (c ? CONSOLE_GAP : 0) + gutterWidth(column);
          placeCards(consolePlacements(column, cursor), "left", cursor);
          cursor += consoleW;
        });
        cursor += CONSOLE_GAP;
      }
      if (count) {
        // The cabinet first, so it draws under its servers.
        nodes.push({
          id: "rack:" + cabinet.group,
          data: { level: "rack", label: cabinet.group || "ungrouped", empty: !cabinet.group, count: count, w: rackW, h: rackH },
          style: { x: cursor + rackW / 2, y: rowTop + rackH / 2, zIndex: 0 }
        });
        var placements = [];
        serverColumns.forEach(function (column, c) {
          column.forEach(function (card, j) {
            placements.push({
              card: card,
              left: cursor + RACK_PAD + c * (serverW + COLUMN_GAP),
              width: serverW,
              top: rowTop + RACK_HEAD + j * (BOX_HEIGHT + UNIT_GAP),
              shift: c * TAP_SHIFT
            });
          });
        });
        placeCards(placements, "right", cursor + rackW);
        cursor += rackW;
      } else {
        consoleColumns.forEach(function (column, c) {
          cursor += c ? CONSOLE_GAP : 0;
          placeCards(consolePlacements(column, cursor), "right", cursor + consoleW);
          cursor += consoleW + gutterWidth(column);
        });
      }
      x += groupW + RACK_GAP;
    });

    // The taps' runs, the same from every row: a tap drops from its lane to
    // the channel under its row and runs along it leftwards to its bar,
    // meeting the bar at the run's height. Along the channel the taps from
    // further left turn higher, so no run crosses another's drop.
    row().bottom = rowTop + rowH;
    rows.forEach(function (r) {
      var taps = r.taps.slice().sort(function (a, b) {
        return a.laneX - b.laneX;
      });
      var channelY = r.bottom + LANE_PAD;
      taps.forEach(function (tap) {
        var points = [[tap.laneX, tap.exitY], [tap.laneX, channelY]];
        busPorts[tap.network].push({ key: tap.key, y: channelY });
        channelY += LANE_PITCH;
        edges.push({
          id: tap.key,
          source: tap.nodeId,
          target: "bus:" + tap.network,
          data: {
            edge: "tap",
            color: hues[tap.network],
            sourcePort: "tap" + tap.i,
            targetPort: tap.key,
            points: points,
            device: tap.link.device,
            dev_raw: tap.link.dev_raw,
            bandwidth: tap.link.bandwidth,
            from: tap.node.name,
            to: (index.networks[tap.network] || {}).name
          }
        });
      });
    });
    // Every node is findable, a card or not (a node on no network has none).
    Object.keys(index.nodes).forEach(function (nodeId) {
      if (cardIds.indexOf(nodeId) !== -1) {
        return;
      }
      var node = index.nodes[nodeId];
      labels[nodeId] = node.name;
      entries.push(nodeEntry(nodeId, node, (index.homes[nodeId] || []).map(namedLink)));
    });

    // The bars beside the grid, each from its switch's stub down to one
    // shared end past the last row's channel, past the cabinet's foot and
    // at least MIN_RUN below the lowest stub; the stub joins the bar's top.
    var busBottom = Math.max(switchRackH + END_PAD, cardIds.length ? rowTop + rowH + LANE_PAD * 2 + row().taps.length * LANE_PITCH + END_PAD : 0);
    busIds.forEach(function (busId) {
      busBottom = Math.max(busBottom, barTop[busId] + MIN_RUN);
    });
    busIds.forEach(function (busId) {
      var network = index.networks[busId];
      var count = (index.members[busId] || []).length;
      var busTop = barTop[busId];
      var busH = busBottom - busTop;
      var barId = "bus:" + busId;
      nodes.push({
        id: barId,
        data: {
          level: "bus",
          tag: "Network",
          kind: "network",
          network: busId,
          label: network.name,
          attrs: network,
          empty: !count,
          w: BUS_W,
          h: busH,
          labelH: tagLength(network.name),
          // Alternate bars' tags ride lower (see stickLabels).
          stagger: ((barX[busId] - gutterX - LANE_PAD - BUS_W / 2) / BUS_PITCH) % 2 ? TAG_STAGGER : 0,
          color: hues[busId],
          count: count,
          ports: [{ key: "end", placement: [LINE_X / BUS_W, 1] }].concat(
            busPorts[busId].map(function (port) {
              return { key: port.key, placement: [LINE_X / BUS_W, (port.y - busTop) / busH] };
            })
          )
        },
        style: { x: barX[busId], y: busTop + busH / 2 }
      });
      edges.push({
        id: "stub:" + busId,
        source: busId,
        target: barId,
        data: {
          edge: "stub",
          color: hues[busId],
          empty: !count,
          sourcePort: "out",
          targetPort: "end",
          // Along the stub's height to the bar's line, then down it to the
          // end: the whole line, drawn in one stroke.
          points: [[barX[busId] - BUS_W / 2 + LINE_X, barTop[busId]]],
          from: network.name,
          to: network.name
        }
      });
      labels[busId] = network.name;
      entries.push({
        type: "network",
        tag: "Network",
        glyph: GLYPHS.bus,
        id: busId,
        label: String(network.name),
        text: String(network.name).toLowerCase(),
        path: plural(count, "node")
      });
    });

    return {
      data: { nodes: nodes, edges: edges },
      copies: {},
      entities: { node: index.nodes, network: index.networks },
      homes: index.homes,
      parents: {},
      labels: labels,
      index: entries
    };
  }

  /* -------------------------------------------------------------- styling */

  /* Every box of either view is the same card: a glyph on the left, a title
   * over a muted subtitle, and a bracketed [+]/[-] on the right when it can
   * open; the hardware view's units, consoles and cabinets wear the same
   * glass, rim, hover and find (app.css, "boxes" and "buses"). */

  var BOX_HEIGHT = 44;

  // The rows of a relation card: row height, bottom padding, and how many
  // rows the card shows at once; longer lists scroll inside the card.
  var ROW_HEIGHT = 26;
  var LIST_PAD = 6;
  var LIST_CAP = 8;


  // The lucide glyph (static/fonts) each kind of box carries; a relation
  // card wears the glyph of what it lists.
  var GLYPHS = {
    root: "lucide-ship",
    csms: "lucide-ship",
    css: "lucide-layers",
    csci: "lucide-boxes",
    csc: "lucide-box",
    csu: "lucide-cpu",
    node: "lucide-server",
    console: "lucide-monitor",
    switch: "lucide-network",
    topic: "lucide-radio",
    message: "lucide-mail",
    lib: "lucide-library",
    bus: "lucide-network"
  };

  var GROUP_SUBTITLES = { "RUNS ON": "Nodes", "PUB TO": "Topics", "SUB TO": "Topics", SENDS: "Messages", RECEIVES: "Messages", USES: "Libraries" };

  function childCount(datum) {
    return (datum.children || []).length;
  }

  function hasChildren(datum) {
    return childCount(datum) > 0;
  }

  function plural(count, word) {
    return count + " " + word + (count === 1 ? "" : /(ch|s|x)$/.test(word) ? "es" : "s");
  }

  // What one level down is called, for the count a card shows.
  var CHILD_NAMES = { root: "CSMS", csms: "CSS", css: "CSCI", csci: "CSC", csc: "CSU" };

  // The second line of the card: what the box is, and for the hierarchy
  // levels how many boxes sit directly below it.
  function subtitleOf(datum) {
    var data = datum.data || {};
    var attrs = data.attrs || {};
    switch (data.level) {
      case "root":
      case "csms":
      case "css":
      case "csci":
      case "csc":
        return (data.tag || "DSM") + " · " + plural(childCount(datum), CHILD_NAMES[data.level]);
      case "csu":
        return "CSU · v" + shown(attrs.version);
      case "node":
        // How many software units run on the node, and for a console (drawn
        // outside the cabinet) its group too, named like its cabinet would
        // be; the hardware stays in the hover card.
        return (data.console ? groupOf(attrs) || "ungrouped" : "Node") + " · " + plural(data.units || 0, "CSU");
      case "switch":
        // How many nodes are on the network; a bandwidth belongs to the node's
        // line, not to the switch, so the cabinet never has one to show.
        return (data.tag || "Switch") + " · " + plural(data.count || 0, "node");
      case "group":
        return (GROUP_SUBTITLES[data.label] || "Relation") + " · " + data.count;
      default:
        return "";
    }
  }

  function titleOf(datum) {
    var data = datum.data || {};
    return String(data.label || datum.id);
  }

  // A relation card wears the glyph of what it points at.
  function glyphOf(datum) {
    var data = datum.data || {};
    if (data.console) {
      return GLYPHS.console;
    }
    return GLYPHS[data.level === "group" ? data.kind : data.level] || "lucide-box-select";
  }

  // A relation card is the header plus up to LIST_CAP rows; the rest scroll.
  function heightOf(datum) {
    var data = datum.data || {};
    if (data.level === "bus" || data.level === "rack") {
      return data.h;
    }
    if (data.level !== "group") {
      return BOX_HEIGHT;
    }
    return BOX_HEIGHT + Math.min((data.items || []).length, LIST_CAP) * ROW_HEIGHT + LIST_PAD;
  }

  /* Card widths come from measuring the real text on an offscreen canvas,
   * once per font and string. The fonts and paddings mirror the box rules
   * of app.css; letter-spacing is added by hand since measureText ignores it. */

  var FONTS = {
    title: { font: "600 13px Barlow, sans-serif", spacing: 0.13 },
    sub: { font: "10px Barlow, sans-serif", spacing: 0.3 },
    row: { font: "11.5px Barlow, sans-serif", spacing: 0.23 },
    toggle: { font: "12px Barlow, sans-serif", spacing: 0 },
    tag: { font: "600 9px Barlow, sans-serif", spacing: 1.08 },
    rackName: { font: "600 11px Barlow, sans-serif", spacing: 1.54 },
    rackCount: { font: "10px Barlow, sans-serif", spacing: 1 }
  };

  // From the .bus__tag rule of app.css: the pill's end paddings and borders.
  var TAG_ENDS = 6 * 2 + 2;

  // The length a name tag takes down its bar.
  function tagLength(name) {
    return Math.ceil(textWidth("tag", String(name).toUpperCase()) + TAG_ENDS + 2);
  }

  // From the rack rules of app.css: the head's paddings and gap, and the
  // count pill's padding and border.
  var RACK_HEAD_PAD = { left: 11, right: 8, gap: 10, pill: 8 * 2 + 2 };

  // The cabinet width its head takes for the name beside the count pill, uncut.
  function rackHeadWidth(name, count, word) {
    var pill = RACK_HEAD_PAD.pill + textWidth("rackCount", plural(count, word || "node").toUpperCase());
    return Math.ceil(CARD_BORDER * 2 + RACK_HEAD_PAD.left + textWidth("rackName", String(name).toUpperCase()) + RACK_HEAD_PAD.gap + pill + RACK_HEAD_PAD.right + 4);
  }

  // From the box rules of app.css: the card border, the header's paddings, glyph and gaps,
  // the rows' margins and paddings (the left one past the rail and tick), and the scrollbar
  // beside long lists.
  var CARD_BORDER = 2;
  var HEAD_PAD = { left: 11, right: 10, gap: 10, glyph: 20, lamp: 14 };
  var ROW_PAD = { margin: 4, left: 26, right: 10, scrollbar: 12 };
  // Cards never grow past MAX_WIDTH; text that would not fit is cut with an
  // ellipsis and carries the full name as a hover title.
  var MIN_WIDTH = 140;
  var MAX_WIDTH = 240;

  var measurer = null;
  var measured = {};

  function textWidth(kind, text) {
    var key = kind + "\u0000" + text;
    if (measured[key] === undefined) {
      if (!measurer) {
        measurer = document.createElement("canvas").getContext("2d");
      }
      var spec = FONTS[kind];
      measurer.font = spec.font;
      measured[key] = measurer.measureText(text).width + text.length * spec.spacing;
    }
    return measured[key];
  }

  // The card width a header takes beyond its text, and the same for a row.
  function headExtra(datum) {
    var extra = CARD_BORDER * 2 + HEAD_PAD.left + HEAD_PAD.glyph + HEAD_PAD.gap + HEAD_PAD.right;
    if ((datum.data || {}).unit) {
      // A rack server's status lamp at the end of its front.
      extra += HEAD_PAD.lamp;
    }
    return hasChildren(datum) ? extra + HEAD_PAD.gap + textWidth("toggle", "[\u2212]") : extra;
  }

  function rowExtra(datum) {
    var items = (datum.data || {}).items || [];
    return CARD_BORDER * 2 + ROW_PAD.margin * 2 + ROW_PAD.left + ROW_PAD.right + (items.length > LIST_CAP ? ROW_PAD.scrollbar : 0);
  }

  // Whether a title will be cut at MAX_WIDTH.
  function titleCut(datum) {
    return headExtra(datum) + textWidth("title", titleOf(datum)) + 3 > MAX_WIDTH;
  }

  function widthOf(datum) {
    var data = datum.data || {};
    // A bus and a cabinet are sized by the build; so is a card in a cabinet,
    // as wide as the cabinet's widest.
    if (data.level === "bus" || data.level === "rack" || data.w) {
      return data.w;
    }
    var lines = Math.max(textWidth("title", titleOf(datum)), textWidth("sub", "[" + subtitleOf(datum) + "]"));
    var width = headExtra(datum) + lines;
    if (data.level === "group") {
      var extra = rowExtra(datum);
      (data.items || []).forEach(function (item) {
        width = Math.max(width, extra + textWidth("row", String(item.label)));
      });
    }
    // Slack for sub-pixel rounding and the title's synthetic bold, which lands
    // about a pixel wider than measured since Barlow ships at 400 only.
    return Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, Math.ceil(width) + 4));
  }

  function escapeHtml(text) {
    return String(text).replace(/[&<>"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
    });
  }

  // The classes a box wears for its G6 states: lit by the pointer (active),
  // lit by the search (highlight), or both.
  function modifiersOf(datum) {
    var states = datum.states || [];
    var classes = [];
    if (states.indexOf("active") !== -1) {
      classes.push("box--active");
    }
    if (states.indexOf("highlight") !== -1) {
      classes.push("box--highlight");
    }
    return classes.join(" ");
  }

  // The card's markup; every string from the file passes through escapeHtml.
  // data-id is the handle the search uses to find the drawn card.
  function boxHtml(datum, modifier) {
    var data = datum.data || {};
    var classes = "box box--" + data.level + (data.unit ? " box--unit" : "") + (data.console ? " box--console" : "") + (modifier ? " " + modifier : "");
    var toggle = hasChildren(datum) ? '<span class="box__toggle">[' + (G6.isCollapsed(datum) ? "+" : "−") + "]</span>" : "";
    // A switch wears its bus's hue (see .box--switch in app.css).
    var vars = data.level === "switch" && data.color ? ' style="--bus:' + data.color + '"' : "";
    return (
      '<div class="' + classes + '" data-id="' + escapeHtml(datum.id) + '"' + vars + ">" +
      '<div class="box__head">' +
      '<i class="box__glyph lucide ' + glyphOf(datum) + '"></i>' +
      '<span class="box__text">' +
      '<span class="box__title"' + (titleCut(datum) ? ' title="' + escapeHtml(titleOf(datum)) + '"' : "") + ">" + escapeHtml(titleOf(datum)) + "</span>" +
      '<span class="box__sub">' + escapeHtml(subtitleOf(datum)) + "</span>" +
      "</span>" +
      toggle +
      "</div>" +
      (data.level === "group" ? rowsHtml(datum) : "") +
      "</div>"
    );
  }

  // The rows of a relation card: its targets, scrolling past LIST_CAP of them.
  function rowsHtml(datum) {
    var data = datum.data || {};
    var items = data.items || [];
    var rows = items.map(function (item) {
      var isLit = !!(lit && lit.ref !== null && lit.nodeId === datum.id && lit.ref === item.ref);
      return (
        '<div class="list__row' + (isLit ? " list__row--highlight" : "") + '" data-ref="' + escapeHtml(item.ref) + '" data-kind="' + escapeHtml(item.kind) + '">' +
        '<span class="list__label">' + escapeHtml(item.label) + "</span>" +
        "</div>"
      );
    });
    return '<div class="list' + (items.length > LIST_CAP ? " list--scroll" : "") + '">' + rows.join("") + "</div>";
  }

  // A bus of the hardware view: the hover band down the bar (the line is
  // the network's edge under it) and the name tag riding the line in the
  // network's hue, read top to bottom. The tag slides down by the bar's
  // stuck offset, so it stays in view as the picture scrolls
  // (stickLabels); the node count stays in the hover card. The
  // box modifiers become bus ones.
  function busHtml(datum, modifier) {
    var data = datum.data || {};
    var classes = "bus" + (data.empty ? " bus--empty" : "") + (modifier ? " " + modifier.replace(/box--/g, "bus--") : "");
    var offset = stuck[datum.id] || TAG_PAD + (data.stagger || 0);
    return (
      '<div class="' + classes + '" data-id="' + escapeHtml(datum.id) + '"' + (data.color ? ' style="--bus:' + data.color + '"' : "") + ">" +
      '<div class="bus__line"></div>' +
      '<div class="bus__tag" style="top:' + offset + 'px">' + escapeHtml(data.label) + "</div>" +
      "</div>"
    );
  }

  // The tags are sticky: when a bar's top scrolls out under the title
  // block, its tag slides down the line to stay just under it, as far as
  // the bar's end. The offsets, in canvas units, are kept for the bus
  // markup and set on the DOM in place.
  var stuck = {};

  function stickLabels() {
    if (!graph || mode !== "hw" || !el.graph || !tree) {
      return;
    }
    var viewTop = graph.getCanvasByViewport([0, topClearance()])[1];
    (tree.data.nodes || []).forEach(function (datum) {
      var data = datum.data || {};
      if (data.level !== "bus") {
        return;
      }
      var top = datum.style.y - data.h / 2;
      var offset = Math.max(TAG_PAD, Math.min(viewTop - top + TAG_PAD, data.h - data.labelH - TAG_PAD - (data.stagger || 0))) + (data.stagger || 0);
      stuck[datum.id] = offset;
      var tag = el.graph.querySelector('.bus[data-id="' + datum.id + '"] .bus__tag');
      if (tag) {
        tag.style.top = offset + "px";
      }
    });
  }

  var stickQueued = false;

  function queueStick() {
    if (stickQueued) {
      return;
    }
    stickQueued = true;
    requestAnimationFrame(function () {
      stickQueued = false;
      stickLabels();
    });
  }

  // A cabinet of the hardware view: the software view's box as a frame,
  // its head the group's name in caps beside a pill with the unit count,
  // over a rule; a rail of mounting holes down each side, the units drawn
  // over it. No states. The head's and rails' measures go in as CSS
  // variables, so app.css draws in step with the layout.
  function rackHtml(datum) {
    var data = datum.data || {};
    // The rails' holes keep step with the units: five to a unit pitch.
    var vars = "--head:" + RACK_HEAD + "px;--rule:" + RACK_RULE + "px;--foot:" + RACK_FOOT + "px;--rail:" + RACK_PAD + "px;--pitch:" + (BOX_HEIGHT + UNIT_GAP) / 5 + "px";
    return (
      '<div class="rack" data-id="' + escapeHtml(datum.id) + '" style="' + vars + '">' +
      '<div class="rack__head">' +
      '<span class="rack__name">' + escapeHtml(data.label) + "</span>" +
      '<span class="rack__count">' + plural(data.count || 0, data.word || "node") + "</span>" +
      "</div>" +
      '<div class="rack__rail rack__rail--left"></div>' +
      '<div class="rack__rail rack__rail--right"></div>' +
      "</div>"
    );
  }

  function htmlOf(datum, modifier) {
    var level = (datum.data || {}).level;
    return level === "bus" ? busHtml(datum, modifier) : level === "rack" ? rackHtml(datum) : boxHtml(datum, modifier);
  }

  function nodeStyle(datum) {
    var data = datum.data || {};
    var width = widthOf(datum);
    var height = heightOf(datum);
    return {
      size: [width, height],
      // An HTML node hangs from its top-left corner; pull it onto its centre
      // so the layout's positions and the ports agree with the drawn card.
      dx: -width / 2,
      dy: -height / 2,
      innerHTML: htmlOf(datum, ""),
      label: false,
      port: false,
      // The hardware view sets each node's ports where its lines attach.
      ports: data.ports || [
        { key: "in", placement: "top" },
        { key: "out", placement: "bottom" },
        { key: "left", placement: "left" },
        { key: "tail", placement: [TAIL / width, 1] }
      ],
      cursor: data.level === "bus" || data.level === "rack" ? "default" : hasChildren(datum) || data.ref ? "pointer" : "default",
      // A bus is mostly empty space over the lines: only its label and line
      // take the pointer (see .bus in app.css); a cabinet takes none, so its
      // cards and the taps under it stay hoverable.
      pointerEvents: data.level === "bus" || data.level === "rack" ? "none" : "auto"
    };
  }

  /* --------------------------------------------------------------- layout */

  /* The mockup's shape as a G6 layout: levels above a CSU fan out top to
   * bottom, a CSC's CSUs stack as an indented list, and an opened CSU fans
   * its relation cards below it. Siblings are packed by outline (the
   * tidy-tree contour rule), so one open fan moves only the neighbours it
   * would touch. */

  var H_GAP = 18; // between siblings laid side by side
  var V_GAP = 34; // between a box and the row of children below it
  var LIST_GAP = 10; // between rows of a vertical list
  var LIST_DROP = 16; // between a box and the first row of its list
  var INDENT = 26; // a list row's inset from its parent's left edge
  var TAIL = 12; // where the list trunk leaves the parent's bottom edge

  var FAN_LEVELS = { root: true, csms: true, css: true, csci: true };

  class DsmTreeLayout extends G6.BaseLayout {
    get id() {
      return "dsm-tree";
    }
  }

  DsmTreeLayout.prototype.execute = function (model) {
    var byId = {};
    var isChild = {};
    (model.nodes || []).forEach(function (node) {
      byId[node.id] = node;
    });
    (model.nodes || []).forEach(function (node) {
      (node.children || []).forEach(function (child) {
        isChild[child] = true;
      });
    });
    var roots = (model.nodes || []).filter(function (node) {
      return !isChild[node.id];
    });

    // The open children the layout has to place: closed boxes hide theirs.
    function shownChildren(node) {
      if (!node || G6.isCollapsed(node)) {
        return [];
      }
      return (node.children || []).map(function (id) {
        return byId[id];
      }).filter(Boolean);
    }

    // A subtree laid out on its own with its box's top-left at (0, 0): its
    // node centres and an outline of y bands holding the extent of anything
    // drawn in each. Packing by outline lets a wide fan deep in one branch
    // push a neighbour only where the two meet.
    function layoutOf(node) {
      var ownW = widthOf(node);
      var ownH = heightOf(node);
      var nodes = [{ id: node.id, x: ownW / 2, y: ownH / 2 }];
      var bands = [{ y0: 0, y1: ownH, l: 0, r: ownW }];
      var children = shownChildren(node);
      var level = (node.data || {}).level;
      var subs = children.map(layoutOf);
      if (!children.length) {
        // Nothing beneath.
      } else if (FAN_LEVELS[level]) {
        // A row of children packed side by side, the box centred over the
        // span of their boxes; the orthogonal edges run in the strip between.
        var top = ownH + V_GAP;
        var packed = packRow(subs, top);
        var first = packed[0] + subs[0].ownW / 2;
        var last = packed[packed.length - 1] + subs[subs.length - 1].ownW / 2;
        var shift = ownW / 2 - (first + last) / 2;
        subs.forEach(function (sub, i) {
          adopt(nodes, bands, sub, packed[i] + shift, top);
        });
        bands.push({ y0: ownH, y1: top, l: Math.min(ownW / 2, first + shift), r: Math.max(ownW / 2, last + shift) });
      } else if (level === "csu") {
        // A CSU's relation groups fan out below it from its left edge; the
        // edges leave its tail and spread to the groups' centres.
        var groupTop = BOX_HEIGHT + V_GAP;
        var at = packRow(subs, groupTop);
        subs.forEach(function (sub, i) {
          adopt(nodes, bands, sub, at[i], groupTop);
        });
        var lastAt = at[at.length - 1] + subs[subs.length - 1].ownW / 2;
        bands.push({ y0: BOX_HEIGHT, y1: groupTop, l: TAIL, r: Math.max(TAIL + 1, lastAt) });
      } else {
        // A list: the rows stacked beneath, inset, each taking the full
        // height of its own subtree; the trunk runs down from the tail.
        var y = ownH + LIST_DROP;
        var lastCentre = y;
        subs.forEach(function (sub) {
          adopt(nodes, bands, sub, INDENT, y);
          lastCentre = y + sub.ownH / 2;
          y += sub.h + LIST_GAP;
        });
        bands.push({ y0: ownH, y1: lastCentre, l: TAIL, r: TAIL + 1 });
      }
      var outline = mergeBands(bands);
      var l = Infinity;
      var r = -Infinity;
      var h = 0;
      outline.forEach(function (band) {
        l = Math.min(l, band.l);
        r = Math.max(r, band.r);
        h = Math.max(h, band.y1);
      });
      return { nodes: nodes, outline: outline, ownW: ownW, ownH: ownH, l: l, r: r, h: h };
    }

    // Moves a laid-out subtree into its parent's coordinates at (dx, dy).
    function adopt(nodes, bands, sub, dx, dy) {
      sub.nodes.forEach(function (n) {
        nodes.push({ id: n.id, x: n.x + dx, y: n.y + dy });
      });
      sub.outline.forEach(function (band) {
        bands.push({ y0: band.y0 + dy, y1: band.y1 + dy, l: band.l + dx, r: band.r + dx });
      });
    }

    // The x offsets of subtrees laid side by side at the same top: each is
    // placed as far left as its outline allows beside everything before it,
    // keeping H_GAP clear wherever the outlines share a band of y.
    function packRow(subs, top) {
      var offsets = [];
      var taken = [];
      subs.forEach(function (sub, i) {
        var dx = i ? -Infinity : 0;
        if (i) {
          sub.outline.forEach(function (band) {
            taken.forEach(function (t) {
              if (band.y0 + top < t.y1 && band.y1 + top > t.y0) {
                dx = Math.max(dx, t.r + H_GAP - band.l);
              }
            });
          });
          if (dx === -Infinity) {
            dx = offsets[i - 1] + subs[i - 1].r - sub.l + H_GAP;
          }
        }
        offsets.push(dx);
        sub.outline.forEach(function (band) {
          taken.push({ y0: band.y0 + top, y1: band.y1 + top, l: band.l + dx, r: band.r + dx });
        });
        taken = mergeBands(taken);
      });
      return offsets;
    }

    // Overlapping bands folded into one outline: between every pair of
    // neighbouring y breakpoints, the extremes of the bands covering it.
    function mergeBands(bands) {
      var ys = [];
      bands.forEach(function (band) {
        ys.push(band.y0, band.y1);
      });
      ys.sort(function (a, b) {
        return a - b;
      });
      var out = [];
      for (var i = 0; i + 1 < ys.length; i++) {
        var y0 = ys[i];
        var y1 = ys[i + 1];
        if (y1 - y0 < 0.5) {
          continue;
        }
        var l = Infinity;
        var r = -Infinity;
        bands.forEach(function (band) {
          if (band.y0 <= y0 && band.y1 >= y1) {
            l = Math.min(l, band.l);
            r = Math.max(r, band.r);
          }
        });
        if (l === Infinity) {
          continue;
        }
        var prev = out[out.length - 1];
        if (prev && prev.y1 === y0 && prev.l === l && prev.r === r) {
          prev.y1 = y1;
        } else {
          out.push({ y0: y0, y1: y1, l: l, r: r });
        }
      }
      return out;
    }

    var placed = [];
    var x = 0;
    roots.forEach(function (root) {
      var sub = layoutOf(root);
      sub.nodes.forEach(function (n) {
        placed.push({ id: n.id, style: { x: n.x + x - sub.l, y: n.y } });
      });
      x += sub.r - sub.l + H_GAP * 3;
    });
    return Promise.resolve({ nodes: placed, edges: [] });
  };

  G6.register(G6.ExtensionCategory.LAYOUT, "dsm-tree", DsmTreeLayout);

  // A fan child hangs from its parent's bottom centre by the orthogonal
  // router; a list row leaves the trunk at the parent's tail with one elbow
  // at its height; a CSU's relation cards hang from a rail halfway down
  // the gap, which the CSU's tail drops to, so no card's line jogs about
  // the CSU's centre. The elbows are read from current positions on every
  // draw, since collapse-expand shifts positions after the layout.
  function edgeStyle(edge) {
    if (mode === "hw") {
      return hardwareEdgeStyle(edge);
    }
    var source = graph.getNodeData(edge.source);
    var target = graph.getNodeData(edge.target);
    var level = ((target || {}).data || {}).level;
    var sourceStyle = (source || {}).style || {};
    var targetStyle = (target || {}).style || {};
    if (level === "group") {
      var tailX = (sourceStyle.x || 0) - widthOf(source) / 2 + TAIL;
      var railY = (sourceStyle.y || 0) + BOX_HEIGHT / 2 + V_GAP / 2;
      return {
        router: false,
        sourcePort: "tail",
        targetPort: "in",
        controlPoints: [[tailX, railY], [targetStyle.x || 0, railY]]
      };
    }
    if (level !== "csu") {
      return { router: { type: "orth" }, sourcePort: "out", targetPort: "in" };
    }
    return {
      router: false,
      sourcePort: "tail",
      targetPort: "left",
      endArrow: false,
      controlPoints: [[(sourceStyle.x || 0) - widthOf(source) / 2 + TAIL, targetStyle.y || 0]]
    };
  }

  // A tap of the hardware view: out of the card's side to its lane, down
  // to the channel under its row and along it to its bar, with rounded
  // corners and a dot where it joins the bar, since its run crosses the
  // bars it passes; the device name stays in the hover card.
  // A network's line: from the switch's side, round the corner and down
  // the bar to its end, one 2px glowing stroke in the network's hue (the
  // bar node under it is only the hover band and the taps' ports); dashed
  // when no node is on it.
  function hardwareEdgeStyle(edge) {
    var data = edge.data || {};
    if (data.edge === "stub") {
      return {
        router: false,
        controlPoints: data.points || [],
        radius: LINE_RADIUS,
        sourcePort: data.sourcePort,
        targetPort: data.targetPort,
        stroke: data.color,
        lineWidth: 2,
        lineDash: data.empty ? [6, 5] : undefined,
        shadowColor: withAlpha(data.color, 0.6),
        shadowBlur: 8,
        endArrow: false
      };
    }
    var color = data.color ? withAlpha(data.color, LINE_ALPHA) : COLOR.line;
    return {
      router: false,
      controlPoints: data.points || [],
      radius: LINE_RADIUS,
      sourcePort: data.sourcePort,
      targetPort: data.targetPort,
      stroke: color,
      endArrow: true,
      endArrowType: "circle",
      endArrowSize: END_MARK,
      endArrowFill: color,
      endArrowStroke: color
    };
  }

  /* -------------------------------------------------------------- tooltip */

  function row(rows, key, value) {
    var dt = document.createElement("dt");
    dt.textContent = key;
    var dd = document.createElement("dd");
    dd.textContent = shown(value);
    rows.appendChild(dt);
    rows.appendChild(dd);
  }

  // The attribute rows of a node, topic, message or library, shown on hover (req 43).
  function entityRows(rows, kind, ref, attrs) {
    if (kind === "topic") {
      var qos = attrs.qos || {};
      row(rows, "Size", attrs.size === -1 ? MISSING : attrs.size);
      row(rows, "Frequency", attrs.frequency);
      row(rows, "Criticality", attrs.criticality);
      row(rows, "Durability", qos.durability);
      row(rows, "Reliability", qos.reliability);
      row(rows, "Transport priority", qos.transport_priority);
    } else if (kind === "message") {
      row(rows, "Message id", attrs.message_id);
      row(rows, "Size", attrs.size === -1 ? MISSING : attrs.size);
      row(rows, "Frequency", attrs.frequency);
    } else if (kind === "lib") {
      row(rows, "Version", attrs.version);
    }
    row(rows, "Id", ref);
    row(rows, "In", plural(((tree && tree.copies[ref]) || []).length, "CSU"));
  }

  // The hover card: a title with the kind beside it, then attribute rows.
  // textContent throughout: nothing from the file is parsed as markup.
  function tipCard(label, kindText, fill) {
    var box = document.createElement("div");
    box.className = "tip";
    var title = document.createElement("p");
    title.className = "tip__title";
    title.textContent = String(label);
    var kind = document.createElement("span");
    kind.className = "tip__kind";
    kind.textContent = kindText || "";
    title.appendChild(kind);
    box.appendChild(title);
    var rows = document.createElement("dl");
    rows.className = "tip__rows";
    fill(rows);
    box.appendChild(rows);
    return box;
  }

  // The hover card of a box: its attributes, and for a level the counts beneath (req 43).
  function tooltipFor(event, items) {
    var datum = items && items[0];
    if (!datum || !datum.data) {
      return "";
    }
    var data = datum.data;
    var attrs = data.attrs || {};
    if (data.edge === "stub") {
      // A switch's stub says nothing its switch does not.
      return "";
    }
    if (data.edge) {
      // A line of the hardware view: the port it leaves by, the bandwidth this
      // link carries and what it joins.
      return tipCard(data.from + " \u2014 " + data.to, "Connects to", function (rows) {
        row(rows, "Device", data.device);
        row(rows, "Raw device", data.dev_raw);
        row(rows, "Bandwidth", bandwidthText(data.bandwidth));
      });
    }
    return tipCard(data.label || datum.id, data.tag || KIND_NAMES[data.kind] || "", function (rows) {
      switch (data.level) {
        case "node":
          row(rows, "Group", attrs.group);
          row(rows, "Hardware", attrs.hw);
          row(rows, "OS", attrs.os);
          row(rows, "Middleware", attrs.mw);
          row(rows, "GPU", attrs.gpu);
          row(rows, "Display", attrs.display);
          row(rows, "Networks", (data.networks || []).map(linkLabel).join(", "));
          row(rows, "CSUs", data.units);
          row(rows, "Id", datum.id);
          break;
        case "bus":
        case "switch":
          row(rows, "Nodes", data.count);
          row(rows, "Id", attrs.id);
          break;
        case "root":
        case "csms":
        case "css":
        case "csci":
        case "csc":
          // The level below, named: "CSCIs 8" rather than "Children 8"; then
          // every software unit beneath.
          var below = childCount(datum);
          row(rows, CHILD_NAMES[data.level] + (below === 1 ? "" : "s"), below);
          row(rows, "Software units", data.count);
          break;
        case "csu":
          row(rows, "Version", attrs.version);
          row(rows, "Roles", (attrs.role || []).join(", "));
          row(rows, "Critical", attrs.criticality ? "yes" : "no");
          row(rows, "Priority", attrs.priority);
          row(rows, "Hot standby", attrs.hotstandby ? "yes" : "no");
          row(rows, "Description", (attrs.system_hierarchy || {}).csu_description);
          break;
        default:
          entityRows(rows, data.kind, data.ref, attrs);
      }
    });
  }

  /* The rows of a relation card are DOM, outside G6's tooltip plugin, so
   * they get the same card from a tooltip element of the page's own. */

  function showRowTip(rowEl, event) {
    var kind = rowEl.getAttribute("data-kind");
    var ref = rowEl.getAttribute("data-ref");
    var entity = ((tree && tree.entities[kind]) || {})[ref] || {};
    el.rowTip.textContent = "";
    el.rowTip.appendChild(
      tipCard(entity.name || rowEl.textContent, KIND_NAMES[kind] || kind, function (rows) {
        entityRows(rows, kind, ref, entity);
      })
    );
    el.rowTip.hidden = false;
    moveRowTip(event);
  }

  function moveRowTip(event) {
    var host = el.graph.getBoundingClientRect();
    var x = event.clientX - host.left + 14;
    var y = event.clientY - host.top + 14;
    // Keep the card inside the graph area.
    x = Math.min(x, host.width - el.rowTip.offsetWidth - 8);
    y = Math.min(y, host.height - el.rowTip.offsetHeight - 8);
    // left/top rather than a transform: the card's frosted fill is a fixed
    // background, and a transform would carry it along instead.
    el.rowTip.style.left = Math.max(0, x) + "px";
    el.rowTip.style.top = Math.max(0, y) + "px";
  }

  function hideRowTip() {
    el.rowTip.hidden = true;
  }

  // The event target's nearest ancestor matching the selector, or null.
  function closest(event, selector) {
    return event.target && event.target.closest ? event.target.closest(selector) : null;
  }

  /* ---------------------------------------------------------------- graph */

  // The stage runs under the stepper on the header line: a fitted tree
  // keeps clear of it at the top, and of the edges elsewhere.
  // The boxes are laid out in the design px of app.css's box rules; the
  // whole picture is then zoomed by the page's root scale (app.css: the
  // 1440x900 design scaled by the screen), so the tree grows with the UI.
  function uiScale() {
    var root = getComputedStyle(document.documentElement);
    var ref = parseFloat(root.getPropertyValue("--ref-root")) || 10;
    return (parseFloat(root.fontSize) || ref) / ref;
  }

  // Viewport margins, in the design's px; viewPx scales one by the root
  // scale so they keep pace with the title block beside them.
  var PADDING = [100, 24, 24, 24];
  // The hardware view opens at its top left; the top is the least clearance,
  // raised at fit time to pass under the title and context line, which
  // float over the canvas (topClearance).
  var PADDING_HW = [48, 24, 24, 24];
  var OVERLAY_GAP = 36;

  function viewPx(n) {
    return n * uiScale();
  }

  function stagePadding() {
    return (mode === "hw" ? PADDING_HW : PADDING).map(viewPx);
  }

  // How far the fixed title (the mode switch) and context line reach into
  // the canvas, plus a gap: where the first bus may start.
  function topClearance() {
    var host = el.graph.getBoundingClientRect();
    var bottom = -Infinity;
    [document.querySelector(".shell--graph .title"), document.getElementById("graph-context")].forEach(function (node) {
      if (node && !node.hidden) {
        var rect = node.getBoundingClientRect();
        if (rect.height) {
          bottom = Math.max(bottom, rect.bottom);
        }
      }
    });
    return Math.max(viewPx(PADDING_HW[0]), bottom - host.top + viewPx(OVERLAY_GAP));
  }

  function makeGraph(data) {
    return new G6.Graph({
      container: el.graph,
      // No autoFit: fitTree sets the opening view after the render.
      padding: stagePadding(),
      // Zoom range (req 43), relative to the root scale; the floor keeps a
      // fit-to-view of a fully opened CSC, thousands of pixels wide, from
      // shrinking the boxes out of sight.
      zoomRange: [0.2 * uiScale(), 3 * uiScale()],
      animation: false,
      data: data,
      // The hardware view's positions come with its data; the tree is laid out.
      layout: mode === "hw" ? undefined : { type: "dsm-tree" },
      node: {
        type: "html",
        style: nodeStyle,
        // Both states draw the card from the full state list, so a box that
        // is hovered and lit by the search shows both whichever G6 applies last.
        state: {
          active: function (datum) {
            return { innerHTML: htmlOf(datum, modifiersOf(datum)) };
          },
          highlight: function (datum) {
            return { innerHTML: htmlOf(datum, modifiersOf(datum)) };
          }
        }
      },
      edge: {
        type: "polyline",
        style: function (edge) {
          var style = edgeStyle(edge);
          if (style.radius === undefined) {
            style.radius = LINE_RADIUS;
          }
          style.stroke = style.stroke || COLOR.line;
          style.lineWidth = style.lineWidth || LINE_WIDTH;
          return style;
        },
        state: {
          // Lit white, like the hovered card: no halo, since the rows of a
          // list share one trunk and G6's halo would stack into a thick band.
          // A lit line rises above the rest, so the lines sharing its trunk
          // or crossing it never paint over the light.
          active: { stroke: "#ffffff", lineWidth: 1.75, endArrowFill: "#ffffff", endArrowStroke: "#ffffff", halo: false, zIndex: 2 },
          // A network's line found by the search: the mark's gold (see --mark in app.css).
          highlight: { stroke: "#ffd166", lineWidth: 2.5, shadowColor: "rgba(255, 209, 102, 0.6)", shadowBlur: 10, halo: false, zIndex: 3 }
        }
      },
      // Pan, zoom and click to expand or collapse (req 43). The hardware
      // picture is tall and narrow, so its wheel scrolls it up and down, and
      // zooms with Ctrl or Cmd held (a trackpad pinch arrives as a Ctrl
      // wheel too: see wheelZoom); it has nothing to fold.
      behaviors: ["drag-canvas"]
        .concat(
          mode === "hw"
            ? {
                type: "scroll-canvas",
                key: "scroll",
                direction: "y",
                enable: function (event) {
                  return !event.ctrlKey && !event.metaKey;
                }
              }
            : "zoom-canvas"
        )
        .concat(
          mode === "hw"
            ? []
            : {
                type: "collapse-expand",
                trigger: "click",
                animation: false,
                // The clicked box stays where it is on screen; the view does not
                // move, and neither opening nor closing lights it, the find's
                // gold being the search's alone.
                align: true
              }
        )
        .concat({ type: "hover-activate", degree: 1 }),
      // Attribute display on hover (req 43); the hardware view's lines too.
      plugins: [
        {
          type: "tooltip",
          key: "tooltip",
          trigger: "hover",
          enable: function (event, items) {
            var datum = items && items[0];
            if (!datum || !datum.data) {
              return false;
            }
            if (event.targetType === "edge") {
              return !!datum.data.edge;
            }
            return datum.data.level !== "group" && datum.data.level !== "rack" && event.targetType === "node";
          },
          getContent: function (event, items) {
            return Promise.resolve(tooltipFor(event, items));
          }
        }
      ]
    });
  }

  // The box the view is remembered by: the tree's root, or the hardware
  // picture's first node. Opening a box by a click shifts the laid-out
  // tree rather than the view, so a fresh layout puts the tree elsewhere;
  // the anchor's place on screen holds the view steady through that.
  function anchorOf() {
    var nodes = (tree && tree.data && tree.data.nodes) || [];
    for (var i = 0; i < nodes.length; i += 1) {
      if (mode !== "sw" || !tree.parents[nodes[i].id]) {
        return nodes[i].id;
      }
    }
    return null;
  }

  // The picture's state as the user left it (see kept).
  function snapshot() {
    if (!graph || !tree) {
      return null;
    }
    var shot = { zoom: graph.getZoom(), position: graph.getPosition(), anchor: anchorOf() };
    if (shot.anchor) {
      var at = graph.getNodeData(shot.anchor).style;
      shot.anchorAt = graph.getViewportByCanvas([at.x, at.y]);
    }
    if (mode === "sw") {
      shot.open = graph
        .getNodeData()
        .filter(function (datum) {
          return hasChildren(datum) && !G6.isCollapsed(datum);
        })
        .map(function (datum) {
          return datum.id;
        });
    } else {
      shot.filter = { networks: Object.assign({}, filter.networks), groups: Object.assign({}, filter.groups) };
      shot.pinned = pinned;
    }
    return shot;
  }

  // Opens the tree's boxes a snapshot had open.
  function reopen(data, open) {
    var wanted = {};
    open.forEach(function (id) {
      wanted[id] = true;
    });
    (data.nodes || []).forEach(function (datum) {
      if (wanted[datum.id] && datum.style) {
        datum.style.collapsed = false;
      }
    });
  }

  // Puts the view back where a snapshot had it, and the pinned card's light:
  // the anchor box back on its spot on screen, or, without one, the view's
  // position (in canvas units; G6's absolute translate is not its inverse,
  // so the view is moved by the difference, scaled to viewport px).
  function restoreView(shot) {
    return graph
      .zoomTo(shot.zoom, false)
      .then(function () {
        var anchor = shot.anchor ? nodeData(shot.anchor) : null;
        if (anchor && shot.anchorAt) {
          var now = graph.getViewportByCanvas([anchor.style.x, anchor.style.y]);
          return graph.translateBy([shot.anchorAt[0] - now[0], shot.anchorAt[1] - now[1]], false);
        }
        var at = graph.getPosition();
        return graph.translateBy([(shot.position[0] - at[0]) * shot.zoom, (shot.position[1] - at[1]) * shot.zoom], false);
      })
      .then(function () {
        stickLabels();
        return shot.pinned ? pin(shot.pinned) : undefined;
      });
  }

  // Draws the picture of the current mode; with a snapshot, as it was left.
  function render(msd, shot) {
    filter = shot && shot.filter ? shot.filter : { networks: {}, groups: {} };
    tree = mode === "hw" ? buildHardware(msd, filter) : buildTree(msd);
    if (shot && shot.open) {
      reopen(tree.data, shot.open);
    }
    lit = null;
    resetChips();
    fillFilters(mode === "hw" ? hardwareIndex(msd) : null);
    pressFilterChips();
    pending = Promise.resolve();
    if (graph) {
      graph.destroy();
      dropLayers();
    }
    graph = makeGraph(tree.data);
    // The pointer entering or leaving the lit card redraws it, which resets
    // its rows' scroll; bring the lit row back into view.
    graph.on("node:pointerenter", relitRow);
    graph.on("node:pointerleave", relitRow);
    // The bars' tags follow the view (see stickLabels).
    stuck = {};
    graph.on("aftertransform", queueStick);
    // A hovered card lights its reach (see reachOf): the networks' lines
    // and switches of a node, the path to the root of a software box.
    graph.on("node:pointerenter", function (event) {
      lightLines(event, true);
    });
    graph.on("node:pointerleave", function (event) {
      lightLines(event, false);
    });
    // A click keeps the hover's lighting until the next click.
    if (mode === "hw") {
      graph.on("node:click", function (event) {
        pin(event.target && event.target.id);
      });
      graph.on("canvas:click", function () {
        pin(null);
      });
    }
    pinned = null;
    // For the browser console and the page's tests.
    window.dsmGraph = graph;
    return graph
      .render()
      .then(function () {
        return shot ? restoreView(shot) : fitPicture();
      })
      .then(function () {
        if (el.panel) {
          el.panel.hidden = false;
          clearQuery();
        }
      });
  }

  // G6 5.1 leaves its DOM layer in the container when a graph is destroyed;
  // one per picture drawn would pile up and squeeze the next canvas.
  function dropLayers() {
    Array.prototype.slice.call(el.graph.children).forEach(function (child) {
      if (child !== el.rowTip) {
        el.graph.removeChild(child);
      }
    });
  }

  // The hover card does not notice the pointer jumping to a toolbar button.
  function hideTooltip() {
    var tooltip = graph && graph.getPluginInstance("tooltip");
    if (tooltip && tooltip.hide) {
      tooltip.hide();
    }
  }

  // The tree fitted to the stage but never enlarged past the root scale
  // (req 43): a wide tree shrinks to fit, a small one opens centred at its
  // natural size, which is the design size times the page's scale.
  function fitTree() {
    var cap = uiScale();
    return graph.fitView().then(function () {
      if (graph.getZoom() <= cap) {
        return undefined;
      }
      return graph.zoomTo(cap, false).then(function () {
        return graph.fitCenter();
      });
    });
  }

  // The hardware picture is tall and narrow: fitted to the stage's width,
  // never enlarged past the root scale, and opened at its top under the title block,
  // where the first buses are, rather than shrunk whole into the stage.
  function fitHardware() {
    var nodes = (tree && tree.data && tree.data.nodes) || [];
    if (!nodes.length) {
      return graph.fitCenter();
    }
    var left = Infinity;
    var right = -Infinity;
    var top = Infinity;
    nodes.forEach(function (node) {
      var data = node.data || {};
      var h = heightOf(node);
      var w = widthOf(node);
      left = Math.min(left, node.style.x - w / 2);
      right = Math.max(right, node.style.x + w / 2);
      top = Math.min(top, node.style.y - h / 2);
    });
    var size = graph.getSize();
    var cap = uiScale();
    var pad = stagePadding();
    var zoom = Math.max(0.2 * cap, Math.min(cap, (size[0] - pad[1] - pad[3]) / (right - left)));
    return graph
      .zoomTo(zoom, false)
      .then(function () {
        var at = graph.getViewportByCanvas([left, top]);
        return graph.translateBy([pad[3] - at[0], topClearance() - at[1]], false);
      })
      .then(stickLabels);
  }

  function fitPicture() {
    return mode === "hw" ? fitHardware() : fitTree();
  }

  // Rebuilds the tree with the given fold and draws it in one pass: one
  // layout, rather than one per box opened.
  function rebuild(open) {
    hideTooltip();
    lit = null;
    tree = buildTree(lastModel, open);
    graph.setData(tree.data);
    return graph.render().then(function () {
      // The results point at the rebuilt tree's entries.
      renderResults();
      return fitTree();
    });
  }

  // Expand all (open) or Collapse all (req 43), queued behind any expansion
  // in flight.
  function queueRebuild(open) {
    if (!graph || !tree) {
      return Promise.resolve();
    }
    pending = pending.then(function () {
      return rebuild(open);
    });
    return pending;
  }

  /* --------------------------------------------------------------- search */

  var LIMIT = 40;
  // Results come ranked by how the query hits (prefix, word start, inside),
  // then by type in this order, then shortest name first.
  var TYPE_ORDER = { csu: 0, hierarchy: 1, node: 2, network: 2, topic: 3, message: 4, lib: 5, relation: 6 };

  // The panel's state: the pressed chips, the rows on show, the selected row
  // (lit until the next pick or query change) and the entity refs whose
  // per-CSU lines are open.
  var types = [];
  var rows = [];
  var cursor = -1;
  var opened = {};

  // Matches the index by name, narrowed to the pressed types (req 43).
  function search(query, kinds) {
    var q = query.trim().toLowerCase();
    if (!tree || (!q && !kinds.length)) {
      return { total: 0, rows: [] };
    }
    var hits = [];
    tree.index.forEach(function (entry) {
      if (kinds.length && kinds.indexOf(entry.type) === -1) {
        return;
      }
      var at = q ? entry.text.indexOf(q) : 0;
      if (at === -1) {
        return;
      }
      hits.push({ entry: entry, rank: at === 0 ? 0 : /[\s_\-\/.]/.test(entry.text.charAt(at - 1)) ? 1 : 2 });
    });
    hits.sort(function (a, b) {
      return (
        a.rank - b.rank ||
        TYPE_ORDER[a.entry.type] - TYPE_ORDER[b.entry.type] ||
        a.entry.label.length - b.entry.label.length ||
        compareText(a.entry.label, b.entry.label)
      );
    });
    return {
      total: hits.length,
      rows: hits.slice(0, LIMIT).map(function (hit) {
        return hit.entry;
      })
    };
  }

  // The labels above a box, top down, without the synthetic root.
  function pathOf(id) {
    var names = [];
    var parent = tree.parents[id];
    while (parent) {
      if (parent !== "root") {
        names.unshift(tree.labels[parent]);
      }
      parent = tree.parents[parent];
    }
    return names;
  }

  function elem(tag, className, text) {
    var node = document.createElement(tag);
    node.className = className;
    if (text !== undefined) {
      node.textContent = text;
    }
    return node;
  }

  // One row of the results: glyph, name over its path, the kind at the end.
  // A copy line names the CSU, with the card and the CSC under it.
  function resultRow(row, i) {
    var entry = row.entry;
    var node = elem("div", "gsearch__row" + (row.copyId ? " gsearch__row--copy" : "") + (i === cursor ? " gsearch__row--active" : ""));
    node.setAttribute("role", "option");
    node.setAttribute("aria-selected", i === cursor ? "true" : "false");
    node.setAttribute("data-index", String(i));
    var glyph = elem("i", "gsearch__glyph lucide " + (row.copyId ? GLYPHS.csu : entry.glyph));
    var text = elem("span", "gsearch__text");
    node.appendChild(glyph);
    node.appendChild(text);
    if (row.copyId) {
      var csuId = row.copyId.split("/")[0];
      var csuName = tree.labels[csuId] || csuId;
      text.appendChild(elem("span", "gsearch__label", csuName));
      text.appendChild(elem("span", "gsearch__path", tree.labels[row.copyId] + " \u00b7 " + pathOf(csuId).slice(-1).join("")));
      node.title = csuName;
      return node;
    }
    text.appendChild(elem("span", "gsearch__label", entry.label));
    var path = entry.path !== undefined ? entry.path : entry.copies ? "in " + plural(entry.copies.length, "CSU") : pathOf(entry.id).join(" \u203a ");
    if (path) {
      text.appendChild(elem("span", "gsearch__path", path));
    }
    node.appendChild(elem("span", "gsearch__kind", entry.tag));
    node.title = entry.label;
    return node;
  }

  function renderResults() {
    if (!el.panel) {
      return;
    }
    var query = el.input.value;
    el.clear.hidden = !query;
    var found = search(query, types);
    rows = [];
    found.rows.forEach(function (entry) {
      rows.push({ entry: entry });
      if (entry.copies && opened[entry.ref]) {
        entry.copies.forEach(function (groupId) {
          rows.push({ entry: entry, copyId: groupId });
        });
      }
    });
    cursor = Math.min(cursor, rows.length - 1);
    el.results.textContent = "";
    rows.forEach(function (row, i) {
      el.results.appendChild(resultRow(row, i));
    });
    var idle = !query.trim() && !types.length;
    el.results.hidden = idle || !rows.length;
    el.count.hidden = idle;
    el.count.textContent =
      found.total === 0 ? "No matches" : (found.total === 1 ? "1 match" : found.total + " matches") + (found.total > LIMIT ? " \u00b7 first " + LIMIT + " shown" : "");
  }

  function restyleCursor() {
    Array.prototype.forEach.call(el.results.children, function (node, i) {
      node.classList.toggle("gsearch__row--active", i === cursor);
      node.setAttribute("aria-selected", i === cursor ? "true" : "false");
    });
  }

  function moveCursor(delta) {
    if (!rows.length) {
      return;
    }
    cursor = Math.max(0, Math.min(rows.length - 1, cursor + delta));
    restyleCursor();
    var active = el.results.children[cursor];
    if (active && active.scrollIntoView) {
      active.scrollIntoView({ block: "nearest" });
    }
  }

  function clearQuery() {
    if (!el.panel) {
      return;
    }
    el.input.value = "";
    opened = {};
    cursor = -1;
    renderResults();
  }

  // A result picked (req 43): a copy line or single-copy entity goes to its
  // row, an entity on several cards opens its lines, a box goes to itself.
  function pick(i) {
    var row = rows[i];
    if (!row) {
      return;
    }
    cursor = i;
    restyleCursor();
    var entry = row.entry;
    if (row.copyId) {
      goTo(row.copyId, entry.ref);
    } else if (entry.copies) {
      if (entry.copies.length === 1) {
        goTo(entry.copies[0], entry.ref);
      } else {
        opened[entry.ref] = !opened[entry.ref];
        cursor = opened[entry.ref] ? i + 1 : i;
        renderResults();
      }
    } else {
      goTo(entry.id, null);
    }
  }

  function nodeData(id) {
    try {
      return graph.getNodeData(id);
    } catch (error) {
      return undefined;
    }
  }

  // Adds or removes one state, keeping the others (hover's "active" among them).
  function withState(id, name, on) {
    var current = graph.getElementState(id);
    var has = current.indexOf(name) !== -1;
    if (on === has) {
      return Promise.resolve();
    }
    var next = on
      ? current.concat(name)
      : current.filter(function (state) {
          return state !== name;
        });
    return graph.setElementState(id, next, false);
  }

  // Lights one box, and the row ref names on it, as the find (req 43).
  function light(nodeId, ref) {
    return clearLit().then(function () {
      lit = { nodeId: nodeId, ref: ref === undefined ? null : ref };
      return withState(nodeId, "highlight", true).then(function () {
        return lightBar(nodeId, true);
      });
    });
  }

  // A switch's bar lights with it (a filtered-out bus has none).
  function lightBar(nodeId, on) {
    var datum = nodeData(nodeId);
    if (!datum || (datum.data || {}).level !== "switch") {
      return Promise.resolve();
    }
    try {
      graph.getEdgeData("stub:" + nodeId);
    } catch (error) {
      return Promise.resolve();
    }
    return withState("stub:" + nodeId, "highlight", on);
  }

  function clearLit() {
    if (!lit) {
      return Promise.resolve();
    }
    var old = lit;
    lit = null;
    return graph && nodeData(old.nodeId)
      ? withState(old.nodeId, "highlight", false).then(function () {
          return lightBar(old.nodeId, false);
        })
      : Promise.resolve();
  }

  // The drawn card of a box; ids hold ":" and "/", so no selector is built from them.
  function boxElement(nodeId) {
    var boxes = el.graph.querySelectorAll(".box");
    for (var i = 0; i < boxes.length; i += 1) {
      if (boxes[i].getAttribute("data-id") === nodeId) {
        return boxes[i];
      }
    }
    return null;
  }

  // Scrolls the lit row to the middle of its card's list, when the list scrolls.
  function scrollLitRow() {
    if (!lit || lit.ref === null) {
      return;
    }
    var box = boxElement(lit.nodeId);
    var row = box && box.querySelector(".list__row--highlight");
    var list = row && row.parentNode;
    if (list && list.classList.contains("list--scroll")) {
      list.scrollTop = row.offsetTop - list.offsetTop - (list.clientHeight - ROW_HEIGHT) / 2;
    }
  }

  // What a card reaches. In the hardware view, for a node, its taps, the
  // bars and lines of its networks and their switches; for a switch, its
  // line and bar, its nodes and their taps to it. In the software view,
  // the boxes above it up to the root and the edges between them. The
  // card itself first.
  function reachOf(id) {
    var datum = tree ? nodeData(id) : null;
    var level = datum ? (datum.data || {}).level : null;
    var ids = [];
    if (mode === "sw") {
      var child = id;
      var parent = datum ? tree.parents[child] : null;
      if (parent) {
        ids.push(id);
      }
      while (parent) {
        ids.push(parent + "->" + child, parent);
        child = parent;
        parent = tree.parents[child];
      }
    }
    if (level === "node") {
      ids.push(id);
      graph.getEdgeData().forEach(function (edge) {
        if ((edge.data || {}).edge === "tap" && edge.source === id) {
          ids.push(edge.id, edge.target);
        }
      });
      (tree.homes[id] || []).forEach(function (link) {
        ids.push("stub:" + link.network, link.network);
      });
    } else if (level === "switch") {
      ids.push(id, "stub:" + id, "bus:" + id);
      graph.getEdgeData().forEach(function (edge) {
        if ((edge.data || {}).edge === "tap" && edge.target === "bus:" + id) {
          ids.push(edge.id, edge.source);
        }
      });
    }
    return ids.filter(function (each) {
      try {
        graph.getElementState(each);
      } catch (error) {
        return false;
      }
      return true;
    });
  }

  // Lights or unlights a card's reach as the hover does.
  function lightReach(id, on) {
    return Promise.all(
      reachOf(id).map(function (each) {
        return withState(each, "active", on);
      })
    );
  }

  // A hovered card lights its reach beyond what hover-activate reaches
  // (its neighbours alone), and unlights it on leaving; a pinned card's
  // reach (hardware view) is put back after any leave, since the hover's
  // own unlighting may have crossed it.
  function lightLines(event, on) {
    if (!event.target || !tree) {
      return;
    }
    lightReach(event.target.id, on).then(function () {
      if (!on && pinned && graph) {
        lightReach(pinned, true);
      }
    });
  }

  // The card whose reach stays lit after a click (hardware view): clicking
  // it again, another card, or the canvas lets it go.
  var pinned = null;

  function pin(id) {
    var old = pinned;
    pinned = null;
    var released = old && graph && nodeData(old) ? lightReach(old, false) : Promise.resolve();
    if (!id || id === old) {
      return released;
    }
    return released.then(function () {
      if (!graph || !reachOf(id).length) {
        return undefined;
      }
      pinned = id;
      return lightReach(id, true);
    });
  }

  function relitRow(event) {
    if (lit && event.target && event.target.id === lit.nodeId) {
      requestAnimationFrame(scrollLitRow);
    }
  }

  // Opens every closed box above the target, lights it and centres the view
  // on it (req 43); selections queue behind one another.
  function goTo(nodeId, ref) {
    if (!graph || !tree) {
      return Promise.resolve();
    }
    hideTooltip();
    hideRowTip();
    if (!nodeData(nodeId)) {
      // A card the hardware filter keeps off the picture: the filter is
      // released and the picture redrawn whole, then the card is found.
      if (mode === "hw" && (Object.keys(filter.networks).length || Object.keys(filter.groups).length)) {
        filter = { networks: {}, groups: {} };
        pressFilterChips();
        return refilter().then(function () {
          return nodeData(nodeId) ? goTo(nodeId, ref) : undefined;
        });
      }
      // A node on no network has no card.
      return Promise.resolve();
    }
    var chain = [];
    var parent = tree.parents[nodeId];
    while (parent) {
      chain.unshift(parent);
      parent = tree.parents[parent];
    }
    pending = pending
      .then(function () {
        return chain.reduce(function (step, id) {
          return step.then(function () {
            var datum = nodeData(id);
            return datum && G6.isCollapsed(datum) ? graph.expandElement(id, false) : undefined;
          });
        }, Promise.resolve());
      })
      .then(function () {
        return light(nodeId, ref);
      })
      .then(function () {
        // After the box is drawn: centring reads its rendered bounds.
        return graph.focusElement(nodeId, false);
      })
      .then(scrollLitRow);
    return pending;
  }

  // Every chip released: a new picture starts with every type on.
  function resetChips() {
    types = [];
    cursor = -1;
    if (el.panel) {
      Array.prototype.forEach.call(el.panel.querySelectorAll(".gsearch__chip"), function (chip) {
        chip.setAttribute("aria-pressed", "false");
      });
    }
  }

  /* The hardware view's filters (the panel's .gfilter): a chip per
   * network, in bus order and in its hue, and a chip per node group. A
   * pressed chip narrows the picture to it; none pressed in a row means
   * every one. The chips are made afresh for every model. */

  function fillFilters(index) {
    if (!el.filter) {
      return;
    }
    var networks = el.filter.querySelector('[data-filter="networks"]');
    var groups = el.filter.querySelector('[data-filter="groups"]');
    networks.innerHTML = "";
    groups.innerHTML = "";
    if (!index) {
      el.filter.hidden = true;
      return;
    }
    orderBuses(index).forEach(function (busId, k) {
      networks.appendChild(filterChip("networks", busId, index.networks[busId].name, hueOf(k)));
    });
    var seen = {};
    Object.keys(index.nodes).forEach(function (nodeId) {
      seen[groupOf(index.nodes[nodeId])] = true;
    });
    Object.keys(seen)
      .sort(function (a, b) {
        return (a === "") - (b === "") || compareText(a, b);
      })
      .forEach(function (group) {
        groups.appendChild(filterChip("groups", group, group || "ungrouped", null));
      });
    networks.parentNode.hidden = !networks.childNodes.length;
    groups.parentNode.hidden = !groups.childNodes.length;
    el.filter.hidden = !networks.childNodes.length && !groups.childNodes.length;
  }

  function filterChip(set, key, label, hue) {
    var chip = document.createElement("button");
    chip.type = "button";
    chip.className = "gsearch__chip gfilter__chip";
    chip.setAttribute("aria-pressed", "false");
    chip.setAttribute("data-set", set);
    chip.setAttribute("data-key", key);
    if (hue) {
      chip.style.setProperty("--bus", hue);
      var dot = document.createElement("i");
      dot.className = "gfilter__dot";
      chip.appendChild(dot);
    }
    chip.appendChild(document.createTextNode(label));
    chip.addEventListener("click", function () {
      var on = chip.getAttribute("aria-pressed") !== "true";
      chip.setAttribute("aria-pressed", on ? "true" : "false");
      if (on) {
        filter[set][key] = true;
      } else {
        delete filter[set][key];
      }
      refilter();
    });
    return chip;
  }

  // Presses the chips of the current filter, after the chips are made afresh.
  function pressFilterChips() {
    if (!el.filter) {
      return;
    }
    Array.prototype.forEach.call(el.filter.querySelectorAll(".gfilter__chip"), function (chip) {
      var on = !!filter[chip.getAttribute("data-set")][chip.getAttribute("data-key")];
      chip.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }

  // Redraws the hardware picture under the current filter, fitted anew.
  function refilter() {
    if (!graph || mode !== "hw" || !lastModel) {
      return Promise.resolve();
    }
    hideTooltip();
    pending = pending
      .then(clearLit)
      .then(function () {
        tree = buildHardware(lastModel, filter);
        graph.setData(tree.data);
        return graph.render();
      })
      .then(function () {
        renderResults();
        return fitHardware();
      });
    return pending;
  }

  // The panel's parts and listeners, taken once with the container.
  function wirePanel(panel) {
    el.panel = panel;
    el.input = panel.querySelector("input");
    el.clear = panel.querySelector(".gsearch__clear");
    el.count = panel.querySelector(".gsearch__count");
    el.results = panel.querySelector(".gsearch__results");
    el.filter = panel.querySelector(".gfilter");
    el.input.addEventListener("input", function () {
      cursor = -1;
      renderResults();
    });
    // The clear button empties the query and, like Escape, takes the find's
    // light off the picture (a switch's line and bar with it).
    el.clear.addEventListener("click", function () {
      clearQuery();
      clearLit();
      el.input.focus();
    });
    Array.prototype.forEach.call(panel.querySelectorAll(".gsearch__chip"), function (chip) {
      chip.addEventListener("click", function () {
        var on = chip.getAttribute("aria-pressed") !== "true";
        var type = chip.getAttribute("data-type");
        chip.setAttribute("aria-pressed", on ? "true" : "false");
        types = on
          ? types.concat(type)
          : types.filter(function (t) {
              return t !== type;
            });
        cursor = -1;
        renderResults();
      });
    });
    el.results.addEventListener("click", function (event) {
      var row = closest(event, ".gsearch__row");
      if (row) {
        pick(Number(row.getAttribute("data-index")));
      }
    });
    panel.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        clearQuery();
        clearLit();
        return;
      }
      if (event.target !== el.input) {
        return;
      }
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        moveCursor(event.key === "ArrowDown" ? 1 : -1);
        event.preventDefault();
      } else if (event.key === "Enter" && rows.length) {
        pick(cursor < 0 ? 0 : cursor);
        event.preventDefault();
      }
    });
  }

  /* ------------------------------------------------------------------ api */

  var mounted = false;

  // Takes the container once, with the rows' hover card and wheel listeners
  // on it. The search panel is optional: without one the search is inert.
  // Zooms the hardware picture about the pointer by a wheel step, within
  // the graph's zoom range (see makeGraph); other wheels pass to G6.
  function wheelZoom(event) {
    if (!graph || mode !== "hw" || !(event.ctrlKey || event.metaKey)) {
      return;
    }
    event.preventDefault();
    // A mouse notch (about 100) zooms by a fifth; a pinch's small deltas
    // come in a smooth run of smaller steps.
    var step = Math.max(-200, Math.min(200, -event.deltaY));
    var zoom = graph.getZoom() * Math.exp(step * 0.002);
    var cap = uiScale();
    zoom = Math.max(0.2 * cap, Math.min(3 * cap, zoom));
    var rect = el.graph.getBoundingClientRect();
    graph.zoomTo(zoom, false, [event.clientX - rect.left, event.clientY - rect.top]);
  }

  function mount(container, panel) {
    if (mounted) {
      return;
    }
    mounted = true;
    el.graph = container;
    if (panel) {
      wirePanel(panel);
    }
    el.rowTip = document.createElement("div");
    el.rowTip.className = "tooltip tooltip--row";
    el.rowTip.hidden = true;
    el.graph.appendChild(el.rowTip);
    // The hardware view zooms on a Ctrl or Cmd wheel, and on a trackpad
    // pinch, which the browser delivers as a wheel with ctrlKey set.
    el.graph.addEventListener("wheel", wheelZoom, { passive: false });
    el.graph.addEventListener("mouseover", function (event) {
      var rowEl = closest(event, ".list__row");
      if (rowEl) {
        showRowTip(rowEl, event);
      }
    });
    el.graph.addEventListener("mousemove", function (event) {
      if (!el.rowTip.hidden) {
        if (closest(event, ".list__row")) {
          moveRowTip(event);
        } else {
          hideRowTip();
        }
      }
    });
    el.graph.addEventListener("mouseleave", hideRowTip);
    // A wheel over a card's rows scrolls them rather than zooming the view;
    // caught in the capture phase so G6 never forwards it.
    el.graph.addEventListener(
      "wheel",
      function (event) {
        var list = closest(event, ".list--scroll");
        if (!list) {
          return;
        }
        var atTop = list.scrollTop <= 0 && event.deltaY < 0;
        var atBottom = list.scrollTop + list.clientHeight >= list.scrollHeight - 1 && event.deltaY > 0;
        if (!atTop && !atBottom) {
          event.stopPropagation();
        }
      },
      true
    );
    window.addEventListener("resize", function () {
      if (graph) {
        graph.resize();
        queueStick();
      }
    });
  }

  // Draws the model's graph (SRS DSM-SMM req 6, 7) in the given mode, "sw"
  // or "hw" (the current one when none); resolves once the first picture
  // is on screen. Switching modes on the same model keeps the picture
  // left behind as it was (see kept) and brings back the one returned to.
  function load(msd, which) {
    if (!mounted) {
      return Promise.reject(new Error("mount() first"));
    }
    if (typeof G6 === "undefined" || !G6.Graph || !G6.treeToGraphData) {
      return Promise.reject(new Error("The graph library is missing."));
    }
    if (msd !== keptModel) {
      kept = { sw: null, hw: null };
      keptModel = msd;
    }
    if ((which === "sw" || which === "hw") && which !== mode) {
      if (graph && lastModel === msd) {
        kept[mode] = snapshot();
      }
      mode = which;
    }
    var shot = kept[mode];
    kept[mode] = null;
    lastModel = msd;
    return (document.fonts ? document.fonts.ready : Promise.resolve()).then(function () {
      return render(msd, shot);
    });
  }

  function fit() {
    if (!graph) {
      return Promise.resolve();
    }
    hideTooltip();
    return fitPicture();
  }

  // Lets the container's size change through: the canvas follows it.
  function resize() {
    if (graph) {
      graph.resize();
    }
  }

  function destroy() {
    if (graph) {
      graph.destroy();
      dropLayers();
      graph = null;
    }
    lit = null;
    pinned = null;
    tree = null;
    lastModel = null;
    if (el.panel) {
      clearQuery();
      el.panel.hidden = true;
    }
  }

  window.DsmHierarchyGraph = {
    mount: mount,
    load: load,
    fit: fit,
    resize: resize,
    // The hardware picture has nothing to fold.
    expandToCsu: function () {
      return mode === "hw" ? Promise.resolve() : queueRebuild(true);
    },
    collapseAll: function () {
      return mode === "hw" ? Promise.resolve() : queueRebuild(false);
    },
    destroy: destroy
  };
})();
