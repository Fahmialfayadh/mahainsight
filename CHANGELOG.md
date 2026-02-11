# Update - MahaInsight 11 Februari 2026

## Perubahan Terbaru  

Artikel ini adalah perubahan yang dilakukan pada project MahaInsight Pada tanggal 11 Februari 2026

---

### 1. Deep Thinking: Proses Analisis Terlihat + Timer

**File yang diubah:**
- `static/js/detail.js` — fungsi `appendMessageWithThinking()`, `sendChat()`
- `templates/detail.html` — toolbar AI section

**Apa yang berubah:**

- Fungsi `appendMessageWithThinking()` menerima parameter baru `elapsedSeconds` untuk menampilkan berapa lama AI memproses jawaban.
- Badge waktu (contoh: `12s`, `1m 5s`) ditampilkan di samping label "Proses analisis" dalam elemen `<details>`.
- Saat Deep Think aktif, typing indicator menampilkan **live timer** yang berjalan setiap detik selama menunggu respons AI.
- Indikator berupa box "Deep Thinking" dengan ikon CPU berdenyut dan teks "Menganalisis data dan menyusun jawaban...".

**Alasan:**

Sebelumnya, saat Deep Think diaktifkan, pengguna hanya melihat teks "Menganalisis..." tanpa indikasi berapa lama proses berlangsung. Ini membuat pengguna tidak tahu apakah sistem masih bekerja atau sudah hang. Timer real-time memberikan transparansi dan kepercayaan bahwa proses masih berjalan. Badge waktu di hasil akhir juga berguna untuk evaluasi performa AI.

---

### 2. Quiz: Tombol Minimize

**File yang diubah:**
- `static/js/detail.js` — fungsi baru `minimizeQuiz()`, `restoreQuiz()`, `removeQuizFloatingBtn()`

```javascript
function minimizeQuiz() {
    const modal = document.getElementById('quiz-modal');
    if (modal) modal.classList.add('hidden');

    if (!document.getElementById('quiz-floating-btn')) {
        const btn = document.createElement('button');
        btn.id = 'quiz-floating-btn';
        btn.onclick = restoreQuiz;
        btn.className = 'fixed bottom-6 right-6 z-[60] flex items-center gap-2 px-4 py-3 bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold rounded-2xl shadow-xl shadow-brand-500/30 transition-all duration-300 animate-bounce-once ring-2 ring-brand-400/30';
        btn.innerHTML = `
            <i class="bi bi-puzzle text-base"></i>
            <span>Lanjut Quiz</span>
            <span class="ml-1 px-1.5 py-0.5 bg-white/20 rounded text-[10px] font-medium">${currentQuestionIndex + 1}/${quizQuestions.length}</span>
        `;
        document.body.appendChild(btn);

        setTimeout(() => btn.classList.remove('animate-bounce-once'), 2000);
    }
}
```
```javascript

function restoreQuiz() {
    const modal = document.getElementById('quiz-modal');
    if (modal) modal.classList.remove('hidden');
    removeQuizFloatingBtn();
}
```
```javascript
function removeQuizFloatingBtn() {
    const btn = document.getElementById('quiz-floating-btn');
    if (btn) btn.remove();
}
```
- `templates/detail.html` — header modal quiz
- `static/style/base.css` — animasi `animate-bounce-once`

**Apa yang berubah:**

- Header modal quiz sekarang memiliki **dua tombol**: minimize (ikon dash) dan close (ikon X).
- **Minimize** menyembunyikan modal quiz tanpa mereset state (skor, pertanyaan saat ini, jawaban yang sudah dipilih tetap tersimpan).
- Saat quiz di-minimize, muncul **floating button** "Lanjut Quiz" di pojok kanan bawah layar dengan badge progress (contoh: `2/5`).
- Tombol floating memiliki animasi bounce singkat untuk menarik perhatian pengguna.
- Klik tombol floating mengembalikan modal quiz ke kondisi terakhir.
- **Close** (tombol X) tetap berfungsi seperti sebelumnya: menutup dan mereset quiz sepenuhnya.
- `resetQuiz()` juga membersihkan floating button jika ada.

**Alasan:**

