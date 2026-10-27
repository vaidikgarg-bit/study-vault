// StudyVault Client Application Logic

let allCourses = [];
let allNotes = [];
let favoritesOnly = false;
let currentQuiz = null;
let currentQuestions = [];
let userAnswers = {};
let quizStartTime = null;

let currentFlashcards = [];
let currentCardIndex = 0;

let currentNoteMode = 'manual';
let selectedPdfFile = null;

function setNoteMode(mode) {
  currentNoteMode = mode;
  const manualTab = document.getElementById("tab-manual");
  const pdfTab = document.getElementById("tab-pdf");
  const manualSec = document.getElementById("manual-content-section");
  const pdfSec = document.getElementById("pdf-dropzone-section");
  const contentInput = document.getElementById("note_content");

  if (mode === 'manual') {
    manualTab.className = "flex-1 py-1.5 rounded-lg text-xs font-bold bg-indigo-600 text-white transition";
    pdfTab.className = "flex-1 py-1.5 rounded-lg text-xs font-bold text-slate-400 hover:text-white transition";
    manualSec.classList.remove("hidden");
    pdfSec.classList.add("hidden");
    contentInput.required = true;
  } else {
    pdfTab.className = "flex-1 py-1.5 rounded-lg text-xs font-bold bg-indigo-600 text-white transition";
    manualTab.className = "flex-1 py-1.5 rounded-lg text-xs font-bold text-slate-400 hover:text-white transition";
    pdfSec.classList.remove("hidden");
    manualSec.classList.add("hidden");
    contentInput.required = false;
  }
}

function handleDragOver(e) {
  e.preventDefault();
  document.getElementById("pdf-dropzone").classList.add("border-indigo-400", "bg-indigo-950/20");
}

function handleDragLeave(e) {
  e.preventDefault();
  document.getElementById("pdf-dropzone").classList.remove("border-indigo-400", "bg-indigo-950/20");
}

function handleFileDrop(e) {
  e.preventDefault();
  handleDragLeave(e);
  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
    processSelectedFile(e.dataTransfer.files[0]);
  }
}

function handleFileSelected(e) {
  if (e.target.files && e.target.files[0]) {
    processSelectedFile(e.target.files[0]);
  }
}

function processSelectedFile(file) {
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    alert("Please select a valid .pdf file.");
    return;
  }
  selectedPdfFile = file;
  document.getElementById("pdf-filename-display").innerHTML = `<i class="fa-solid fa-file-pdf text-rose-400 mr-2"></i> ${file.name} (${Math.round(file.size / 1024)} KB)`;
  // Auto-fill title if empty
  const titleInput = document.getElementById("note_title_input");
  if (!titleInput.value) {
    titleInput.value = file.name.replace(/\.pdf$/i, '').replace(/[-_]/g, ' ');
  }
}

function triggerMathRender() {
  setTimeout(() => {
    if (window.renderMathInElement) {
      try {
        renderMathInElement(document.body, {
          delimiters: [
            { left: "$$", right: "$$", display: true },
            { left: "$", right: "$", display: false },
            { left: "\\(", right: "\\)", display: false },
            { left: "\\[", right: "\\]", display: true }
          ],
          throwOnError: false
        });
      } catch (e) {
        console.warn("KaTeX render error:", e);
      }
    }
    if (window.Prism) {
      Prism.highlightAll();
    }
  }, 50);
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  loadCourses();
  loadNotes();
  loadAnalytics();
});

// View Switching
function showView(viewId) {
  const views = ["dashboard", "quiz", "flashcards", "analytics"];
  views.forEach(v => {
    const el = document.getElementById(`view-${v}`);
    if (el) el.classList.add("hidden");
  });

  const target = document.getElementById(`view-${viewId}`);
  if (target) target.classList.remove("hidden");

  // Update nav buttons
  document.querySelectorAll(".nav-btn").forEach(btn => {
    btn.classList.remove("text-indigo-400", "bg-slate-700/60");
    btn.classList.add("text-slate-400");
  });
  const activeBtn = document.getElementById(`nav-${viewId}`);
  if (activeBtn) {
    activeBtn.classList.add("text-indigo-400", "bg-slate-700/60");
    activeBtn.classList.remove("text-slate-400");
  }

  if (viewId === "analytics") {
    loadAnalytics();
  }
}

// Modal Helpers
function openModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove("hidden");
}

function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add("hidden");
}

