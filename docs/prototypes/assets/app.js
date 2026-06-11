/**
 * 音伴原型交互 — 非生产代码（含动效状态机）
 */

const SONGS = [
  { id: 1, name: "夜航船", artist: "示例歌手", reason: "安静舒缓，适合疲惫的晚上", tags: ["治愈", "民谣"] },
  { id: 2, name: "半句再见", artist: "示例歌手", reason: "旋律轻柔，帮你慢慢放松", tags: ["安静", "流行"] },
  { id: 3, name: "云上.walk", artist: "示例歌手", reason: "节奏平稳，像晚风一样", tags: ["放松", "独立"] },
  { id: 4, name: "木吉他练习曲", artist: "示例歌手", reason: "简单和弦，适合入门弹唱", tags: ["练习", "民谣"] },
  { id: 5, name: "雨后街角", artist: "示例歌手", reason: "淡淡忧郁但不沉重", tags: ["emo", "流行"] },
];

const PLAYLISTS = [
  { id: 1, name: "今晚治愈", desc: "适合疲惫夜晚的安静歌单", songIds: [1, 2, 3, 4, 5] },
  { id: 2, name: "周末练琴", desc: "适合周末练习的弹唱曲", songIds: [4, 1, 3] },
  { id: 3, name: "通勤路上", desc: "节奏适中，适合路上听", songIds: [3, 5, 2, 1, 4, 2, 3, 5] },
];

const SCORE_SONG_IDS = [1, 4];

/* 吉他六线谱和弦图（弦序 1→6：E A D G B e，左→右） */
const GUITAR_CHORD_SHAPES = {
  Am: {
    tops: ["×", "○", "", "", "", "○"],
    dots: [{ s: 3, f: 2, n: 2 }, { s: 4, f: 2, n: 3 }, { s: 5, f: 1, n: 1 }],
  },
  F: {
    tops: ["", "", "", "", "", ""],
    barre: { from: 1, to: 6, fret: 1 },
    dots: [{ s: 3, f: 2, n: 2 }, { s: 4, f: 3, n: 3 }, { s: 5, f: 3, n: 4 }],
  },
  C: {
    tops: ["×", "○", "", "○", "", "○"],
    dots: [{ s: 2, f: 3, n: 3 }, { s: 3, f: 2, n: 2 }, { s: 5, f: 1, n: 1 }],
  },
  G: {
    tops: ["", "", "○", "○", "○", ""],
    dots: [{ s: 1, f: 3, n: 4 }, { s: 2, f: 2, n: 1 }, { s: 6, f: 3, n: 3 }],
  },
};

/* 尤克里里四线谱和弦图（弦序：G C E A，左→右） */
const UKULELE_CHORD_SHAPES = {
  Am: { tops: ["", "○", "", "○"], dots: [{ s: 2, f: 2, n: 1 }] },
  F: { tops: ["", "○", "", "○"], dots: [{ s: 1, f: 2, n: 1 }, { s: 3, f: 1, n: 2 }] },
  C: { tops: ["○", "○", "○", ""], dots: [{ s: 4, f: 3, n: 3 }] },
  G: { tops: ["", "", "", ""], dots: [{ s: 1, f: 2, n: 1 }, { s: 2, f: 3, n: 3 }, { s: 3, f: 2, n: 2 }, { s: 4, f: 3, n: 4 }] },
};

const RHYTHM_PATTERNS = {
  guitar: {
    label: "节奏型",
    strings: 6,
    names: ["e", "B", "G", "D", "A", "E"],
    rows: [
      { marks: ["", "", "×", "", "", ""] },
      { marks: ["", "×", "", "×", "", ""] },
      { marks: ["", "", "×", "", "×", ""] },
      { marks: ["", "", "", "×", "", ""] },
      { marks: ["×", "", "", "", "", ""] },
      { marks: ["", "", "", "", "", ""] },
    ],
    beats: ["↓", "", "↑↓", "", "↑", ""],
  },
  ukulele: {
    label: "节奏型",
    strings: 4,
    names: ["A", "E", "C", "G"],
    rows: [
      { marks: ["", "", "", "×"] },
      { marks: ["", "×", "", ""] },
      { marks: ["×", "", "×", ""] },
      { marks: ["", "", "×", ""] },
    ],
    beats: ["↓", "", "↑", "↓"],
  },
};