Quiz mengharuskan pengguna menjawab pertanyaan berdasarkan isi artikel. Namun modal quiz menutupi seluruh layar, sehingga pengguna tidak bisa membaca kembali artikel untuk mencari jawaban. Tombol minimize memungkinkan pengguna menyembunyikan quiz sementara, scroll ke artikel untuk "mencontek", lalu melanjutkan quiz tanpa kehilangan progress.

---

### 3. AI Chat: Stream Mode (SSE)

**File yang diubah:**
- `app.py` — endpoint `/api/ai/chat`
- `static/js/detail.js` — fungsi `sendChat()`, fungsi baru `createStreamingBubble()`, `createStreamingBubbleWithThinking()`

```javascript
function createStreamingBubble() {
    const welcomeState = document.getElementById('welcome-state');
    if (welcomeState) welcomeState.remove();

    const div = document.createElement('div');
    div.className = 'flex gap-3 items-start';
    div.innerHTML = `
        <div class="w-7 h-7 rounded-lg bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center text-brand-600 dark:text-brand-400 shrink-0 mt-0.5">
            <i class="bi bi-robot text-sm"></i>
        </div>
        <div class="text-sm text-slate-700 dark:text-dm-200 max-w-[85%] prose prose-sm dark:prose-invert prose-p:my-1 prose-headings:my-2 leading-relaxed" id="stream-content">
            <span class="inline-block w-1.5 h-4 bg-brand-500 animate-pulse rounded-sm align-middle"></span>
        </div>
    `;
    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return div;
}

function createStreamingBubbleWithThinking() {
    const welcomeState = document.getElementById('welcome-state');
    if (welcomeState) welcomeState.remove();

    const div = document.createElement('div');
    div.className = 'flex gap-3 items-start';
    div.innerHTML = `
        <div class="w-7 h-7 rounded-lg bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center text-brand-600 dark:text-brand-400 shrink-0 mt-0.5">
            <i class="bi bi-robot text-sm"></i>
        </div>
        <div class="text-sm max-w-[85%]">
            <details class="group mb-2" open id="stream-thinking-details">
                <summary class="list-none flex items-center gap-1.5 cursor-pointer text-[11px] text-slate-400 dark:text-dm-500 hover:text-brand-500 transition py-0.5">
                    <i class="bi bi-cpu text-[10px]"></i>
                    <span>Proses analisis</span>
                    <span class="ml-1 px-1.5 py-0.5 bg-brand-50 dark:bg-brand-900/20 text-brand-600 dark:text-brand-400 rounded text-[10px] font-medium" id="stream-thinking-timer"><i class="bi bi-clock text-[9px] mr-0.5"></i>0s</span>
                    <i class="bi bi-chevron-down text-[9px] transition-transform group-open:rotate-180 ml-0.5"></i>
                </summary>
                <div class="mt-1.5 pl-3 border-l border-slate-200 dark:border-dm-600">
                    <div class="text-xs text-slate-500 dark:text-dm-400 prose prose-xs dark:prose-invert max-w-none leading-relaxed" id="stream-thinking-content">
                        <span class="inline-block w-1.5 h-3 bg-slate-400 animate-pulse rounded-sm align-middle"></span>
                    </div>
                </div>
            </details>
            <div class="prose prose-sm dark:prose-invert leading-relaxed text-slate-700 dark:text-dm-200 hidden" id="stream-answer-content"></div>
        </div>
    `;
    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return div;
}
```
#### Backend (`app.py`)

**Apa yang berubah:**

- Pemanggilan Groq API diubah dari mode sinkron (`stream=False`) ke **streaming** (`stream=True`).
- Response endpoint berubah dari `jsonify()` (JSON biasa) menjadi **Server-Sent Events (SSE)** dengan `mimetype='text/event-stream'`.
- Format event SSE:
  - `{"type": "token", "content": "..."}` — setiap potongan teks dari AI.
  - `{"type": "done", "remaining": N}` — sinyal stream selesai, berisi sisa kuota pertanyaan.
  - `{"type": "error", "message": "..."}` — jika terjadi error selama streaming.