// Load Courses
async function loadCourses() {
  try {
    const res = await fetch("/api/courses");
    allCourses = await res.json();

    document.getElementById("course-count-badge").innerText = allCourses.length;

    // Render Sidebar List
    const courseListEl = document.getElementById("course-list");
    courseListEl.innerHTML = allCourses.map(c => `
      <div onclick="filterByCourseId(${c.id})" class="cursor-pointer group flex items-center justify-between p-2.5 rounded-xl hover:bg-slate-700/50 transition">
        <div class="flex items-center gap-2.5">
          <span class="w-2.5 h-2.5 rounded-full bg-indigo-400"></span>
          <span class="text-sm font-semibold text-slate-200 group-hover:text-white">${c.code}</span>
        </div>
        <span class="text-xs px-2 py-0.5 rounded-md bg-slate-700 text-slate-400 font-bold">${c.note_count}</span>
      </div>
    `).join("");

    // Populate Selects
    const filterSelect = document.getElementById("course-filter-select");
    filterSelect.innerHTML = `<option value="all">All Courses (${allCourses.length})</option>` +
      allCourses.map(c => `<option value="${c.id}">${c.code} - ${c.title}</option>`).join("");

    const noteCourseSelect = document.getElementById("note_course_id");
    noteCourseSelect.innerHTML = allCourses.map(c => `<option value="${c.id}">${c.code} - ${c.title}</option>`).join("");

    if (allCourses.length > 0) {
      loadMilestones(allCourses[0].id);
    }
  } catch (err) {
    console.error("Failed to load courses:", err);
  }
}

async function loadMilestones(courseId) {
  const container = document.getElementById("course-milestones-list");
  if (!container) return;
  if (!courseId) {
    container.innerHTML = `<div class="text-slate-500 italic">No course selected</div>`;
    return;
  }
  try {
    const res = await fetch(`/api/courses/${courseId}/milestones`);
    if (!res.ok) return;
    const milestones = await res.json();
    if (milestones.length === 0) {
      container.innerHTML = `<div class="text-slate-500 italic">No pending milestones</div>`;
      return;
    }
    container.innerHTML = milestones.map(m => `
      <div class="flex items-center justify-between p-1.5 rounded-lg bg-slate-900/60 border border-slate-700/40">
        <span class="${m.is_completed ? 'line-through text-slate-500' : 'text-slate-200'} font-medium truncate max-w-[120px]">${m.title}</span>
        <span class="text-[10px] text-slate-400 font-mono">${m.target_date || ''}</span>
      </div>
    `).join("");
  } catch (e) {
    container.innerHTML = `<div class="text-slate-500 italic">Milestones unavailable</div>`;
  }
}

// Load Notes
async function loadNotes() {
  try {
    const res = await fetch("/api/notes");
    allNotes = await res.json();
    renderNotes(allNotes);
  } catch (err) {
    console.error("Failed to load notes:", err);
  }
}

function filterByCourseId(id) {
  document.getElementById("course-filter-select").value = id;
  filterNotes();
  showView("dashboard");
}

function toggleFavoriteFilter() {
  favoritesOnly = !favoritesOnly;
  const btn = document.getElementById("btn-filter-favs");
  const star = document.getElementById("star-filter-icon");
  if (favoritesOnly) {
    btn.classList.add("border-amber-500", "bg-amber-950/40", "text-amber-300");
    star.className = "fa-solid fa-star text-amber-400";
  } else {
    btn.classList.remove("border-amber-500", "bg-amber-950/40", "text-amber-300");
    star.className = "fa-solid fa-star text-slate-500";
  }
  filterNotes();
}

async function toggleFavoriteNote(noteId) {
  try {
    const res = await fetch(`/api/notes/${noteId}/favorite`, { method: "POST" });
    const data = await res.json();
    const note = allNotes.find(n => n.id === noteId);
    if (note) {
      note.is_favorite = data.is_favorite;
    }
    filterNotes();
  } catch (err) {
    console.error("Failed to toggle favorite:", err);
  }
}