const CHORDS = {
  guitar: {
    unique: ["Am", "F", "C", "G"],
    lines: [
      { section: "A", lyric: "后来 我总算学会了", chords: [{ name: "Am", at: 0 }] },
      { lyric: "如何去爱", chords: [{ name: "F", at: 0 }] },
      { lyric: "可惜你早已远去", chords: [{ name: "C", at: 0 }] },
      { lyric: "消失在人海", chords: [{ name: "G", at: 0 }] },
      { section: "B", lyric: "后来 终于在眼泪中明白", chords: [{ name: "Am", at: 0 }, { name: "F", at: 6 }] },
      { lyric: "有些人 一旦错过就不再", chords: [{ name: "C", at: 0 }, { name: "G", at: 10 }] },
    ],
  },
  ukulele: {
    unique: ["Am", "F", "C", "G"],
    lines: [
      { section: "A", lyric: "后来 我总算学会了", chords: [{ name: "Am", at: 0 }] },
      { lyric: "如何去爱", chords: [{ name: "F", at: 0 }] },
      { lyric: "可惜你早已远去", chords: [{ name: "C", at: 0 }] },
      { lyric: "消失在人海", chords: [{ name: "G", at: 0 }] },
      { section: "B", lyric: "后来 终于在眼泪中明白", chords: [{ name: "Am", at: 0 }, { name: "F", at: 6 }] },
      { lyric: "有些人 一旦错过就不再", chords: [{ name: "C", at: 0 }, { name: "G", at: 10 }] },
    ],
  },
};

const TOTAL_DURATION_SEC = 269; // 04:29

let state = {
  currentSong: SONGS[0],
  currentPlaylistId: 1,
  playing: false,
  progress: 32,
  scoreInstrument: "guitar",
  progressTimer: null,
  progressDragging: false,
  globalSearchOpen: false,
};

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

function openChat() {
  const float = $("#chat-float");
  const fab = $("#chat-fab");
  float.classList.remove("minimized");
  float.classList.add("open");
  fab.classList.add("hidden");
  $("#ai-chat-input")?.focus();
}

function closeChat() {
  $("#chat-float").classList.remove("open");
  $("#chat-float").classList.remove("minimized");
  syncChatFabVisibility();
}

function minimizeChat() {
  $("#chat-float").classList.remove("open");
  $("#chat-float").classList.add("minimized");
  syncChatFabVisibility();
}

function syncChatFabVisibility() {
  const fab = $("#chat-fab");
  const isHome = document.body.classList.contains("page-home-active");
  const floatOpen = $("#chat-float").classList.contains("open");
  if (isHome || floatOpen) {
    fab.classList.add("hidden");
  } else {
    fab.classList.remove("hidden");
  }
}

function updateChatForPage(pageId) {
  document.body.classList.toggle("page-player-active", pageId === "player");
  document.body.classList.toggle("page-home-active", pageId === "home");

  const float = $("#chat-float");

  if (pageId === "home") {
    float.classList.remove("open", "minimized");
    syncChatFabVisibility();
    return;
  }

  if (pageId === "player") {
    float.classList.remove("minimized");
    float.classList.add("open");
    $("#chat-fab").classList.add("hidden");
    return;
  }

  float.classList.remove("open", "minimized");
  syncChatFabVisibility();
}

function initChatFloat() {
  $("#btn-chat-close").addEventListener("click", closeChat);
  $("#btn-chat-minimize").addEventListener("click", minimizeChat);
  $("#chat-fab").addEventListener("click", openChat);
  $("#btn-header-chat").addEventListener("click", openChat);

  const sendChat = () => {
    const input = $("#ai-chat-input");
    const text = input.value.trim();
    if (!text) return;
    handleChatSend(text);
    input.value = "";
    openChat();
  };

  $("#btn-chat-send").addEventListener("click", (e) => {
    addRipple($("#btn-chat-send"), e);
    sendChat();
  });

  $("#ai-chat-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendChat();
  });
}

