// Stage 1 UI, vanilla Web Components. No framework.
// Both components share the page's <input type="file"> (referenced by id via
// the `for` attribute) so everything submits with the normal form POST.

/** Resolve the file input this component drives. */
function resolveInput(host) {
  const id = host.getAttribute("for");
  return id ? document.getElementById(id) : null;
}

/**
 * Append File objects to a file input without dropping existing selections.
 * The DataTransfer trick is the standard way to build a FileList in JS.
 */
function addFiles(input, files) {
  const dt = new DataTransfer();
  for (const existing of input.files) dt.items.add(existing);
  for (const file of files) dt.items.add(file);
  input.files = dt.files;
  input.dispatchEvent(new Event("change", { bubbles: true }));
}

/** <upload-dropzone for="file-input"> : drag/drop or click to browse. */
class UploadDropzone extends HTMLElement {
  connectedCallback() {
    this.input = resolveInput(this);
    this.innerHTML = `
      <button type="button" class="dropzone" part="dropzone">
        <span class="dropzone__scan" aria-hidden="true"></span>
        <svg class="dropzone__icon" width="34" height="34" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M12 16V6m0 0l-4 4m4-4l4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M5 19h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <strong>Arrastra las órdenes aquí</strong>
        <span class="dropzone__hint">o toca para buscar en tu equipo</span>
      </button>`;
    this.zone = this.querySelector(".dropzone");

    this.zone.addEventListener("click", () => this.input?.click());

    ["dragenter", "dragover"].forEach((evt) =>
      this.zone.addEventListener(evt, (e) => {
        e.preventDefault();
        this.zone.classList.add("dropzone--active");
      })
    );
    ["dragleave", "drop"].forEach((evt) =>
      this.zone.addEventListener(evt, (e) => {
        e.preventDefault();
        this.zone.classList.remove("dropzone--active");
      })
    );
    this.zone.addEventListener("drop", (e) => {
      if (this.input && e.dataTransfer?.files?.length) {
        addFiles(this.input, e.dataTransfer.files);
      }
    });
  }
}

/** <camera-capture for="file-input"> : live camera -> captured photo -> input. */
class CameraCapture extends HTMLElement {
  connectedCallback() {
    this.input = resolveInput(this);
    this.stream = null;
    this.innerHTML = `
      <div class="camera">
        <button type="button" class="btn" data-role="start">Usar cámara</button>
        <div class="camera__stage" hidden>
          <video class="camera__video" autoplay playsinline muted></video>
          <div class="camera__controls">
            <button type="button" class="btn btn--primary" data-role="shoot">Capturar</button>
            <button type="button" class="btn" data-role="stop">Cerrar</button>
          </div>
        </div>
      </div>`;

    this.stage = this.querySelector(".camera__stage");
    this.video = this.querySelector(".camera__video");
    this.querySelector('[data-role="start"]').addEventListener("click", () => this.start());
    this.querySelector('[data-role="shoot"]').addEventListener("click", () => this.shoot());
    this.querySelector('[data-role="stop"]').addEventListener("click", () => this.stop());
  }

  async start() {
    if (!navigator.mediaDevices?.getUserMedia) {
      alert("La cámara no está disponible en este navegador. Usa el selector de archivos.");
      return;
    }
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
        audio: false,
      });
      this.video.srcObject = this.stream;
      this.stage.hidden = false;
    } catch {
      alert("No se pudo acceder a la cámara.");
    }
  }

  shoot() {
    if (!this.stream) return;
    const canvas = document.createElement("canvas");
    canvas.width = this.video.videoWidth;
    canvas.height = this.video.videoHeight;
    canvas.getContext("2d").drawImage(this.video, 0, 0);
    canvas.toBlob((blob) => {
      if (!blob || !this.input) return;
      const name = `capture-${Date.now()}.png`;
      addFiles(this.input, [new File([blob], name, { type: "image/png" })]);
    }, "image/png");
  }

  stop() {
    this.stream?.getTracks().forEach((track) => track.stop());
    this.stream = null;
    this.video.srcObject = null;
    this.stage.hidden = true;
  }

  disconnectedCallback() {
    this.stop();
  }
}

customElements.define("upload-dropzone", UploadDropzone);
customElements.define("camera-capture", CameraCapture);

// Live thumbnail previews + submit guard.
const input = document.getElementById("file-input");
const preview = document.getElementById("preview");
const form = document.querySelector("form.card");
const submitBtn = form ? form.querySelector('button[type="submit"]') : null;

function syncSubmit() {
  const hasFiles = !!(input && input.files && input.files.length);
  if (submitBtn) submitBtn.disabled = !hasFiles;
}

if (input && preview) {
  input.addEventListener("change", () => {
    preview.innerHTML = "";
    for (const file of input.files) {
      const img = document.createElement("img");
      img.className = "preview__thumb";
      img.src = URL.createObjectURL(file);
      img.onload = () => URL.revokeObjectURL(img.src);
      preview.appendChild(img);
    }
    syncSubmit();
  });
}

if (form) {
  syncSubmit(); // start disabled
  form.addEventListener("submit", (e) => {
    if (!input || !input.files || input.files.length === 0) {
      e.preventDefault(); // belt-and-suspenders: never submit empty
    }
  });
}