function filterNotes() {
  const query = document.getElementById("note-search").value.toLowerCase().trim();
  const courseFilter = document.getElementById("course-filter-select").value;

  const filtered = allNotes.filter(n => {
    const matchesCourse = courseFilter === "all" || n.course_id == courseFilter;
    const matchesFav = !favoritesOnly || Boolean(n.is_favorite);
    const matchesQuery = n.title.toLowerCase().includes(query) ||
                         n.topic.toLowerCase().includes(query) ||
                         n.content.toLowerCase().includes(query) ||
                         n.course_code.toLowerCase().includes(query);
    return matchesCourse && matchesFav && matchesQuery;
  });

  renderNotes(filtered);
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

const debouncedFilterNotes = debounce(filterNotes, 200);

function renderNotes(notes) {
  const grid = document.getElementById("notes-grid");
  if (notes.length === 0) {
    grid.innerHTML = `
      <div class="col-span-full py-16 text-center text-slate-500 space-y-3">
        <i class="fa-solid fa-folder-open text-4xl"></i>
        <p class="text-sm">No notes found. Upload a new note to get started!</p>
      </div>
    `;
    return;
  }

  grid.innerHTML = notes.map(n => `
    <div class="bg-slate-800/70 border border-slate-700/70 rounded-2xl p-5 hover:border-slate-600 transition flex flex-col justify-between space-y-4">
      <div>
        <div class="flex items-center justify-between gap-2 mb-2">
          <span class="text-xs font-bold px-2.5 py-1 rounded-md bg-indigo-500/20 text-indigo-300">${n.course_code}</span>
          <div class="flex items-center gap-2">
            <span class="text-xs text-slate-400 font-medium">${n.topic}</span>
            <button onclick="toggleFavoriteNote(${n.id})" class="text-sm p-1 transition ${n.is_favorite ? 'text-amber-400 hover:text-amber-300' : 'text-slate-500 hover:text-amber-400'}" title="${n.is_favorite ? 'Unstar note' : 'Star note'}">
              <i class="fa-solid fa-star"></i>
            </button>
          </div>
        </div>
        <h4 class="text-base font-bold text-slate-100 leading-snug">${n.title}</h4>
        <div class="flex items-center gap-3 mt-1.5 text-[11px] text-slate-400 font-medium">
          <span><i class="fa-regular fa-clock text-indigo-400 mr-1"></i>${n.reading_time_mins || 1} min read</span>
          <span>•</span>
          <span>${n.word_count || (n.content.split(' ').length)} words</span>
        </div>
        <p class="text-xs text-slate-400 mt-2 line-clamp-3 leading-relaxed">${n.content}</p>
      </div>

      <div class="pt-4 border-t border-slate-700/60 flex items-center justify-between gap-2">
        <div class="flex items-center gap-2">
          <button onclick="startQuiz(${n.id})" class="px-3 py-1.5 rounded-lg bg-indigo-600/90 hover:bg-indigo-600 text-white text-xs font-semibold flex items-center gap-1.5 transition">
            <i class="fa-solid fa-bolt-lightning text-yellow-300"></i> AI Quiz
          </button>
          <button onclick="startFlashcards(${n.id})" class="px-3 py-1.5 rounded-lg bg-purple-600/90 hover:bg-purple-600 text-white text-xs font-semibold flex items-center gap-1.5 transition">
            <i class="fa-solid fa-clone"></i> Flashcards
          </button>
        </div>
        <div class="flex items-center gap-1">
          <button onclick="duplicateNote(${n.id})" class="text-slate-400 hover:text-sky-300 p-1.5 text-xs transition" title="Duplicate Note">
            <i class="fa-solid fa-copy"></i>
          </button>
          <a href="/api/notes/${n.id}/export/markdown" download class="text-slate-400 hover:text-indigo-300 p-1.5 text-xs transition" title="Export as Markdown (.md)">
            <i class="fa-solid fa-file-arrow-down"></i>
          </a>
          <a href="/api/notes/${n.id}/export/json" download class="text-slate-400 hover:text-emerald-300 p-1.5 text-xs transition" title="Export as JSON">
            <i class="fa-solid fa-code"></i>
          </a>
          <a href="/api/notes/${n.id}/export/anki" download class="text-slate-400 hover:text-amber-300 p-1.5 text-xs transition" title="Export to Anki (.tsv)">
            <i class="fa-solid fa-file-export"></i>
          </a>
          <button onclick="deleteNote(${n.id})" class="text-slate-500 hover:text-red-400 p-1.5 text-xs transition" title="Delete Note">
            <i class="fa-solid fa-trash"></i>
          </button>
        </div>
      </div>
    </div>
  `).join("");
  triggerMathRender();
}

async function duplicateNote(noteId) {
  try {
    const res = await fetch(`/api/notes/${noteId}/duplicate`, { method: "POST" });
    if (!res.ok) throw new Error("Duplication failed");
    await loadNotes();
    await loadCourses();
  } catch (err) {
    alert("Could not duplicate note: " + err.message);
  }
}

// Form Handlers
async function handleCreateCourse(e) {
  e.preventDefault();
  const code = document.getElementById("course_code").value;
  const title = document.getElementById("course_title").value;
  const department = document.getElementById("course_dept").value;

  try {
    const res = await fetch("/api/courses", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: jsonPayload = JSON.stringify({ code, title, department })
    });
    if (!res.ok) throw new Error("Failed to create course");
    closeModal("courseModal");
    document.getElementById("courseForm").reset();
    await loadCourses();
    await loadAnalytics();
  } catch (err) {
    alert("Error creating course: " + err.message);
  }
}

