const stageListEl = document.getElementById("stage-list");
const repoTitleEl = document.getElementById("repo-title");
const repoDescriptionEl = document.getElementById("repo-description");
const taskListEl = document.getElementById("task-list");
const overallProgressEl = document.getElementById("overall-progress-value");
const stageProgressEl = document.getElementById("stage-progress");
const repoProgressEl = document.getElementById("repo-progress");
const codingChecklistEl = document.getElementById("coding-checklist");
const linksListEl = document.getElementById("links-list");
const panelOverlayEl = document.getElementById("panel-overlay");
const panelButtons = document.querySelectorAll("[data-panel-trigger]");
let activePanel = null;

const CODING_CHECKLIST_KEY = "tasktracking:coding-checklist";
const CODING_CHECKLIST = [
  {
    title: "Math + ML",
    tasks: [
      "Implement linear regression from scratch",
      "Implement logistic regression from scratch",
      "Implement gradient descent",
      "Implement softmax + cross-entropy manually",
    ],
  },
  {
    title: "Deep Learning",
    tasks: [
      "Build a neural network from scratch",
      "Build a PyTorch network with custom training loop",
      "Implement dropout manually",
      "Implement layer normalization manually",
    ],
  },
  {
    title: "NLP",
    tasks: [
      "Implement BPE tokenization",
      "Train a word-level language model",
      "Train an LSTM language model",
    ],
  },
  {
    title: "Transformers",
    tasks: [
      "Implement attention",
      "Implement multi-head attention",
      "Implement positional encodings",
      "Implement a transformer encoder",
      "Implement a causal transformer",
      "Train on tiny dataset (Shakespeare)",
    ],
  },
  {
    title: "LLM Work",
    tasks: [
      "Fine-tune GPT-2 using LoRA",
      "Perform 8-bit quantization",
      "Implement RAG pipeline",
      "Build a simple agent",
      "Use MCP (model context protocol)",
    ],
  },
];

const state = {
  stages: [],
  selectedRepoId: null,
};

function loadCodingChecklistState() {
  try {
    const stored = localStorage.getItem(CODING_CHECKLIST_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch {
    return {};
  }
}

function persistCodingChecklistState(nextState) {
  localStorage.setItem(CODING_CHECKLIST_KEY, JSON.stringify(nextState));
}

function renderCodingChecklist() {
  const saved = loadCodingChecklistState();
  codingChecklistEl.innerHTML = "";

  CODING_CHECKLIST.forEach((group) => {
    const section = document.createElement("section");
    section.className = "coding-group";

    const heading = document.createElement("h4");
    heading.textContent = group.title;
    section.appendChild(heading);

    const list = document.createElement("ul");
    group.tasks.forEach((task) => {
      const item = document.createElement("li");
      const label = document.createElement("label");
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = Boolean(saved[task]);
      checkbox.addEventListener("change", () => {
        const next = loadCodingChecklistState();
        next[task] = checkbox.checked;
        persistCodingChecklistState(next);
      });
      label.appendChild(checkbox);
      label.append(task);
      item.appendChild(label);
      list.appendChild(item);
    });

    section.appendChild(list);
    codingChecklistEl.appendChild(section);
  });
}

function setupSlidePanels() {
  panelButtons.forEach((button) => {
    button.addEventListener("click", () => {
      togglePanel(button.dataset.panelTrigger);
    });
  });

  document.querySelectorAll(".close-panel").forEach((closeBtn) => {
    closeBtn.addEventListener("click", closeActivePanel);
  });

  panelOverlayEl?.addEventListener("click", closeActivePanel);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeActivePanel();
    }
  });
}

function togglePanel(panelId) {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  if (activePanel === panel) {
    closeActivePanel();
    return;
  }
  closeActivePanel();
  panel.classList.add("open");
  panelOverlayEl?.classList.add("visible");
  activePanel = panel;
}

function closeActivePanel() {
  if (activePanel) {
    activePanel.classList.remove("open");
    activePanel = null;
  }
  panelOverlayEl?.classList.remove("visible");
}

