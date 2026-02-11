import streamlit.components.v1 as components

# --- English Minimalist Mic Widget ---
_MIC_WIDGET_HTML = """
<div class="mic-mini-root" style="font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size:12px; color:#374151; border-radius:8px; border:1px solid #e5e7eb; padding:10px 12px; background:#f9fafb;">
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
    <div style="font-weight:600; color:#4b5563;">🎙️ Record & Compare</div>
    <div class="mic-status-pill" style="padding:1px 8px; border-radius:999px; background:#f3f4f6; color:#6b7280; font-size:11px; display:flex; align-items:center; gap:4px;">
      <span class="mic-dot" style="width:6px; height:6px; border-radius:999px; background:#9ca3af;"></span>
      <span class="mic-status-text">Disconnected</span>
    </div>
  </div>
  <div style="margin-bottom:6px;">
    <select class="mic-select" style="width:100%; padding:4px 6px; border-radius:6px; border:1px solid #d1d5db; font-size:12px; background:#ffffff;">
      <option value="">Loading microphones...</option>
    </select>
  </div>
  <div style="display:flex; gap:6px; margin-bottom:6px;">
    <button type="button" class="mic-start" style="flex:1; border:none; border-radius:6px; padding:4px 0; font-size:12px; font-weight:600; cursor:pointer; background:#3b82f6; color:#fff;">Start</button>
    <button type="button" class="mic-stop" style="flex:1; border:none; border-radius:6px; padding:4px 0; font-size:12px; font-weight:600; cursor:pointer; background:#e5e7eb; color:#374151;" disabled>Stop</button>
  </div>
  <div class="mic-meter-wrap" style="margin-bottom:4px;">
    <div style="width:100%; height:6px; border-radius:999px; background:#e5e7eb; overflow:hidden;">
      <div class="mic-meter-fill" style="height:100%; width:0%; background:linear-gradient(90deg,#22c55e,#facc15,#f97316,#ef4444); transition:width 80ms linear;"></div>
    </div>
    <div style="text-align:right; font-size:10px; color:#9ca3af; margin-top:2px;">
      Vol: <span class="mic-volume-text">0%</span>
    </div>
  </div>
  <audio class="mic-playback" controls style="width:100%; height:28px;"></audio>
</div>
<script>
(async () => {
  const root = document.currentScript.parentElement;
  const selectEl = root.querySelector('.mic-select');
  const startBtn = root.querySelector('.mic-start');
  const stopBtn = root.querySelector('.mic-stop');
  const playback = root.querySelector('.mic-playback');
  const statusText = root.querySelector('.mic-status-text');
  const dot = root.querySelector('.mic-dot');
  const meterFill = root.querySelector('.mic-meter-fill');
  const volumeText = root.querySelector('.mic-volume-text');

  let stream = null;
  let mediaRecorder = null;
  let chunks = [];
  let audioCtx = null;
  let analyser = null;
  let dataArray = null;
  let animationId = null;

  function setConnected(connected) {
    if (connected) {
      statusText.textContent = 'Recording';
      root.querySelector('.mic-status-pill').style.background = '#dcfce7';
      statusText.style.color = '#166534';
      dot.style.background = '#16a34a';
    } else {
      statusText.textContent = 'Disconnected';
      root.querySelector('.mic-status-pill').style.background = '#f3f4f6';
      statusText.style.color = '#6b7280';
      dot.style.background = '#9ca3af';
    }
  }

  async function initDevices() {
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      const devices = await navigator.mediaDevices.enumerateDevices();
      const inputs = devices.filter(d => d.kind === 'audioinput');
      selectEl.innerHTML = '';
      if (inputs.length === 0) {
        selectEl.innerHTML = '<option value="">No microphone detected</option>';
        return;
      }
      inputs.forEach((d, i) => {
        const opt = document.createElement('option');
        opt.value = d.deviceId;
        opt.textContent = d.label || `Microphone ${i + 1}`;
        selectEl.appendChild(opt);
      });
    } catch (err) {
      selectEl.innerHTML = '<option value="">Cannot access mic, check permissions</option>';
    }
  }

  function stopVisual() {
    if (animationId) cancelAnimationFrame(animationId);
    animationId = null;
    meterFill.style.width = '0%';
    volumeText.textContent = '0%';
    if (audioCtx) {
      audioCtx.close();
      audioCtx = null;
    }
  }

  function startVisual() {
    if (!analyser) return;
    const draw = () => {
      animationId = requestAnimationFrame(draw);
      analyser.getByteTimeDomainData(dataArray);
      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        const v = (dataArray[i] - 128) / 128;
        sum += v * v;
      }
      const rms = Math.sqrt(sum / dataArray.length);
      const vol = Math.min(1, rms * 3);
      const percent = Math.round(vol * 100);
      meterFill.style.width = percent + '%';
      volumeText.textContent = percent + '%';
    };
    draw();
  }

  startBtn.addEventListener('click', async () => {
    try {
      const deviceId = selectEl.value || undefined;
      stream = await navigator.mediaDevices.getUserMedia({
        audio: { deviceId: deviceId ? { exact: deviceId } : undefined, echoCancellation: true, noiseSuppression: true }
      });

      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const source = audioCtx.createMediaStreamSource(stream);
      analyser = audioCtx.createAnalyser();
      analyser.fftSize = 1024;
      dataArray = new Uint8Array(analyser.fftSize);
      source.connect(analyser);
      startVisual();

      chunks = [];
      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.ondataavailable = e => {
        if (e.data.size > 0) chunks.push(e.data);
      };
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        const url = URL.createObjectURL(blob);
        playback.src = url;
      };
      mediaRecorder.start();

      setConnected(true);
      startBtn.disabled = true;
      stopBtn.disabled = false;
    } catch (err) {
      alert('Failed to start recording. Please check permissions.');
    }
  });

  stopBtn.addEventListener('click', () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
    }
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
      stream = null;
    }
    stopVisual();
    setConnected(false);
    startBtn.disabled = false;
    stopBtn.disabled = true;
  });

  initDevices();
})();
</script>
"""

def render_mic_widget():
    components.html(_MIC_WIDGET_HTML, height=210, scrolling=False)