function showToast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2500);
}

function addRipple(el, e) {
  if (!el.classList.contains("ripple-host")) return;
  const rect = el.getBoundingClientRect();
  const size = Math.max(rect.width, rect.height);
  const ripple = document.createElement("span");
  ripple.className = "ripple";
  ripple.style.width = ripple.style.height = `${size}px`;
  ripple.style.left = `${e.clientX - rect.left - size / 2}px`;
  ripple.style.top = `${e.clientY - rect.top - size / 2}px`;
  el.appendChild(ripple);
  ripple.addEventListener("animationend", () => ripple.remove());
}

function bindRipple(selector) {
  $$(selector).forEach((el) => {
    el.classList.add("ripple-host");
    el.addEventListener("click", (e) => addRipple(el, e));
  });
}

function showTypingIndicator(container) {
  const el = document.createElement("div");
  el.className = "typing-indicator";
  el.id = "typing-indicator";
  el.innerHTML = "<span></span><span></span><span></span>";
  container.appendChild(el);
  container.scrollTop = container.scrollHeight;
  return el;
}

function removeTypingIndicator() {
  $("#typing-indicator")?.remove();
}

function animatePlayerMeta() {
  const title = $("#player-title");
  const artist = $("#player-artist");
  [title, artist].forEach((el) => {
    el.style.opacity = "0";
    el.style.transform = "translateY(8px)";
    requestAnimationFrame(() => {
      el.classList.add("player-meta-switch");
      el.style.opacity = "";
      el.style.transform = "";
    });
  });
}

