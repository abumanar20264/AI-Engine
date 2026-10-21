"use strict";

const form = document.querySelector("#project-form");
const list = document.querySelector("#project-list");
const listStatus = document.querySelector("#project-list-status");
const message = document.querySelector("#global-message");
const saveState = document.querySelector("#save-state");
const editorTitle = document.querySelector("#editor-title");
const objectContainer = document.querySelector("#objects");
const taskList = document.querySelector("#task-list");
const taskListStatus = document.querySelector("#task-list-status");
const startTaskButton = document.querySelector("#start-task");
let currentProject = null;
let projectSaved = false;
let taskPollTimer = null;

function showMessage(text, kind) {
  message.textContent = text;
  message.className = `message visible ${kind}`;
}

function clearMessage() {
  message.textContent = "";
  message.className = "message";
}

function setSaveState(text, kind = "") {
  saveState.textContent = text;
  saveState.className = `state-badge ${kind}`.trim();
}

function clearFieldErrors() {
  document.querySelectorAll(".field-error").forEach((element) => {
    element.textContent = "";
  });
  document.querySelectorAll("[aria-invalid='true']").forEach((element) => {
    element.removeAttribute("aria-invalid");
  });
}

function showFieldError(field, text) {
  const group = [...document.querySelectorAll("[data-field]")]
    .find((element) => element.dataset.field === field);
  if (!group) {
    showMessage(text, "error");
    return;
  }
  const error = group.querySelector(".field-error");
  if (error) error.textContent = text;
  const input = group.querySelector("input, select");
  if (input) input.setAttribute("aria-invalid", "true");
  group.scrollIntoView({ behavior: "smooth", block: "center" });
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  let payload;
  try {
    payload = await response.json();
  } catch {
    throw new Error(`The local server returned an unreadable response (${response.status}).`);
  }
  if (!response.ok) {
    const error = new Error(payload.error || `Request failed (${response.status}).`);
    error.field = payload.field;
    error.status = response.status;
    throw error;
  }
  return payload;
}

function showRequestError(error) {
  setSaveState("Action failed", "error");
  showMessage(error.message, "error");
  if (error.field) showFieldError(error.field, error.message);
}

function vectorMarkup(field, values) {
  return `<div class="vector-inputs" data-vector="${field}">${
    values.map((value, index) =>
      `<input type="number" step="any" value="${escapeAttribute(value)}" aria-label="${field} ${"XYZ"[index]}">`
    ).join("")
  }</div>`;
}

