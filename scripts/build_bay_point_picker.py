"""Generate the in-conversation bay 0/1 corner picker."""

import base64
from pathlib import Path

import cv2


SOURCE = Path(
    r"C:\Users\srini\Downloads\extracted\analysis_frames\opencv_geometry\multiframe\distal_ribs_sharpest_8x.png"
)
OUTPUT = Path(
    r"C:\Users\srini\.codex\visualizations\2026\08\26\01a03d98-ba5b-7732-9a42-2af0371b7261\bay-point-picker.html"
)


FRAGMENT = r'''
<div id="bay-point-picker">
  <h2>Bay 0–1 corner picker</h2>
  <div class="viz-controls" aria-label="Bay selection and editing">
    <button type="button" class="btn btn-primary" data-bay="0" aria-pressed="true">Edit bay 0</button>
    <button type="button" class="btn" data-bay="1" aria-pressed="false">Edit bay 1</button>
    <button type="button" class="btn btn-ghost" id="clear-active">Clear active bay</button>
    <button type="button" class="btn btn-ghost" id="reset-points">Reset</button>
  </div>
  <div class="card">
    <canvas id="bay-canvas" width="440" height="980" aria-label="Finger image with draggable bay corner points"></canvas>
  </div>
  <div class="text-small text-muted" id="picker-status" aria-live="polite"></div>
  <pre><code id="picker-json"></code></pre>
  <div class="viz-controls">
    <button type="button" class="btn btn-primary" id="send-points">Send points to Codex</button>
    <button type="button" class="btn" id="copy-points">Copy JSON</button>
  </div>
</div>

<style>
  #bay-point-picker { width: 100%; max-width: 100%; overflow-x: hidden; }
  #bay-point-picker .card { box-sizing: border-box; width: 100%; max-width: 460px; margin-top: 12px; padding: 10px; }
  #bay-point-picker canvas { display: block; width: 100%; max-width: 100%; height: auto; touch-action: none; cursor: crosshair; }
  #bay-point-picker pre { max-width: 460px; white-space: pre-wrap; margin: 10px 0; }
</style>

<script>
(() => {
  const root = document.getElementById('bay-point-picker');
  const canvas = document.getElementById('bay-canvas');
  const context = canvas.getContext('2d');
  const status = document.getElementById('picker-status');
  const jsonView = document.getElementById('picker-json');
  const image = new Image();
  image.src = '__IMAGE_DATA__';

  const labels = ['outer top', 'inner top', 'inner bottom', 'outer bottom'];
  const defaults = {
    0: [[304, 74], [677, 75], [655, 229], [266, 243]],
    1: [[260, 320], [654, 290], [640, 430], [246, 566]]
  };
  let points = JSON.parse(JSON.stringify(defaults));
  let activeBay = 0;
  let dragging = null;

  function themeColor(name) {
    const probe = document.createElement('span');
    probe.style.color = `var(${name})`;
    probe.style.display = 'none';
    root.appendChild(probe);
    const resolved = getComputedStyle(probe).color;
    probe.remove();
    return resolved;
  }
  const toCanvas = ([x, y]) => [x / 2, y / 2];
  const toSource = (x, y) => [
    Math.round(Math.max(0, Math.min(879, x * 2))),
    Math.round(Math.max(0, Math.min(1959, y * 2)))
  ];

  function valid() {
    return points[0].length === 4 && points[1].length === 4;
  }

  function payload() {
    return {
      order: labels,
      bay0: points[0],
      bay1: points[1],
      source_size_px: [880, 1960]
    };
  }

  function drawBay(index, active) {
    const bay = points[index];
    if (!bay.length) return;
    const red = themeColor('--red');
    const purple = themeColor('--purple');
    const yellow = themeColor('--yellow');
    const foreground = themeColor('--foreground');
    const canvasPoints = bay.map(toCanvas);
    context.save();
    context.globalAlpha = active ? 1 : 0.48;
    context.lineJoin = 'round';
    context.lineCap = 'round';
    context.lineWidth = active ? 3 : 2;
    if (bay.length === 4) {
      context.beginPath();
      context.moveTo(...canvasPoints[0]);
      context.lineTo(...canvasPoints[1]);
      context.strokeStyle = red;
      context.stroke();
      context.beginPath();
      context.moveTo(...canvasPoints[1]);
      context.lineTo(...canvasPoints[2]);
      context.strokeStyle = yellow;
      context.stroke();
      context.beginPath();
      context.moveTo(...canvasPoints[2]);
      context.lineTo(...canvasPoints[3]);
      context.strokeStyle = red;
      context.stroke();
      context.beginPath();
      context.moveTo(...canvasPoints[3]);
      context.lineTo(...canvasPoints[0]);
      context.strokeStyle = purple;
      context.stroke();
    }
    canvasPoints.forEach(([x, y], pointIndex) => {
      context.beginPath();
      context.arc(x, y, active ? 7 : 5, 0, Math.PI * 2);
      context.fillStyle = active ? red : foreground;
      context.fill();
      context.font = '500 12px system-ui, sans-serif';
      context.fillStyle = foreground;
      context.fillText(String(pointIndex + 1), x + 9, y - 8);
    });
    context.restore();
  }

  function render() {
    context.clearRect(0, 0, canvas.width, canvas.height);
    if (image.complete) context.drawImage(image, 0, 0, canvas.width, canvas.height);
    drawBay(1 - activeBay, false);
    drawBay(activeBay, true);
    jsonView.textContent = JSON.stringify({ bay0: points[0], bay1: points[1] });
    const next = points[activeBay].length < 4 ? labels[points[activeBay].length] : 'drag any numbered point';
    status.textContent = `Bay ${activeBay}: ${next}. Point order is outer top, inner top, inner bottom, outer bottom.`;
  }

  function canvasPosition(event) {
    const bounds = canvas.getBoundingClientRect();
    return [
      (event.clientX - bounds.left) * canvas.width / bounds.width,
      (event.clientY - bounds.top) * canvas.height / bounds.height
    ];
  }

  canvas.addEventListener('pointerdown', (event) => {
    const [x, y] = canvasPosition(event);
    let nearest = null;
    let nearestDistance = 18;
    points[activeBay].forEach((point, index) => {
      const [px, py] = toCanvas(point);
      const distance = Math.hypot(px - x, py - y);
      if (distance < nearestDistance) {
        nearest = index;
        nearestDistance = distance;
      }
    });
    if (nearest !== null) {
      dragging = nearest;
      canvas.setPointerCapture(event.pointerId);
    } else if (points[activeBay].length < 4) {
      points[activeBay].push(toSource(x, y));
      dragging = points[activeBay].length - 1;
      canvas.setPointerCapture(event.pointerId);
      render();
    }
  });

  canvas.addEventListener('pointermove', (event) => {
    if (dragging === null) return;
    const [x, y] = canvasPosition(event);
    points[activeBay][dragging] = toSource(x, y);
    render();
  });

  const finishDrag = () => { dragging = null; };
  canvas.addEventListener('pointerup', finishDrag);
  canvas.addEventListener('pointercancel', finishDrag);

  root.querySelectorAll('[data-bay]').forEach((button) => {
    button.addEventListener('click', () => {
      activeBay = Number(button.dataset.bay);
      root.querySelectorAll('[data-bay]').forEach((item) => {
        const selected = Number(item.dataset.bay) === activeBay;
        item.setAttribute('aria-pressed', String(selected));
        item.classList.toggle('btn-primary', selected);
      });
      render();
    });
  });

  document.getElementById('clear-active').addEventListener('click', () => {
    points[activeBay] = [];
    render();
  });

  document.getElementById('reset-points').addEventListener('click', () => {
    points = JSON.parse(JSON.stringify(defaults));
    render();
  });

  document.getElementById('copy-points').addEventListener('click', async () => {
    await navigator.clipboard.writeText(JSON.stringify(payload(), null, 2));
    status.textContent = 'Coordinates copied.';
  });

  document.getElementById('send-points').addEventListener('click', async () => {
    if (!valid()) {
      status.textContent = 'Both bays need four points before sending.';
      return;
    }
    const coordinates = JSON.stringify(payload());
    if (window.openai?.sendFollowUpMessage) {
      await window.openai.sendFollowUpMessage({
        title: 'Use corrected bay points',
        prompt: `Use these manually corrected corner coordinates for bays 0 and 1. The point order is outer top, inner top, inner bottom, outer bottom. Keep bays 2–5 unchanged and rebuild the two continuous rails through these endpoints: ${coordinates}`
      });
      status.textContent = 'Coordinates sent.';
    } else {
      await navigator.clipboard.writeText(coordinates);
      status.textContent = 'Coordinates copied; paste them into the conversation.';
    }
  });

  image.addEventListener('load', render);
  render();
})();
</script>
'''


def main():
    image = cv2.imread(str(SOURCE), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(SOURCE)
    image = cv2.resize(image, (440, 980), interpolation=cv2.INTER_AREA)
    ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 82])
    if not ok:
        raise RuntimeError("Could not encode point-picker background")
    data_uri = "data:image/jpeg;base64," + base64.b64encode(encoded).decode("ascii")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(FRAGMENT.replace("__IMAGE_DATA__", data_uri), encoding="utf-8")
    print(OUTPUT)
    print("bytes", OUTPUT.stat().st_size)


if __name__ == "__main__":
    main()