function renderStageList() {
  if (!state.stages.length) {
    stageListEl.innerHTML =
      '<li class="stage-item empty">Loading checklist…</li>';
    return;
  }

  stageListEl.innerHTML = "";
  state.stages.forEach((stage) => {
    const li = document.createElement("li");
    li.className = "stage-item";

    const heading = document.createElement("div");
    heading.className = "stage-heading";
    heading.innerHTML = `
      <div>
        <p class="stage-label">${stage.title}</p>
        <small>${stage.description}</small>
      </div>
      ${renderProgressBar(stage.progress.percent)}
    `;

    const repos = document.createElement("div");
    repos.className = "repo-list";
    let stageUnlocked = true;
    stage.repositories.forEach((repo) => {
      const repoComplete =
        repo.progress.total > 0 &&
        repo.progress.completed === repo.progress.total;
      const clickable = stageUnlocked;
      const entry = document.createElement("button");
      entry.type = "button";
      entry.className = `repo-entry${
        repo.id === state.selectedRepoId ? " active" : ""
      }${clickable ? "" : " disabled"}`;
      entry.disabled = !clickable;
      entry.innerHTML = `
        <span>${repo.title}</span>
        <small>${repo.progress.completed}/${repo.progress.total}</small>
      `;
      if (clickable) {
        entry.addEventListener("click", () => {
          state.selectedRepoId = repo.id;
          renderRepoDetails();
          renderStageSummary();
          renderRepoSummary();
          renderLinksList();
          renderStageList();
        });
      }
      repos.appendChild(entry);
      stageUnlocked = repoComplete;
    });

    li.appendChild(heading);
    li.appendChild(repos);
    stageListEl.appendChild(li);
  });
}

function getSelectedRepo() {
  if (!state.selectedRepoId) {
    return null;
  }
  for (const stage of state.stages) {
    const stageComplete =
      stage.progress.total > 0 &&
      stage.progress.completed === stage.progress.total;
    const repo = stage.repositories.find(
      (candidate) => candidate.id === state.selectedRepoId,
    );
    if (repo) {
      return repo;
    }
    if (!stageComplete) {
      break;
    }
  }
  return null;
}

function renderRepoDetails() {
  const repo = getSelectedRepo();
  if (!repo) {
    repoTitleEl.textContent = "Select a repository";
    repoDescriptionEl.textContent =
      "Choose a repository from the left panel to see its checklist.";
    taskListEl.innerHTML = "";
    return;
  }

  repoTitleEl.textContent = repo.title;
  repoDescriptionEl.textContent = repo.description ?? "";
  taskListEl.innerHTML = "";

  repo.tasks.forEach((task) => {
    const item = document.createElement("li");
    item.className = "task-item";
    item.dataset.taskId = task.id;
    item.innerHTML = `
      <div class="task-meta">
        <strong>${task.title}</strong>
        <p>${task.description ?? ""}</p>
        ${
          task.link
            ? `<a href="${task.link}" target="_blank" rel="noopener">View submitted link</a>`
            : ""
        }
      </div>
    `;

    const action = document.createElement("button");
    action.textContent = task.completed ? "Completed" : "Mark complete";
    action.disabled = task.completed || !task.enabled;
    const form = document.createElement("div");
    form.className = "link-form";
    form.innerHTML = `
      <input type="url" name="task-link" placeholder="Paste link to your work" />
      <div class="form-actions">
        <button type="button" class="submit-link">Submit</button>
        <button type="button" class="cancel-link">Cancel</button>
      </div>
    `;

    if (!task.completed && task.enabled) {
      action.addEventListener("click", () => {
        const expanded = item.classList.toggle("expanded");
        if (expanded) {
          form.querySelector("input")?.focus();
        }
      });
    }

    const submitBtn = form.querySelector(".submit-link");
    const cancelBtn = form.querySelector(".cancel-link");
    const input = form.querySelector("input");

    submitBtn?.addEventListener("click", async () => {
      if (!input) return;
      const linkValue = input.value.trim();
      if (!linkValue) {
        input.focus();
        return;
      }
      submitBtn.disabled = true;
      cancelBtn.disabled = true;
      try {
        await updateTaskCompletion(repo.id, task.id, true, linkValue);
      } finally {
        submitBtn.disabled = false;
        cancelBtn.disabled = false;
      }
    });

    cancelBtn?.addEventListener("click", () => {
      input.value = "";
      item.classList.remove("expanded");
    });

    item.appendChild(action);
    item.appendChild(form);
    taskListEl.appendChild(item);
  });
}