function escapeAttribute(value) {
  return String(value).replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function addFieldError(field) {
  return `<small class="field-error" data-field="${field}"></small>`;
}

function renderObjects(objects) {
  objectContainer.replaceChildren();
  objects.forEach((object, index) => {
    const card = document.createElement("article");
    card.className = "object-card";
    card.dataset.objectIndex = String(index);
    card.innerHTML = `
      <div class="object-heading">
        <h4>Object ${index + 1}</h4>
        <button class="button button-danger remove-object" type="button" aria-label="Remove object ${index + 1}">Remove</button>
      </div>
      <div class="object-grid">
        <label class="field" data-field="scenario.objects[${index}].id">
          <span>Object ID</span><input data-object-key="id" type="text" maxlength="64" value="${escapeAttribute(object.id)}">
          ${addFieldError(`scenario.objects[${index}].id`)}
        </label>
        <label class="field" data-field="scenario.objects[${index}].shape">
          <span>Shape</span>
          <select data-object-key="shape">
            ${["sphere", "box", "cylinder"].map((shape) =>
              `<option value="${shape}" ${shape === object.shape ? "selected" : ""}>${shape}</option>`
            ).join("")}
          </select>
          ${addFieldError(`scenario.objects[${index}].shape`)}
        </label>
        <label class="field span-two" data-field="scenario.objects[${index}].position">
          <span>Position (X, Y, Z)</span>${vectorMarkup(`object-${index}-position`, object.position)}
          ${addFieldError(`scenario.objects[${index}].position`)}
        </label>
        <label class="field span-two" data-field="scenario.objects[${index}].dimensions">
          <span>Dimensions (X, Y, Z)</span>${vectorMarkup(`object-${index}-dimensions`, object.dimensions)}
          ${addFieldError(`scenario.objects[${index}].dimensions`)}
        </label>
        <label class="field" data-field="scenario.objects[${index}].mass_kg">
          <span>Mass (kg)</span><input data-object-key="mass_kg" type="number" min="0.001" max="100000" step="any" value="${escapeAttribute(object.mass_kg)}">
          ${addFieldError(`scenario.objects[${index}].mass_kg`)}
        </label>
        <label class="field" data-field="scenario.objects[${index}].friction">
          <span>Friction (0–1)</span><input data-object-key="friction" type="number" min="0" max="1" step="any" value="${escapeAttribute(object.friction)}">
          ${addFieldError(`scenario.objects[${index}].friction`)}
        </label>
        <label class="field" data-field="scenario.objects[${index}].restitution">
          <span>Restitution (0–1)</span><input data-object-key="restitution" type="number" min="0" max="1" step="any" value="${escapeAttribute(object.restitution)}">
          ${addFieldError(`scenario.objects[${index}].restitution`)}
        </label>
      </div>`;
    objectContainer.append(card);
  });
  clearFieldErrors();
  updateObjectButtons();
}

function updateObjectButtons() {
  const cards = [...objectContainer.querySelectorAll(".object-card")];
  objectContainer.querySelectorAll(".remove-object").forEach((button) => {
    button.disabled = cards.length <= 2;
  });
  document.querySelector("#add-object").disabled = cards.length >= 64;
}

function readNumber(element) {
  return element.value.trim() === "" ? Number.NaN : Number(element.value);
}

function readVector(field) {
  return [...document.querySelector(`[data-vector="${field}"]`).querySelectorAll("input")]
    .map(readNumber);
}

function collectProject() {
  const project = structuredClone(currentProject);
  project.name = document.querySelector("#project-name").value;
  project.scenario.type = document.querySelector("#scenario-type").value;
  project.scenario.gravity_m_s2 = readVector("scenario.gravity_m_s2");
  project.scenario.camera.position = readVector("scenario.camera.position");
  project.scenario.camera.target = readVector("scenario.camera.target");
  project.scenario.camera.lens_mm = readNumber(document.querySelector("#camera-lens"));
  project.scenario.video = {
    width: readNumber(document.querySelector("#video-width")),
    height: readNumber(document.querySelector("#video-height")),
    fps: readNumber(document.querySelector("#video-fps")),
    frame_count: readNumber(document.querySelector("#video-frames")),
    eevee_samples: Number(document.querySelector("#video-samples").value),
  };
  project.scenario.objects = [...objectContainer.querySelectorAll(".object-card")]
    .map((card, index) => ({
      id: card.querySelector("[data-object-key='id']").value,
      shape: card.querySelector("[data-object-key='shape']").value,
      position: readVector(`object-${index}-position`),
      dimensions: readVector(`object-${index}-dimensions`),
      mass_kg: readNumber(card.querySelector("[data-object-key='mass_kg']")),
      friction: readNumber(card.querySelector("[data-object-key='friction']")),
      restitution: readNumber(card.querySelector("[data-object-key='restitution']")),
    }));
  project.audio.enabled = document.querySelector("#audio-enabled").checked;
  project.audio.source = document.querySelector("#audio-source").value.trim() || null;
  project.audio.volume = readNumber(document.querySelector("#audio-volume"));
  return project;
}

function populateProject(project, saved = false) {
  currentProject = structuredClone(project);
  projectSaved = saved;
  document.querySelector("#project-name").value = project.name;
  document.querySelector("#scenario-type").value = project.scenario.type;
  document.querySelector("#camera-lens").value = project.scenario.camera.lens_mm;
  document.querySelector("#video-width").value = project.scenario.video.width;
  document.querySelector("#video-height").value = project.scenario.video.height;
  document.querySelector("#video-fps").value = project.scenario.video.fps;
  document.querySelector("#video-frames").value = project.scenario.video.frame_count;
  document.querySelector("#video-samples").value = project.scenario.video.eevee_samples;
  document.querySelector("#audio-enabled").checked = project.audio.enabled;
  document.querySelector("#audio-source").value = project.audio.source || "";
  document.querySelector("#audio-source").disabled = !project.audio.enabled;
  document.querySelector("#audio-volume").value = project.audio.volume;
  for (const [field, values] of [
    ["scenario.gravity_m_s2", project.scenario.gravity_m_s2],
    ["scenario.camera.position", project.scenario.camera.position],
    ["scenario.camera.target", project.scenario.camera.target],
  ]) {
    document.querySelector(`[data-vector="${field}"]`).innerHTML = values.map((value, index) =>
      `<input type="number" step="any" value="${escapeAttribute(value)}" aria-label="${field} ${"XYZ"[index]}">`
    ).join("");
  }
  renderObjects(project.scenario.objects);
  form.hidden = false;
  editorTitle.textContent = project.name || "Untitled project";
  document.querySelector("#project-meta").textContent =
    `${project.id} · ${project.status} · Created ${new Date(project.created_at).toLocaleString()}`;
  clearFieldErrors();
  clearMessage();
  setSaveState("Unsaved changes");
  updateTaskAction();
}

function markDirty() {
  if (!currentProject || form.hidden) return;
  projectSaved = false;
  setSaveState("Unsaved changes");
  clearMessage();
  updateTaskAction();
}

function updateTaskAction(active = false) {
  startTaskButton.disabled = !currentProject || !projectSaved || active;
  startTaskButton.title = !projectSaved
    ? "Save this project before starting a task."
    : active ? "A task is already active." : "";
}

async function refreshProjects() {
  list.replaceChildren();
  listStatus.textContent = "Loading saved projects…";
  try {
    const result = await request("/api/projects");
    if (!result.projects.length) {
      listStatus.textContent = "No saved projects yet.";
      return;
    }
    listStatus.textContent = `${result.projects.length} saved project${result.projects.length === 1 ? "" : "s"}`;
    result.projects.forEach((project) => {
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.projectId = project.id;
      button.setAttribute("aria-current", currentProject?.id === project.id ? "true" : "false");
      const name = document.createElement("span");
      name.className = "project-name";
      name.textContent = project.name;
      const detail = document.createElement("span");
      detail.className = "project-detail";
      detail.textContent = `${project.status} · ${project.scenario.type}`;
      button.append(name, detail);
      button.addEventListener("click", () => loadProject(project.id));
      item.append(button);
      list.append(item);
    });
    if (currentProject) await refreshTasks();
  } catch (error) {
    listStatus.textContent = "Could not read saved projects.";
    showRequestError(error);
  }
}

async function startNewProject() {
  clearFieldErrors();
  try {
    const result = await request("/api/projects/new", {
      method: "POST",
      body: JSON.stringify({ name: "Physics experiment" }),
    });
    populateProject(result.project);
    document.querySelector("#project-name").focus();
    showMessage("New draft ready. Edit the project name and settings, then save it locally.", "success");
  } catch (error) {
    showRequestError(error);
  }
}

async function loadProject(projectId) {
  clearFieldErrors();
  try {
    const result = await request(`/api/projects/${encodeURIComponent(projectId)}`);
    populateProject(result.project, true);
    await refreshProjects();
    showMessage("Project opened from local storage.", "success");
    setSaveState("Saved", "saved");
    await refreshTasks();
  } catch (error) {
    showRequestError(error);
  }
}

async function saveProject(event) {
  event.preventDefault();
  if (!currentProject) return;
  clearFieldErrors();
  setSaveState("Saving…");
  try {
    const result = await request("/api/projects", {
      method: "POST",
      body: JSON.stringify(collectProject()),
    });
    populateProject(result.project, true);
    await refreshProjects();
    showMessage("Project saved locally.", "success");
    setSaveState("Saved", "saved");
    await refreshTasks();
  } catch (error) {
    showRequestError(error);
  }
}

function renderTasks(tasks) {
  taskList.replaceChildren();
  const active = tasks.some((task) => !["succeeded", "failed"].includes(task.status));
  updateTaskAction(active);
  if (!tasks.length) {
    taskListStatus.textContent = "No production tasks have been started for this project.";
    return;
  }
  taskListStatus.textContent = `${tasks.length} task${tasks.length === 1 ? "" : "s"}`;
  tasks.forEach((task) => {
    const card = document.createElement("article");
    card.className = "task-card";
    const heading = document.createElement("div");
    heading.className = "task-card-heading";
    const title = document.createElement("strong");
    title.textContent = `Task ${task.id}`;
    const state = document.createElement("span");
    state.className = `task-state ${task.status}`;
    state.textContent = task.status;
    heading.append(title, state);
    card.append(heading);
    const times = document.createElement("p");
    times.className = "muted";
    times.textContent = `Created ${new Date(task.created_at).toLocaleString()}`
      + (task.run_id ? ` · Kaggle kernel version ${task.run_id}` : "");
    card.append(times);
    if (task.error) {
      const error = document.createElement("p");
      error.className = "task-error";
      error.textContent = task.error;
      card.append(error);
    }
    if (task.result && Object.keys(task.result).length) {
      const results = document.createElement("p");
      results.className = "task-results";
      results.textContent = [
        `Blender: ${task.result.blender_version || "unknown"}`,
        `Kaggle status: ${task.result.remote_status || "unknown"}`,
        `Remote .blend: ${task.result.remote_blend_file || "not available"}`,
        `Local .blend: ${task.result.blend_file || "not available"}`,
        `Blend size: ${task.result.blend_size_bytes || "not available"}`,
        `Blend SHA-256: ${task.result.blend_sha256 || "not available"}`,
        `Local MP4: ${task.result.video_file || "not available"}`,
        `MP4 size: ${task.result.video_size_bytes || "not available"}`,
        `MP4 SHA-256: ${task.result.video_sha256 || "not available"}`,
        `Audio: ${task.result.audio_status || "not available"}`,
        `Report: ${task.result.report_file || "not available"}`,
        `Video report: ${task.result.video_report_file || "not available"}`,
        `Logs: ${task.result.logs_file || "not available"}`,
      ].join("\n");
      card.append(results);
      if (task.result.video_file) {
        const download = document.createElement("a");
        download.href = `/api/tasks/${encodeURIComponent(task.id)}/video`;
        download.download = `${task.project_id}.mp4`;
        download.textContent = "Download verified MP4";
        card.append(download);
      }
    }
    if (Array.isArray(task.events) && task.events.length) {
      const events = document.createElement("ol");
      events.className = "task-events";
      task.events.forEach((event) => {
        const item = document.createElement("li");
        item.textContent = `${event.to_status}: ${event.message}`;
        events.append(item);
      });
      card.append(events);
    }
    taskList.append(card);
  });
  if (active && !taskPollTimer) {
    taskPollTimer = window.setTimeout(async () => {
      taskPollTimer = null;
      await refreshTasks();
    }, 3000);
  }
}

async function refreshTasks() {
  if (!currentProject || !projectSaved) {
    taskList.replaceChildren();
    taskListStatus.textContent = projectSaved
      ? "Select a saved project to view its tasks."
      : "Save or open a project before starting a task.";
    updateTaskAction();
    return;
  }
  try {
    const result = await request(
      `/api/projects/${encodeURIComponent(currentProject.id)}/tasks`
    );
    renderTasks(result.tasks);
  } catch (error) {
    taskListStatus.textContent = "Could not read task history.";
    updateTaskAction();
    showRequestError(error);
  }
}

async function startTask() {
  if (!currentProject || !projectSaved) {
    showMessage("Save the project before starting a task.", "error");
    return;
  }
  startTaskButton.disabled = true;
  taskListStatus.textContent = "Submitting a tracked CPU-only Kaggle task…";
  try {
    const result = await request(
      `/api/projects/${encodeURIComponent(currentProject.id)}/tasks`,
      { method: "POST", body: JSON.stringify({}) }
    );
    showMessage("Task accepted. Its status and event history will update below.", "success");
    renderTasks([result.task]);
    await refreshTasks();
  } catch (error) {
    showRequestError(error);
    await refreshTasks();
  }
}

document.querySelector("#new-project").addEventListener("click", startNewProject);
document.querySelector("#refresh-projects").addEventListener("click", refreshProjects);
document.querySelector("#start-task").addEventListener("click", startTask);
document.querySelector("#save-project").addEventListener("click", (event) => {
  if (!form.reportValidity()) event.preventDefault();
});
form.addEventListener("submit", saveProject);
form.addEventListener("input", markDirty);
form.addEventListener("change", markDirty);
document.querySelector("#add-object").addEventListener("click", () => {
  if (!currentProject) return;
  const objects = collectProject().scenario.objects;
  const number = objects.length + 1;
  objects.push({
    id: `object_${number}`,
    shape: "box",
    position: [0, 0, 1],
    dimensions: [0.5, 0.5, 0.5],
    mass_kg: 1,
    friction: 0.5,
    restitution: 0.2,
  });
  renderObjects(objects);
  markDirty();
});
objectContainer.addEventListener("click", (event) => {
  const button = event.target.closest(".remove-object");
  if (!button || !currentProject) return;
  const objects = collectProject().scenario.objects;
  const index = Number(button.closest(".object-card").dataset.objectIndex);
  if (objects.length <= 2) return;
  objects.splice(index, 1);
  renderObjects(objects);
  markDirty();
});
document.querySelector("#audio-enabled").addEventListener("change", (event) => {
  document.querySelector("#audio-source").disabled = !event.target.checked;
});

refreshProjects();