function formatTime(seconds) {
  const s = Math.max(0, Math.floor(seconds));
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${String(m).padStart(2, "0")}:${String(r).padStart(2, "0")}`;
}

function updateProgressUI() {
  const fill = $("#progress-fill");
  const thumb = $("#progress-thumb");
  const bar = $("#progress-bar");
  const currentEl = $("#progress-current");
  if (!fill) return;

  const pct = Math.max(0, Math.min(100, state.progress));
  fill.style.width = `${pct}%`;
  if (thumb) thumb.style.left = `${pct}%`;
  if (currentEl) {
    currentEl.textContent = formatTime((pct / 100) * TOTAL_DURATION_SEC);
  }
  if (bar) bar.setAttribute("aria-valuenow", String(Math.round(pct)));
  fill.classList.toggle("playing-shimmer", state.playing && !state.progressDragging);
  fill.style.transition = state.progressDragging ? "none" : "";
  if (thumb) thumb.style.transition = state.progressDragging ? "none" : "";
}

function seekProgress(clientX) {
  const bar = $("#progress-bar");
  if (!bar) return;
  const rect = bar.getBoundingClientRect();
  const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
  state.progress = ratio * 100;
  updateProgressUI();
}

function initProgressBar() {
  const bar = $("#progress-bar");
  if (!bar) return;

  const onDragStart = (clientX) => {
    state.progressDragging = true;
    bar.classList.add("dragging");
    seekProgress(clientX);
  };

  const onDragMove = (clientX) => {
    if (!state.progressDragging) return;
    seekProgress(clientX);
  };

  const onDragEnd = () => {
    if (!state.progressDragging) return;
    state.progressDragging = false;
    bar.classList.remove("dragging");
    updateProgressUI();
  };

  bar.addEventListener("mousedown", (e) => {
    e.preventDefault();
    onDragStart(e.clientX);
  });

  window.addEventListener("mousemove", (e) => onDragMove(e.clientX));
  window.addEventListener("mouseup", onDragEnd);

  bar.addEventListener(
    "touchstart",
    (e) => {
      onDragStart(e.touches[0].clientX);
    },
    { passive: true }
  );

  window.addEventListener(
    "touchmove",
    (e) => {
      if (state.progressDragging) onDragMove(e.touches[0].clientX);
    },
    { passive: true }
  );

  window.addEventListener("touchend", onDragEnd);

  bar.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") {
      state.progress = Math.max(0, state.progress - 2);
      updateProgressUI();
    }
    if (e.key === "ArrowRight") {
      state.progress = Math.min(100, state.progress + 2);
      updateProgressUI();
    }
  });

  $("#progress-total").textContent = formatTime(TOTAL_DURATION_SEC);
}

function startProgressSimulation() {
  stopProgressSimulation();
  if (!state.playing) return;
  state.progressTimer = setInterval(() => {
    if (!state.playing || state.progressDragging) return;
    state.progress = Math.min(state.progress + 0.15, 100);
    updateProgressUI();
    if (state.progress >= 100) state.progress = 0;
  }, 200);
}

function stopProgressSimulation() {
  if (state.progressTimer) {
    clearInterval(state.progressTimer);
    state.progressTimer = null;
  }
}

function renderSongRows(container, onPlay) {
  if (!container) return;
  container.innerHTML = SONGS.slice(0, 5)
    .map(
      (s, i) => `
    <div class="song-row" data-id="${s.id}" style="animation-delay:${0.04 + i * 0.05}s">
      <div class="song-cover">封面</div>
      <div class="song-info">
        <div class="name">${s.name}</div>
        <div class="artist">${s.artist}</div>
        <span class="reason-tag">${s.reason}</span>
      </div>
      <button class="song-play-btn ripple-host" data-play="${s.id}" aria-label="播放">▶</button>
    </div>`
    )
    .join("");

  container.querySelectorAll("[data-play]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      addRipple(btn, e);
      const song = SONGS.find((s) => s.id === +btn.dataset.play);
      onPlay(song);
    });
  });

  container.querySelectorAll(".song-row").forEach((row) => {
    row.addEventListener("click", () => {
      const song = SONGS.find((s) => s.id === +row.dataset.id);
      onPlay(song);
    });
  });
}

function renderRecList() {
  const list = $("#rec-list");
  list.innerHTML = SONGS.map(
    (s, i) => `
    <div class="rec-card ${s.id === state.currentSong.id ? "active" : ""}" data-id="${s.id}" style="animation-delay:${0.05 + i * 0.05}s">
      <div class="song-cover">封面</div>
      <div class="song-info">
        <div class="name">${s.name}</div>
        <div class="artist">${s.artist}</div>
      </div>
    </div>`
  ).join("");

  list.querySelectorAll(".rec-card").forEach((card) => {
    card.addEventListener("click", () => {
      const prev = state.currentSong.id;
      state.currentSong = SONGS.find((s) => s.id === +card.dataset.id);
      if (prev !== state.currentSong.id) animatePlayerMeta();
      updatePlayerUI();
      renderRecList();
    });
  });
}

function updatePlayerUI() {
  const s = state.currentSong;
  $("#player-title").textContent = s.name;
  $("#player-artist").textContent = s.artist;
  $("#score-title").textContent = `${s.name} — 弹唱谱`;

  const disc = $("#vinyl-disc");
  const arm = $("#vinyl-arm");
  const playBtn = $("#btn-play-main");
  const armState = state.playing ? "playing" : "paused";

  if (state.playing) {
    disc.classList.add("playing");
    playBtn.textContent = "⏸";
    playBtn.classList.add("playing-pulse");
    startProgressSimulation();
  } else {
    disc.classList.remove("playing");
    playBtn.textContent = "▶";
    playBtn.classList.remove("playing-pulse");
    stopProgressSimulation();
  }

  if (arm) {
    arm.setAttribute("data-state", armState);
    arm.style.transform = state.playing ? "rotate(-8deg)" : "rotate(48deg)";
  }
  updateProgressUI();
}

function switchPage(pageId) {
  $$(".page").forEach((p) => p.classList.remove("active"));
  $$(".nav-link").forEach((n) => n.classList.remove("active"));

  const home = $("#page-home");
  const player = $("#page-player");
  player.classList.remove("active");

  if (pageId === "player") {
    home.classList.add("hidden");
    void player.offsetWidth;
    player.classList.add("active");
    updatePlayerUI();
    updateChatForPage("player");
    return;
  }

  home.classList.remove("hidden");

  const pageMap = {
    home: "page-home",
    playlists: "page-playlists",
    scores: "page-scores",
    mine: "page-mine",
    "playlist-detail": "page-playlist-detail",
  };
  const pageEl = $(`#${pageMap[pageId] || `page-${pageId}`}`);
  if (pageEl) {
    void pageEl.offsetWidth;
    pageEl.classList.add("active");
  }

  const nav = $(`.nav-link[data-page="${pageId}"]`);
  if (nav) nav.classList.add("active");
  else if (pageId === "playlist-detail") {
    $(`.nav-link[data-page="playlists"]`)?.classList.add("active");
  }

  updateChatForPage(pageId === "playlist-detail" ? "playlists" : pageId);
}