async function handleCreateNote(e) {
  e.preventDefault();
  const course_id = parseInt(document.getElementById("note_course_id").value);
  const title = document.getElementById("note_title_input").value;
  const topic = document.getElementById("note_topic").value;
  const saveBtn = document.getElementById("save-note-btn");

  saveBtn.disabled = true;
  saveBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-2"></i> Processing...`;

  try {
    if (currentNoteMode === 'pdf') {
      if (!selectedPdfFile) {
        alert("Please select or drop a PDF file first.");
        saveBtn.disabled = false;
        saveBtn.innerText = "Save Note";
        return;
      }
      const formData = new FormData();
      formData.append("course_id", course_id);
      formData.append("title", title);
      formData.append("topic", topic);
      formData.append("file", selectedPdfFile);

      const res = await fetch("/api/notes/upload-pdf", {
        method: "POST",
        body: formData
      });
      if (!res.ok) throw new Error("Failed to upload and parse PDF");
    } else {
      const content = document.getElementById("note_content").value;
      const res = await fetch("/api/notes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ course_id, title, topic, content })
      });
      if (!res.ok) throw new Error("Failed to create note");
    }

    closeModal("noteModal");
    document.getElementById("noteForm").reset();
    selectedPdfFile = null;
    document.getElementById("pdf-filename-display").innerHTML = `Drag & drop your PDF slide deck here, or <span class="text-indigo-400 underline">browse</span>`;
    setNoteMode('manual');
    await loadNotes();
    await loadCourses();
    await loadAnalytics();
  } catch (err) {
    alert("Error saving note: " + err.message);
  } finally {
    saveBtn.disabled = false;
    saveBtn.innerText = "Save Note";
  }
}

async function deleteNote(id) {
  if (!confirm("Are you sure you want to delete this study note?")) return;
  try {
    await fetch(`/api/notes/${id}`, { method: "DELETE" });
    await loadNotes();
    await loadCourses();
    await loadAnalytics();
  } catch (err) {
    alert("Failed to delete note: " + err.message);
  }
}

// ---------------------------------------------------------------------------
// Quiz Logic
// ---------------------------------------------------------------------------

async function startQuiz(noteId) {
  showView("quiz");
  document.getElementById("quiz-title").innerText = "Generating AI Quiz Questions...";
  document.getElementById("quiz-container").innerHTML = `
    <div class="py-16 text-center text-indigo-400 space-y-3">
      <i class="fa-solid fa-spinner fa-spin text-3xl"></i>
      <p class="text-sm font-semibold">Analyzing study notes and synthesizing conceptual questions...</p>
    </div>
  `;
  document.getElementById("quiz-result-card").classList.add("hidden");

  try {
    const res = await fetch(`/api/notes/${noteId}/quiz`, { method: "POST" });
    currentQuiz = await res.json();
    currentQuestions = currentQuiz.questions;
    userAnswers = {};
    quizStartTime = Date.now();

    document.getElementById("quiz-title").innerText = currentQuiz.note_title;
    renderQuizQuestions();
  } catch (err) {
    document.getElementById("quiz-container").innerHTML = `<div class="text-red-400 p-4 text-center">Failed to load quiz: ${err.message}</div>`;
  }
}

