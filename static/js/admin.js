// Initialize SimpleMDE
var simplemde = new SimpleMDE({
    element: document.getElementById("content_md"),
    spellChecker: false,
    toolbar: ["bold", "italic", "heading", "|", "quote", "unordered-list", "ordered-list", "|", "link", "image", "|", "preview", "side-by-side", "fullscreen", "|", "guide"]
});

// Update file name display
function updateFileName(input, targetId) {
    const fileName = input.files[0]?.name || 'Upload file baru (opsional)';
    document.getElementById(targetId).textContent = fileName;
}

// ========== MULTI-VISUALIZATION MANAGEMENT ==========
let vizCounter = 0;

function addVizField() {
    vizCounter++;
    const container = document.getElementById('viz-container-list');
    const emptyMsg = document.getElementById('viz-empty-msg');
    emptyMsg.classList.add('hidden');

    const html = `
        <div class="viz-item flex items-center gap-3 p-3 bg-slate-50 rounded-xl border border-slate-200" id="viz-item-${vizCounter}">
            <span class="w-7 h-7 bg-white rounded-lg border border-slate-200 flex items-center justify-center text-sm font-medium text-slate-600">+</span>
            <input type="text" name="viz_titles[]" placeholder="Judul visualisasi" 
                class="flex-1 px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary-500">
            <div class="relative">
                <input type="file" name="viz_files[]" accept=".html,.htm" id="viz-file-${vizCounter}" class="hidden" onchange="updateVizFileName(${vizCounter})">
                <label for="viz-file-${vizCounter}" 
                    class="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50 text-sm">
                    <i class="bi bi-file-earmark-code text-slate-400"></i>
                    <span id="viz-fname-${vizCounter}" class="text-slate-500">Pilih file HTML</span>
                </label>
            </div>
            <button type="button" onclick="removeViz(${vizCounter})" class="p-2 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg">
                <i class="bi bi-trash"></i>
            </button>
        </div>`;

    container.insertAdjacentHTML('beforeend', html);
}

function removeViz(index) {
    const item = document.getElementById('viz-item-' + index);
    if (item) {
        item.remove();
        const container = document.getElementById('viz-container-list');
        const emptyMsg = document.getElementById('viz-empty-msg');
        if (container.children.length === 0 && !document.querySelector('.existing-viz')) {
            emptyMsg.classList.remove('hidden');
        }
    }
}

// Delete existing visualization (mark for deletion)
let deleteIndices = [];

function deleteExistingViz(index, title) {
    if (!confirm(`Yakin ingin menghapus visualisasi "${title}"?`)) {
        return;
    }

    // Hide the element visually
    const item = document.getElementById('existing-viz-' + index);
    if (item) {
        item.style.display = 'none';
        item.classList.add('marked-for-delete');
    }

    // Add to delete list
    if (!deleteIndices.includes(index)) {
        deleteIndices.push(index);
    }

    // Update hidden field
    document.getElementById('delete-viz-indices').value = deleteIndices.join(',');

    // Check if all existing viz items are hidden
    const visibleItems = document.querySelectorAll('.existing-viz:not(.marked-for-delete)');
    if (visibleItems.length === 0) {
        const list = document.getElementById('existing-viz-list');
        if (list) list.style.display = 'none';
    }
}

function updateVizFileName(index) {
    const input = document.getElementById('viz-file-' + index);
    const label = document.getElementById('viz-fname-' + index);
    if (input.files[0]) {
        label.textContent = input.files[0].name;
        label.classList.remove('text-slate-500');
        label.classList.add('text-slate-800');
    }
}

// Prepare form submission - sync SimpleMDE content
function prepareSubmit() {
    const content = simplemde.value();
    document.getElementById('content_md').value = content;

    const title = document.getElementById('title').value.trim();
    if (!title) {
        alert('Judul artikel harus diisi!');
        return false;
    }
    if (!content || content.trim() === '') {
        alert('Konten artikel harus diisi!');
        return false;
    }
    return true;
}

// Delete post via separate form
function deletePost() {
    if (confirm('Yakin ingin menghapus artikel ini secara permanen?')) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '{{ url_for("admin_delete", post_id=post.id) }}';
        document.body.appendChild(form);
        form.submit();
    }
}