- `increment_user_ai_usage()` dipanggil **sebelum** streaming dimulai, bukan setelah. Ini memastikan kuota tetap tercatat meskipun koneksi stream terputus di tengah jalan.
- Header response ditambah `Cache-Control: no-cache`, `X-Accel-Buffering: no`, dan `Connection: keep-alive` untuk mencegah buffering oleh proxy/server.
- Error non-stream (rate limit, parameter kosong, post tidak ditemukan) tetap mengembalikan JSON biasa agar frontend bisa membedakan.

**Alasan:**

Mode non-stream membuat pengguna menunggu seluruh respons AI selesai diproses sebelum melihat apapun. Untuk model LLM, ini bisa memakan waktu 5-15 detik tergantung panjang jawaban. Dengan streaming, token pertama muncul dalam 1-2 detik dan teks mengalir secara real-time, memberikan pengalaman yang jauh lebih responsif.

#### Frontend (`static/js/detail.js`)

**Apa yang berubah:**

**Fungsi baru — `createStreamingBubble()`:**
- Membuat bubble chat AI kosong dengan kursor berkedip (blinking cursor).
- Elemen `#stream-content` menjadi target rendering token.

**Fungsi baru — `createStreamingBubbleWithThinking()`:**
- Membuat bubble chat AI dengan dua bagian: `<details open>` untuk thinking dan `<div hidden>` untuk answer.
- Elemen `#stream-thinking-content` untuk konten thinking, `#stream-answer-content` untuk jawaban.
- Badge timer `#stream-thinking-timer` diperbarui secara real-time oleh interval yang sudah ada.

**Fungsi `sendChat()` ditulis ulang:**

- Setelah menerima response, mengecek `Content-Type` header:
  - Jika `application/json` → error response (rate limit, dll), ditangani seperti sebelumnya.
  - Jika `text/event-stream` → masuk ke mode streaming.
- Menggunakan `ReadableStream` API (`resp.body.getReader()`) untuk membaca chunk secara bertahap.
- Setiap chunk di-decode dan diparsing sebagai SSE event (`data: {...}`).
- Buffer digunakan untuk menangani chunk yang terpotong di tengah baris.

**Mode normal (tanpa Deep Think):**
- Setiap token langsung di-render ke bubble chat menggunakan `marked.parse()`.
- Kursor berkedip muncul di akhir teks selama streaming berlangsung.
- Setelah event `done`, kursor dihapus dan teks final di-render ulang tanpa kursor.

**Mode Deep Think:**
- Stream dimulai di fase `thinking`. Token yang masuk di-render ke bagian thinking (dalam `<details open>`).
- Tag `<thinking>` di-strip saat rendering.
- Saat tag `</thinking>` terdeteksi dalam accumulated text:
  - Bagian thinking di-render final.
  - `<details>` ditutup (atribut `open` dihapus).
  - Bagian answer (`#stream-answer-content`) ditampilkan dengan kursor baru.
  - Variabel `fullText` di-reset untuk hanya menyimpan konten setelah `</thinking>`.
  - Fase berubah dari `thinking` ke `answer`.
- Di fase `answer`, tag `<answer>` dan `</answer>` di-strip, konten di-render secara streaming.
- Setelah event `done`:
  - Timer dihentikan dan badge diperbarui ke nilai final.
  - Kedua bagian (thinking dan answer) di-render ulang tanpa kursor.

**Alasan:**

Frontend perlu diubah total karena `resp.json()` tidak bisa digunakan untuk SSE. `ReadableStream` API memungkinkan pembacaan chunk-by-chunk dari response body. Parsing SSE dilakukan manual karena `EventSource` API hanya mendukung GET request, sedangkan endpoint ini menggunakan POST dengan body JSON dan header autentikasi.

Untuk thinking mode, parsing tag `<thinking>` dan `<answer>` dilakukan secara on-the-fly di frontend (bukan di backend) karena dalam mode stream, backend mengirim token mentah tanpa bisa memisahkan bagian thinking dan answer terlebih dahulu — token dikirim sesuai urutan generate dari LLM.

---

## Ringkasan hal yang diubah

| Tipe | Perubahan |
|------|-----------|
| Backend | Endpoint `/api/ai/chat` → SSE streaming |
| Frontend | Streaming UI, thinking timer, quiz minimize |
| Template | Tombol minimize di header modal quiz |
| Style | Animasi `bounceOnce` untuk floating button |