function goToPlayer(song) {
  const changed = state.currentSong.id !== song.id;
  state.currentSong = song;
  state.playing = true;
  if (changed) animatePlayerMeta();
  updatePlayerUI();
  renderRecList();
  switchPage("player");
  showToast(`正在播放：${song.name}`);
}

function openScore(instrument) {
  state.scoreInstrument = instrument;
  $$(".score-tab").forEach((t) => {
    t.classList.toggle("active", t.dataset.tab === instrument);
  });
  renderScore();
  $("#score-drawer").classList.add("open");
}

function renderChordDiagramGrid(name, shape, stringCount, delay = 0) {
  const frets = 4;
  const cols = Array.from({ length: stringCount }, (_, i) => i + 1);
  const topMarks = shape.tops || cols.map(() => "");

  const topHtml = cols
    .map((s) => `<span class="chord-top-mark">${topMarks[s - 1] || ""}</span>`)
    .join("");

  const fretCells = [];
  for (let f = 1; f <= frets; f += 1) {
    cols.forEach((s) => {
      const dot = (shape.dots || []).find((d) => d.s === s && d.f === f);
      const isBarre =
        shape.barre && shape.barre.fret === f && s >= shape.barre.from && s <= shape.barre.to;
      if (dot) {
        fretCells.push(
          `<span class="chord-fret-cell" data-s="${s}" data-f="${f}"><span class="chord-finger-dot">${dot.n || ""}</span></span>`
        );
      } else if (isBarre && s === Math.ceil((shape.barre.from + shape.barre.to) / 2)) {
        fretCells.push(
          `<span class="chord-fret-cell barre-cell" data-s="${s}" data-f="${f}"><span class="chord-barre-line"></span></span>`
        );
      } else {
        fretCells.push(`<span class="chord-fret-cell" data-s="${s}" data-f="${f}"></span>`);
      }
    });
  }

  return `
    <div class="chord-diagram" style="animation-delay:${delay}s">
      <div class="chord-diagram-name">${name}</div>
      <div class="chord-diagram-grid strings-${stringCount}">
        <div class="chord-top-row">${topHtml}</div>
        <div class="chord-nut"></div>
        <div class="chord-fret-board" style="--strings:${stringCount};--frets:${frets}">
          ${fretCells.join("")}
        </div>
      </div>
    </div>`;
}

function renderRhythmPattern(instrument) {
  const pat = RHYTHM_PATTERNS[instrument];
  const stringLines = pat.rows
    .map(
      (row, i) => `
      <div class="rhythm-string-row">
        <span class="rhythm-string-name">${pat.names[i]}</span>
        ${row.marks.map((m) => `<span class="rhythm-mark">${m}</span>`).join("")}
      </div>`
    )
    .join("");

  const beatsHtml = pat.beats
    .map((b) => `<span class="rhythm-beat">${b}</span>`)
    .join("");

  return `
    <div class="rhythm-pattern strings-${pat.strings}">
      <div class="rhythm-label">${pat.label}</div>
      <div class="rhythm-tab">${stringLines}</div>
      <div class="rhythm-beats">${beatsHtml}</div>
    </div>`;
}