function renderQuizQuestions() {
  updateQuizProgress();
  const container = document.getElementById("quiz-container");
  container.innerHTML = currentQuestions.map((q, qIdx) => `
    <div class="bg-slate-900/60 rounded-xl p-5 border border-slate-700/60 space-y-4">
      <div class="flex items-start gap-3">
        <span class="w-6 h-6 rounded-md bg-indigo-500/20 text-indigo-300 text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">${qIdx + 1}</span>
        <h4 class="text-base font-semibold text-slate-100">${q.question}</h4>
      </div>

      <div class="space-y-2 pt-1">
        ${q.options.map((opt, optIdx) => `
          <button onclick="selectQuizAnswer(${qIdx}, ${optIdx})" id="q-${qIdx}-opt-${optIdx}" class="quiz-opt-btn w-full text-left p-3 rounded-lg border border-slate-700 bg-slate-800/80 hover:bg-slate-700/80 text-sm text-slate-200 transition flex items-center justify-between">
            <span>${opt}</span>
            <span class="opt-indicator opacity-0 text-xs font-bold px-2 py-0.5 rounded"></span>
          </button>
        `).join("")}
      </div>

      <div id="explanation-${qIdx}" class="hidden p-3 rounded-lg bg-indigo-950/40 border border-indigo-800/40 text-xs text-indigo-200 mt-2">
        <strong>Explanation:</strong> ${q.explanation}
      </div>
    </div>
  `).join("") + `
    <div class="pt-4 flex justify-end">
      <button onclick="submitQuiz()" class="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 transition">
        Submit Quiz Results
      </button>
    </div>
  `;
  triggerMathRender();
}

function updateQuizProgress() {
  const answered = Object.keys(userAnswers).length;
  const total = currentQuestions.length;
  const pct = total > 0 ? Math.round((answered / total) * 100) : 0;
  const pText = document.getElementById("quiz-progress-text");
  const pBar = document.getElementById("quiz-progress-bar");
  if (pText) pText.innerText = `${answered} / ${total} Answered (${pct}%)`;
  if (pBar) pBar.style.width = `${pct}%`;
}

function selectQuizAnswer(qIdx, optIdx) {
  userAnswers[qIdx] = optIdx;
  updateQuizProgress();
  const q = currentQuestions[qIdx];

  // Disable buttons for this question & highlight choices
  q.options.forEach((_, idx) => {
    const btn = document.getElementById(`q-${qIdx}-opt-${idx}`);
    btn.disabled = true;
    btn.classList.remove("hover:bg-slate-700/80");

    if (idx === q.correct_index) {
      btn.classList.add("bg-emerald-950/60", "border-emerald-500/80", "text-emerald-200");
      const ind = btn.querySelector(".opt-indicator");
      ind.innerText = "Correct";
      ind.classList.add("bg-emerald-500/20", "text-emerald-300", "opacity-100");
    } else if (idx === optIdx && optIdx !== q.correct_index) {
      btn.classList.add("bg-red-950/60", "border-red-500/80", "text-red-200");
      const ind = btn.querySelector(".opt-indicator");
      ind.innerText = "Incorrect";
      ind.classList.add("bg-red-500/20", "text-red-300", "opacity-100");
    }
  });

  const exp = document.getElementById(`explanation-${qIdx}`);
  if (exp) exp.classList.remove("hidden");
}

async function submitQuiz() {
  let score = 0;
  currentQuestions.forEach((q, idx) => {
    if (userAnswers[idx] === q.correct_index) {
      score++;
    }
  });

  const total = currentQuestions.length;
  const elapsedSecs = Math.max(1, Math.round((Date.now() - quizStartTime) / 1000));
  const pct = Math.round((score / total) * 100);

  // Submit attempt to backend
  try {
    await fetch("/api/quiz-attempts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        note_id: currentQuiz.note_id,
        score: score,
        total_questions: total,
        time_taken_seconds: elapsedSecs
      })
    });
  } catch (err) {
    console.error("Failed to record attempt:", err);
  }

  // Display result card
  document.getElementById("quiz-score-text").innerText = `Score: ${score} / ${total} (${pct}%)`;
  document.getElementById("quiz-time-text").innerText = `Completed in ${elapsedSecs} seconds`;
  document.getElementById("quiz-result-card").classList.remove("hidden");
  window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
}

// ---------------------------------------------------------------------------
// 3D Flashcards Logic
// ---------------------------------------------------------------------------

async function startFlashcards(noteId) {
  showView("flashcards");
  document.getElementById("flashcard-title").innerText = "Loading Flashcards...";
  currentFlashcards = [];
  currentCardIndex = 0;

  try {
    const res = await fetch(`/api/notes/${noteId}/flashcards`, { method: "POST" });
    const data = await res.json();
    currentFlashcards = data.flashcards;
    document.getElementById("flashcard-title").innerText = data.note_title;
    showCard(0);
  } catch (err) {
    alert("Failed to load flashcards: " + err.message);
  }
}