function renderStageSummary() {
  const repo = getSelectedRepo();
  if (!repo) {
    stageProgressEl.innerHTML = "<p>Select a repository to view its stage.</p>";
    return;
  }

  const stage = state.stages.find((s) => s.id === repo.stage_id);
  if (!stage) {
    stageProgressEl.innerHTML = "<p>Stage not found.</p>";
    return;
  }

  stageProgressEl.innerHTML = `
    <div class="progress-card">
      <p>${stage.title}</p>
      ${renderProgressBar(stage.progress.percent)}
      <small>${stage.progress.completed} / ${stage.progress.total} tasks complete</small>
    </div>
  `;
}

function renderRepoSummary() {
  const repo = getSelectedRepo();
  if (!repo) {
    repoProgressEl.innerHTML = "<p>Select a repository to view its metrics.</p>";
    return;
  }

  repoProgressEl.innerHTML = `
    <div class="progress-card">
      <p>${repo.title}</p>
      ${renderProgressBar(repo.progress.percent)}
      <small>${repo.progress.completed} / ${repo.progress.total} tasks complete</small>
    </div>
  `;
}

function renderLinksList() {
  if (!linksListEl) return;
  const stageMap = new Map();
  state.stages.forEach((stage) => {
    stage.repositories.forEach((repo) => {
      repo.tasks.forEach((task) => {
        if (task.link) {
          const bucket = stageMap.get(stage.title) ?? [];
          bucket.push({
            repo: repo.title,
            task: task.title,
            link: task.link,
          });
          stageMap.set(stage.title, bucket);
        }
      });
    });
  });

  if (!stageMap.size) {
    linksListEl.innerHTML = "<p>No links submitted yet.</p>";
    return;
  }

  linksListEl.innerHTML = "";
  stageMap.forEach((entries, stageTitle) => {
    const section = document.createElement("section");
    section.className = "links-stage";
    const stageHeading = document.createElement("h4");
    stageHeading.textContent = stageTitle;
    section.appendChild(stageHeading);

    entries.forEach((entry) => {
      const container = document.createElement("article");
      container.className = "link-entry";
      container.innerHTML = `
        <div class="link-entry-header">
          <p class="link-task">${entry.task}</p>
          <small>${entry.repo}</small>
        </div>
        <a href="${entry.link}" target="_blank" rel="noopener">${entry.link}</a>
      `;
      section.appendChild(container);
    });

    linksListEl.appendChild(section);
  });
}

function renderProgressBar(percent = 0) {
  const clamped = Math.min(100, Math.max(0, Number(percent) || 0));
  return `
    <div class="progress-bar">
      <div class="progress-bar-fill" style="width:${clamped}%"></div>
      <span class="progress-value">${clamped.toFixed(1)}%</span>
    </div>
  `;
}

async function loadHierarchy() {
  stageListEl.innerHTML =
    '<li class="stage-item empty">Loading checklist…</li>';

  try {
    const response = await fetch("/api/v1/progress");
    if (!response.ok) {
      throw new Error("Failed to load data");
    }

    const data = await response.json();
    state.stages = data.stages;
    overallProgressEl.textContent = `${data.overall_progress.toFixed?.(1) ?? data.overall_progress}%`;

    if (!state.selectedRepoId && state.stages[0]?.repositories[0]) {
      state.selectedRepoId = state.stages[0].repositories[0].id;
    } else if (state.selectedRepoId) {
      const repo = getSelectedRepo();
      if (!repo && state.stages[0]?.repositories[0]) {
        state.selectedRepoId = state.stages[0].repositories[0].id;
      }
    }

    renderStageList();
    renderRepoDetails();
    renderStageSummary();
    renderRepoSummary();
    renderLinksList();
  } catch (error) {
    console.error(error);
    stageListEl.innerHTML =
      '<li class="stage-item empty">Unable to load data.</li>';
  }
}

async function updateTaskCompletion(repoId, taskId, completed, link) {
  try {
    const response = await fetch(`/api/v1/progress/${repoId}/${taskId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ completed, link }),
    });

    if (!response.ok) {
      throw new Error("Update failed");
    }

    await loadHierarchy();
  } catch (error) {
    console.error(error);
    alert("Could not update task. Ensure prerequisites are met.");
  }
}

function init() {
  setupSlidePanels();
  renderCodingChecklist();
  loadHierarchy();
}

document.addEventListener("DOMContentLoaded", init);