function renderLyricLine(line, index) {
  const chordMap = {};
  (line.chords || []).forEach((c) => {
    chordMap[c.at] = c.name;
  });

  const chars = [...line.lyric];
  const cells = chars
    .map((ch, i) => {
      const chord = chordMap[i] || "";
      const display = ch === " " ? "\u00a0" : ch;
      return `
        <span class="char-cell">
          <span class="chord-slot">${chord}</span>
          <span class="char">${display}</span>
        </span>`;
    })
    .join("");

  const sectionHtml = line.section
    ? `<span class="lyric-section-tag">${line.section}</span>`
    : "";

  return `
    <div class="lyric-line" style="animation-delay:${0.08 + index * 0.06}s">
      ${sectionHtml}
      <div class="lyric-chars">${cells}</div>
    </div>`;
}

function matchText(text, query) {
  if (!query) return true;
  return text.toLowerCase().includes(query.trim().toLowerCase());
}

function searchSongs(query) {
  const q = query.trim();
  if (!q) return [];
  return SONGS.filter((s) => matchText(s.name, q) || matchText(s.artist, q) || s.tags.some((t) => matchText(t, q)));
}

function renderGlobalSearchDropdown(query) {
  const dropdown = $("#global-search-dropdown");
  const results = searchSongs(query);
  if (!query.trim()) {
    dropdown.classList.add("hidden");
    dropdown.innerHTML = "";
    return;
  }
  if (!results.length) {
    dropdown.innerHTML = '<div class="search-dropdown-empty">未找到相关歌曲</div>';
    dropdown.classList.remove("hidden");
    return;
  }
  dropdown.innerHTML = results
    .map(
      (s) => `
    <button type="button" class="search-result-item" data-id="${s.id}">
      <div class="song-cover">封面</div>
      <div class="song-info">
        <div class="name">${s.name}</div>
        <div class="artist">${s.artist}</div>
      </div>
    </button>`
    )
    .join("");
  dropdown.querySelectorAll(".search-result-item").forEach((item) => {
    item.addEventListener("click", () => {
      const song = SONGS.find((s) => s.id === +item.dataset.id);
      $("#global-search").value = "";
      dropdown.classList.add("hidden");
      goToPlayer(song);
    });
  });
  dropdown.classList.remove("hidden");
}

function initGlobalSearch() {
  const input = $("#global-search");
  const dropdown = $("#global-search-dropdown");
  const wrap = $("#header-search-wrap");

  input.addEventListener("input", () => renderGlobalSearchDropdown(input.value));
  input.addEventListener("focus", () => {
    if (input.value.trim()) renderGlobalSearchDropdown(input.value);
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      const first = searchSongs(input.value)[0];
      if (first) {
        input.value = "";
        dropdown.classList.add("hidden");
        goToPlayer(first);
      }
    }
    if (e.key === "Escape") {
      dropdown.classList.add("hidden");
      input.blur();
    }
  });

  document.addEventListener("click", (e) => {
    if (!wrap.contains(e.target)) dropdown.classList.add("hidden");
  });
}

function renderPlaylistGrid(query = "") {
  const grid = $("#playlist-grid");
  const empty = $("#playlist-empty");
  const list = PLAYLISTS.filter((p) => matchText(p.name, query) || matchText(p.desc, query));

  grid.innerHTML = list
    .map(
      (p) => `
    <div class="playlist-card" data-id="${p.id}">
      <div class="playlist-cover">♪</div>
      <h3>${p.name}</h3>
      <p>${p.songIds.length} 首歌曲</p>
    </div>`
    )
    .join("");

  empty.classList.toggle("hidden", list.length > 0);

  grid.querySelectorAll(".playlist-card").forEach((card) => {
    card.addEventListener("click", () => openPlaylistDetail(+card.dataset.id));
  });
}

function openPlaylistDetail(playlistId) {
  state.currentPlaylistId = playlistId;
  const pl = PLAYLISTS.find((p) => p.id === playlistId);
  if (!pl) return;
  $("#playlist-detail-title").textContent = pl.name;
  $("#playlist-detail-desc").textContent = `${pl.desc} · ${pl.songIds.length} 首`;
  $("#playlist-song-search").value = "";
  renderPlaylistSongs("");
  switchPage("playlist-detail");
}