function showCard(index) {
  if (currentFlashcards.length === 0) return;
  currentCardIndex = index;

  // Unflip card
  document.getElementById("card-inner").classList.remove("is-flipped");

  const card = currentFlashcards[currentCardIndex];
  document.getElementById("card-front-text").innerText = card.front;
  document.getElementById("card-back-text").innerText = card.back;
  document.getElementById("card-counter").innerText = `${currentCardIndex + 1} / ${currentFlashcards.length}`;

  const boxElem = document.getElementById("leitner-box-indicator");
  if (boxElem) {
    const boxNum = card.leitner_box || 1;
    boxElem.innerText = `Leitner Box ${boxNum}`;
  }

  triggerMathRender();
}

function flipCard() {
  document.getElementById("card-inner").classList.toggle("is-flipped");
}

function nextCard() {
  if (currentFlashcards.length === 0) return;
  const nextIdx = (currentCardIndex + 1) % currentFlashcards.length;
  showCard(nextIdx);
}

function prevCard() {
  if (currentFlashcards.length === 0) return;
  const prevIdx = (currentCardIndex - 1 + currentFlashcards.length) % currentFlashcards.length;
  showCard(prevIdx);
}

async function rateCard(rating) {
  try {
    const res = await fetch(`/api/flashcards/review?rating=${rating}`, { method: "POST" });
    const data = await res.json();
    const ratingLabels = { 1: "Again (1d)", 2: "Hard (3d)", 3: "Good (6d)", 4: "Easy (boost)" };
    const label = ratingLabels[rating] || "Rated";

    // Show brief toast
    const counter = document.getElementById("card-counter");
    const origText = counter.innerText;
    counter.innerText = `Saved: ${label}`;
    counter.classList.add("text-emerald-400");
    setTimeout(() => {
      counter.classList.remove("text-emerald-400");
      nextCard();
    }, 400);
  } catch (e) {
    nextCard();
  }
}

// Global Keyboard Navigation
document.addEventListener("keydown", (e) => {
  // Only trigger if not typing inside an input or textarea
  if (["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)) return;

  const flashcardSec = document.getElementById("view-flashcards");
  if (flashcardSec && !flashcardSec.classList.contains("hidden")) {
    if (e.code === "Space" || e.key === "Enter") {
      e.preventDefault();
      flipCard();
    } else if (e.key === "ArrowRight" || e.key === "l") {
      e.preventDefault();
      nextCard();
    } else if (e.key === "ArrowLeft" || e.key === "h") {
      e.preventDefault();
      prevCard();
    } else if (["1", "2", "3", "4"].includes(e.key)) {
      e.preventDefault();
      rateCard(parseInt(e.key, 10));
    }
  }
});

// ---------------------------------------------------------------------------
// Analytics
// ---------------------------------------------------------------------------

async function loadAnalytics() {
  try {
    const res = await fetch("/api/analytics");
    const data = await res.json();

    document.getElementById("stat-courses").innerText = data.total_courses;
    document.getElementById("stat-notes").innerText = data.total_notes;
    document.getElementById("stat-quizzes").innerText = data.quizzes_taken;
    document.getElementById("stat-avg").innerText = `${data.average_score_percent}%`;

    // Load badges
    const bRes = await fetch("/api/analytics/badges");
    if (bRes.ok) {
      const bData = await bRes.json();
      const badgeCountEl = document.getElementById("badge-unlocked-count");
      if (badgeCountEl) {
        badgeCountEl.innerText = `${bData.unlocked_count} / ${bData.total_badges} Unlocked`;
      }
      const bContainer = document.getElementById("badges-container");
      if (bContainer) {
        bContainer.innerHTML = bData.badges.map(b => `
          <div class="p-3.5 rounded-xl border ${b.unlocked ? 'border-amber-500/40 bg-amber-500/10' : 'border-slate-700/60 bg-slate-900/40 opacity-50'} flex items-start gap-3 transition">
            <div class="w-9 h-9 rounded-lg ${b.unlocked ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/30' : 'bg-slate-800 text-slate-500'} flex items-center justify-center text-sm font-bold shrink-0">
              <i class="fa-solid ${b.icon}"></i>
            </div>
            <div class="space-y-0.5 min-w-0">
              <div class="flex items-center gap-1.5">
                <h4 class="text-xs font-bold ${b.unlocked ? 'text-amber-300' : 'text-slate-400'} truncate">${b.title}</h4>
                ${b.unlocked ? '<i class="fa-solid fa-circle-check text-amber-400 text-[10px]"></i>' : ''}
              </div>
              <p class="text-[11px] text-slate-400 leading-snug line-clamp-2">${b.description}</p>
            </div>
          </div>
        `).join("");
      }
    }
  } catch (err) {
    console.error("Failed to load analytics:", err);
  }
}