function renderPlaylistSongs(query = "") {
  const pl = PLAYLISTS.find((p) => p.id === state.currentPlaylistId);
  const container = $("#playlist-songs");
  const empty = $("#playlist-song-empty");
  if (!pl) return;

  const songs = pl.songIds
    .map((id) => SONGS.find((s) => s.id === id))
    .filter(Boolean)
    .filter((s) => matchText(s.name, query) || matchText(s.artist, query));

  container.innerHTML = songs
    .map(
      (s) => `
    <div class="song-table-row" data-id="${s.id}">
      <button class="song-play-btn" aria-label="播放">▶</button>
      <div class="song-cover">封面</div>
      <div class="song-info"><div class="name">${s.name}</div><div class="artist">${s.artist}</div></div>
    </div>`
    )
    .join("");

  empty.classList.toggle("hidden", songs.length > 0);

  container.querySelectorAll(".song-table-row").forEach((row) => {
    row.addEventListener("click", () => {
      goToPlayer(SONGS.find((s) => s.id === +row.dataset.id));
    });
  });
}

function renderScoreLib(query = "") {
  const container = $("#score-lib-list");
  const empty = $("#score-empty");
  const songs = SCORE_SONG_IDS.map((id) => SONGS.find((s) => s.id === id))
    .filter(Boolean)
    .filter((s) => matchText(s.name, query) || matchText(s.artist, query));

  container.innerHTML = songs
    .map(
      (s) => `
    <div class="song-table-row score-lib-row" data-id="${s.id}">
      <div class="song-cover">封面</div>
      <div class="song-info"><div class="name">${s.name}</div><div class="artist">${s.artist} · 吉他 / 尤克里里</div></div>
      <button class="btn btn-outline btn-sm btn-view-score" data-id="${s.id}">查看谱面</button>
    </div>`
    )
    .join("");

  empty.classList.toggle("hidden", songs.length > 0);

  container.querySelectorAll(".btn-view-score").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const song = SONGS.find((s) => s.id === +btn.dataset.id);
      state.currentSong = song;
      updatePlayerUI();
      openScore("guitar");
    });
  });

  container.querySelectorAll(".score-lib-row").forEach((row) => {
    row.addEventListener("click", () => {
      const song = SONGS.find((s) => s.id === +row.dataset.id);
      state.currentSong = song;
      updatePlayerUI();
      openScore("guitar");
    });
  });
}

function initPageSearch() {
  $("#playlist-search")?.addEventListener("input", (e) => renderPlaylistGrid(e.target.value));
  $("#playlist-song-search")?.addEventListener("input", (e) => renderPlaylistSongs(e.target.value));
  $("#score-search")?.addEventListener("input", (e) => renderScoreLib(e.target.value));
}

function renderScore() {
  const instrument = state.scoreInstrument;
  const score = CHORDS[instrument];
  const shapes = instrument === "guitar" ? GUITAR_CHORD_SHAPES : UKULELE_CHORD_SHAPES;
  const stringCount = instrument === "guitar" ? 6 : 4;

  $("#chord-diagrams").innerHTML = score.unique
    .map((c, i) => renderChordDiagramGrid(c, shapes[c] || { tops: [], dots: [] }, stringCount, 0.05 + i * 0.05))
    .join("");

  $("#rhythm-pattern").innerHTML = renderRhythmPattern(instrument);
  $("#chord-lines").innerHTML = score.lines.map(renderLyricLine).join("");
}

function handleChatSend(text) {
  if (!text.trim()) return;
  const messages = $("#ai-messages");
  const userBubble = document.createElement("div");
  userBubble.className = "bubble bubble-user bubble-enter";
  userBubble.textContent = text;
  messages.appendChild(userBubble);
  messages.scrollTop = messages.scrollHeight;

  showTypingIndicator(messages);

  setTimeout(() => {
    removeTypingIndicator();
    const aiBubble = document.createElement("div");
    aiBubble.className = "bubble bubble-ai bubble-enter";
    aiBubble.innerHTML = `我理解你现在的感受。根据你的心情，我为你挑选了这些歌：<div class="song-rec-inline" id="ai-rec-new"></div>`;
    messages.appendChild(aiBubble);
    renderSongRows($("#ai-rec-new"), goToPlayer);
    messages.scrollTop = messages.scrollHeight;
  }, 900);
}

function closeOnboarding() {
  const overlay = $("#onboarding");
  overlay.classList.add("closing");
  setTimeout(() => {
    overlay.classList.add("hidden");
    overlay.classList.remove("closing");
    showToast("偏好已保存，开始探索吧");
  }, 280);
}

function initOnboarding() {
  if (localStorage.getItem("yinban_onboarded")) {
    $("#onboarding").classList.add("hidden");
    return;
  }
  $("#onboarding").classList.remove("hidden");

  $$("#onboarding .chip[data-level]").forEach((chip) => {
    chip.addEventListener("click", () => {
      $$("#onboarding .chip[data-level]").forEach((c) => c.classList.remove("selected"));
      chip.classList.add("selected");
    });
  });

  $$("#onboarding .chip[data-style]").forEach((chip) => {
    chip.addEventListener("click", () => chip.classList.toggle("selected"));
  });

  $("#btn-onboard-done").addEventListener("click", () => {
    localStorage.setItem("yinban_onboarded", "1");
    closeOnboarding();
  });
}

function init() {
  initOnboarding();
  initChatFloat();
  initProgressBar();
  initGlobalSearch();
  initPageSearch();
  updateChatForPage("home");

  renderSongRows($("#ai-rec-initial"), goToPlayer);
  renderRecList();
  renderPlaylistGrid();
  renderScoreLib();
  updatePlayerUI();
  renderScore();

  bindRipple(".mood-tag, .btn-primary, .ctrl-btn.play-main, #btn-guitar, #btn-ukulele, #btn-add-playlist");

  $$(".nav-link").forEach((link) => {
    link.addEventListener("click", () => switchPage(link.dataset.page));
  });

  const heroSend = $("#btn-hero-send");
  heroSend.addEventListener("click", (e) => {
    addRipple(heroSend, e);
    heroSend.classList.add("sending");
    setTimeout(() => heroSend.classList.remove("sending"), 600);
    const val = $("#hero-input").value;
    handleChatSend(val || "今天有点累，想听点安静的");
    setTimeout(() => goToPlayer(SONGS[0]), 400);
  });

  $("#hero-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") heroSend.click();
  });

  $$(".mood-tag").forEach((tag) => {
    tag.addEventListener("click", (e) => {
      addRipple(tag, e);
      $("#hero-input").value = tag.dataset.mood;
      setTimeout(() => heroSend.click(), 200);
    });
  });

  $("#btn-play-main").addEventListener("click", () => {
    state.playing = !state.playing;
    updatePlayerUI();
  });

  $("#btn-guitar").addEventListener("click", () => openScore("guitar"));
  $("#btn-ukulele").addEventListener("click", () => openScore("ukulele"));
  $("#btn-add-playlist").addEventListener("click", () => showToast("已加入歌单「今晚治愈」"));

  $("#btn-close-score").addEventListener("click", () => {
    $("#score-drawer").classList.remove("open");
  });

  $("#score-backdrop").addEventListener("click", () => {
    $("#score-drawer").classList.remove("open");
  });

  $$(".score-tab").forEach((tab) => {
    tab.addEventListener("click", () => openScore(tab.dataset.tab));
  });

  $("#back-playlists").addEventListener("click", () => switchPage("playlists"));

  $(".btn-create-playlist")?.addEventListener("click", () => showToast("新建歌单（原型演示）"));

  $("#btn-clear-data").addEventListener("click", () => {
    localStorage.removeItem("yinban_onboarded");
    showToast("数据已清除（原型演示）");
  });
}

document.addEventListener("DOMContentLoaded", init);
