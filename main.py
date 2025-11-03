import os
import glob
import time
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np
import mss
from pynput import keyboard
try:
	import win32gui  # type: ignore
	import win32con  # type: ignore
	import win32api  # type: ignore
	import win32ui   # type: ignore
except Exception:
	win32gui = None
try:
	import dxcam  # type: ignore
except Exception:
	dxcam = None


TEMPLATES_DIR = "."  # current folder with PNGs
SCREEN_SCALE = 1.0  # downscale factor for preview; matching uses multi-scale
MATCH_THRESHOLD = 0.7  # default threshold; can override via filename: name@0.7.png
COOLDOWN_SECONDS = 0.06  # tuned for smoother feel
USE_GRAYSCALE = True  # grayscale improves robustness
USE_EDGE_ENHANCE = False  # off for ORB path; keeps colors as-is in preview
USE_GPU = True  # try OpenCV CUDA when available and compatible
# ORB/Feature mode
USE_ORB = True
USE_TEMPLATE_MATCHING = False
USE_OPENCL = True  # enable OpenCL (AMD/NVIDIA/Intel) via UMat
USE_DXCAM = True  # DXGI capture; set False to force MSS
USE_OVERLAY = True  # draw floating boxes on desktop instead of preview window
# Desktop overlay (transparent, click-through) for drawing boxes
class DesktopOverlay:

	def __init__(self, title: str = "Matcher Overlay") -> None:
		self.title = title
		self.hwnd = None
		self.hdc_mem = None
		self.bmp = None
		self.size = (0, 0)

	def create(self, width: int, height: int) -> None:
		if win32gui is None:
			return
		wc = win32gui.WNDCLASS()
		wc.hInstance = win32api.GetModuleHandle(None)
		wc.lpszClassName = self.title
		wc.lpfnWndProc = win32gui.DefWindowProc
		atom = win32gui.RegisterClass(wc)
		style = win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW
		self.hwnd = win32gui.CreateWindowEx(
			style,
			atom,
			self.title,
			win32con.WS_POPUP,
			0,
			0,
			width,
			height,
			0,
			0,
			wc.hInstance,
			None,
		)
		win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)
		self.size = (width, height)

	def update(self, img_bgra: np.ndarray) -> bool:
		if win32gui is None or self.hwnd is None:
			return False
		try:
			hwnd_dc = win32gui.GetDC(self.hwnd)
			mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
			h, w = img_bgra.shape[:2]
			# Create DIB section from buffer (top-down by negative height)
			bmi = win32gui.BITMAPINFO()
			bmi['bmiHeader']['biSize'] = 40
			bmi['bmiHeader']['biWidth'] = w
			bmi['bmiHeader']['biHeight'] = -h
			bmi['bmiHeader']['biPlanes'] = 1
			bmi['bmiHeader']['biBitCount'] = 32
			bmi['bmiHeader']['biCompression'] = win32con.BI_RGB
			dst_pt = (0, 0)
			size = (w, h)
			src_pt = (0, 0)
			# Create a memory DC+bitmap
			self.hdc_mem = win32ui.CreateDCFromHandle(win32gui.CreateCompatibleDC(hwnd_dc))
			dib = win32gui.CreateDIBSection(hwnd_dc, bmi, win32con.DIB_RGB_COLORS, img_bgra.tobytes())
			bmp = win32ui.CreateBitmapFromHandle(dib)
			self.hdc_mem.SelectObject(bmp)
			blend = win32gui.BLENDFUNCTION()
			blend.AlphaFormat = win32con.AC_SRC_ALPHA
			blend.SourceConstantAlpha = 255
			blend.BlendOp = win32con.AC_SRC_OVER
			win32gui.UpdateLayeredWindow(self.hwnd, 0, dst_pt, size, self.hdc_mem.GetSafeHdc(), src_pt, 0, blend, win32con.ULW_ALPHA)
			# Cleanup
			win32gui.ReleaseDC(self.hwnd, hwnd_dc)
			self.hdc_mem.DeleteDC()
			mfc_dc.DeleteDC()
			self.hdc_mem = None
			return True
		except Exception:
			return False

	def close(self) -> None:
		if self.hwnd is not None and win32gui is not None:
			try:
				win32gui.DestroyWindow(self.hwnd)
			except Exception:
				pass
		self.hwnd = None
# We'll scale templates rather than the screen so huge PNGs can match when shown smaller
TEMPLATE_SCALES = [
	0.2, 0.25, 0.33, 0.4, 0.5,
	0.6, 0.75, 0.85, 1.0, 1.15, 1.33
]  # adjust as needed
UI_SCALE = 2.0  # larger UI text
WINDOW_EXCLUDE = True  # mask out our preview window to avoid "mirror" detections
MAX_MATCHES_PER_TEMPLATE_PER_SCALE = 3  # limit boxes per template per scale
TOPK_PER_TEMPLATE_PER_SCALE = 2  # compute up to K best peaks per template per scale

# Enable OpenCL (T-API) and prefer AMD device when available
try:
	cv2.ocl.setUseOpenCL(USE_OPENCL)
	os.environ.setdefault("OPENCV_OPENCL_DEVICE", "GPU:AMD")
except Exception:
	pass


def parse_threshold_from_name(filename: str, default_thr: float) -> float:
	# Example: wheat lvl 1@0.72.png
	name = Path(filename).stem
	if "@" in name:
		try:
			thr_str = name.split("@")[-1]
			thr = float(thr_str)
			if 0.0 < thr < 1.0:
				return thr
		except Exception:
			return default_thr
	return default_thr


def load_templates(directory: str) -> Dict[str, Dict]:

	templates: Dict[str, Dict] = {}
	pattern = os.path.join(directory, "*.png")
	for path in glob.glob(pattern):
		img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
		if img is None:
			continue
		# Convert to BGR if image has alpha; keep template and mask for transparency
		mask = None
		if img.shape[2] == 4:
			bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
			alpha = img[:, :, 3]
			mask = cv2.threshold(alpha, 0, 255, cv2.THRESH_BINARY)[1]
		else:
			bgr = img
		thr = parse_threshold_from_name(Path(path).name, MATCH_THRESHOLD)
		if USE_ORB:
			gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
			# Precompute ORB features (UMat to favor OpenCL pipeline)
			orb = cv2.ORB_create(nfeatures=1500, scaleFactor=1.2, nlevels=8, fastThreshold=7)
			ugray = cv2.UMat(gray) if USE_OPENCL else gray
			kp, des = orb.detectAndCompute(ugray, None)
			des = des.get() if isinstance(des, cv2.UMat) else des
			h, w = gray.shape[:2]
			corners = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
			templates[path] = {
				"image": bgr,
				"mask": mask,
				"name": Path(path).name,
				"kp": kp,
				"des": des,
				"corners": corners,
			}
		else:
			if USE_GRAYSCALE:
				gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
				templates[path] = {
					"image": gray,
					"mask": mask,
					"name": Path(path).name,
					"threshold": thr,
					"scaled": {},
				}
			else:
				templates[path] = {
					"image": bgr,
					"mask": mask,
					"name": Path(path).name,
					"threshold": thr,
					"scaled": {},
				}
	return templates


def orb_match_all(screen_bgr: np.ndarray, templates: Dict[str, Dict]) -> Tuple[List[Tuple[str, float, np.ndarray]], Dict[str, float]]:

	results: List[Tuple[str, float, np.ndarray]] = []
	best_scores: Dict[str, float] = {info["name"]: 0.0 for info in templates.values()}

	gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
	ugray = cv2.UMat(gray) if USE_OPENCL else gray

	orb = cv2.ORB_create(nfeatures=2500, scaleFactor=1.2, nlevels=8, fastThreshold=7)
	scene_kp, scene_des = orb.detectAndCompute(ugray, None)
	if isinstance(scene_des, cv2.UMat):
		scene_des = scene_des.get()
	if scene_des is None or len(scene_des) == 0:
		return results, best_scores

	# FLANN-LSH for ORB (binary descriptors)
	index_params = dict(algorithm=6, table_number=12, key_size=12, multi_probe_level=1)
	search_params = dict(checks=64)
	flann = cv2.FlannBasedMatcher(index_params, search_params)

	for info in templates.values():
		tpl_des = info.get("des")
		if tpl_des is None or len(tpl_des) == 0:
			continue
		knn = flann.knnMatch(tpl_des.astype(np.uint8), scene_des.astype(np.uint8), k=2)
		good = []
		for m, n in knn:
			if m.distance < 0.8 * n.distance:
				good.append(m)
		best_scores[info["name"]] = float(len(good))
		if len(good) < 10:
			continue
		src_pts = np.float32([info["kp"][m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
		dst_pts = np.float32([scene_kp[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
		H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 4.0)
		if H is None:
			continue
		inliers = int(mask.sum()) if mask is not None else len(good)
		# Confidence: ratio of inliers vs min(template_kp, 60)
		tpl_kp_count = max(1, min(len(info["kp"]), 60))
		conf = min(1.0, inliers / float(tpl_kp_count))
		corners = info["corners"]
		proj = cv2.perspectiveTransform(corners, H)  # shape (4,1,2)
		quad = proj.reshape(4, 2)
		results.append((info["name"], conf, quad))

	return results, best_scores


def get_scaled_template(info: Dict, scale: float) -> Tuple[np.ndarray, np.ndarray]:

	cache = info["scaled"]
	if scale in cache:
		return cache[scale]["image"], cache[scale]["mask"]
	img = info["image"]
	msk = info["mask"]
	if abs(scale - 1.0) < 1e-3:
		res_img = img
		res_msk = msk
	else:
		new_w = max(1, int(round(img.shape[1] * scale)))
		new_h = max(1, int(round(img.shape[0] * scale)))
		res_img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
		res_msk = None
		if msk is not None:
			res_msk = cv2.resize(msk, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
	cache[scale] = {"image": res_img, "mask": res_msk}
	return res_img, res_msk


def match_all_multiscale(screen_bgr: np.ndarray, templates: Dict[str, Dict]) -> Tuple[List[Tuple[str, float, Tuple[int, int, int, int]]], Dict[str, float]]:

	matches: List[Tuple[str, float, Tuple[int, int, int, int]]] = []
	best_scores: Dict[str, float] = {info["name"]: 0.0 for info in templates.values()}
	# Prepare screen for grayscale if needed
	if USE_GRAYSCALE:
		screen = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
	else:
		screen = screen_bgr

	# Optional edge map
	if USE_EDGE_ENHANCE:
		if screen.ndim == 3:
			s_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
		else:
			s_gray = screen
		edges = cv2.Canny(s_gray, 50, 150)
		screen_for_match = edges
	else:
		screen_for_match = screen
	sh, sw = screen.shape[:2]

	# Setup GPU if allowed and available
	use_cuda = False
	if USE_GPU and hasattr(cv2, "cuda"):
		try:
			use_cuda = cv2.cuda.getCudaEnabledDeviceCount() > 0
		except Exception:
			use_cuda = False
	if use_cuda:
		try:
			gpu_screen = cv2.cuda_GpuMat()
			gpu_screen.upload(screen_for_match)
		except Exception:
			use_cuda = False
	for info in templates.values():
		thr = info["threshold"]
		for scale in TEMPLATE_SCALES:
			tpl, msk = get_scaled_template(info, scale)
			th, tw = tpl.shape[:2]
			if th > sh or tw > sw:
				continue
			# Prepare template (with optional edges)
			if USE_EDGE_ENHANCE:
				if tpl.ndim == 3:
					tp_gray = cv2.cvtColor(tpl, cv2.COLOR_BGR2GRAY)
				else:
					tp_gray = tpl
				tp = cv2.Canny(tp_gray, 50, 150)
			else:
				tp = tpl

			# Use GPU when possible (mask not supported in CUDA path)
			if use_cuda and msk is None:
				try:
					gpu_tpl = cv2.cuda_GpuMat()
					gpu_tpl.upload(tp)
					matcher = cv2.cuda.createTemplateMatching(tp.dtype, cv2.TM_CCOEFF_NORMED)
					gpu_res = matcher.match(gpu_screen, gpu_tpl)
					r = gpu_res.download()
				except Exception:
					# Fallback to CPU if GPU path fails
					r = cv2.matchTemplate(screen_for_match, tp, cv2.TM_CCOEFF_NORMED)
			else:
				r = cv2.matchTemplate(screen_for_match, tp, cv2.TM_CCOEFF_NORMED, mask=msk)
			min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(r)
			if max_val > best_scores[info["name"]]:
				best_scores[info["name"]] = float(max_val)
			# Fast-topK: iteratively pick best location, then suppress its neighborhood
			k = 0
			res = r.copy()
			while k < TOPK_PER_TEMPLATE_PER_SCALE:
				min_val2, max_val2, min_loc2, max_loc2 = cv2.minMaxLoc(res)
				if max_val2 < thr:
					break
				x, y = max_loc2
				matches.append((info["name"], float(max_val2), (x, y, tw, th)))
				# suppress neighborhood around (x,y)
				x0 = max(0, x - tw // 3); y0 = max(0, y - th // 3)
				x1 = min(res.shape[1], x + tw // 3); y1 = min(res.shape[0], y + th // 3)
				res[y0:y1, x0:x1] = 0
				k += 1
	return matches, best_scores


def nms_boxes(boxes: List[Tuple[int, int, int, int]], scores: List[float], iou_threshold: float = 0.5) -> List[int]:

	if not boxes:
		return []
	# boxes: (x, y, w, h)
	x1 = np.array([b[0] for b in boxes])
	y1 = np.array([b[1] for b in boxes])
	x2 = x1 + np.array([b[2] for b in boxes])
	y2 = y1 + np.array([b[3] for b in boxes])
	scores_arr = np.array(scores)
	indices = scores_arr.argsort()[::-1]
	keep: List[int] = []
	while indices.size > 0:
		i = int(indices[0])
		keep.append(i)
		if indices.size == 1:
			break
		xx1 = np.maximum(x1[i], x1[indices[1:]])
		yy1 = np.maximum(y1[i], y1[indices[1:]])
		xx2 = np.minimum(x2[i], x2[indices[1:]])
		yy2 = np.minimum(y2[i], y2[indices[1:]])

		w = np.maximum(0, xx2 - xx1)
		h = np.maximum(0, yy2 - yy1)
		inter = w * h
		area_i = (x2[i] - x1[i]) * (y2[i] - y1[i])
		area_rest = (x2[indices[1:]] - x1[indices[1:]]) * (y2[indices[1:]] - y1[indices[1:]])
		iou = inter / (area_i + area_rest - inter + 1e-6)
		indices = indices[1:][iou < iou_threshold]
	return keep


class Toggle:

	def __init__(self) -> None:
		self.running = False
		self.stop = False

	def on_press(self, key) -> None:
		try:
			if key.char == " ":
				self.running = not self.running
		except AttributeError:
			# Special keys
			if key == keyboard.Key.space:
				self.running = not self.running
			elif key == keyboard.Key.esc:
				self.stop = True
				return False


def main() -> None:

	print("Loading templates from current folder (*.png)...")
	templates = load_templates(TEMPLATES_DIR)
	if not templates:
		print("No PNG templates found in the current folder.")
		return
	print(f"Loaded {len(templates)} template(s): {[t['name'] for t in templates.values()]}")
	print("Press Space to start/pause. Press Esc to quit.")

	listener_toggle = Toggle()
	listener = keyboard.Listener(on_press=listener_toggle.on_press)
	listener.start()

	# Prefer DXGI capture when available for speed
	camera = None
	use_dx = False
	if dxcam is not None and USE_DXCAM:
		try:
			camera = dxcam.create()
			camera.start(target_fps=60)
			use_dx = True
		except Exception:
			use_dx = False

	with mss.mss() as sct:
		mon = sct.monitors[0]  # full virtual screen (fallback)
		win_name = "Screen Matcher"
		# Always show a small HUD window for status/debug, even with overlay
		cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
		cv2.resizeWindow(win_name, 420, 160)
		cv2.moveWindow(win_name, 20, 20)
		overlay = None
		if USE_OVERLAY and win32gui is not None:
			overlay = DesktopOverlay()
			overlay.create(mon["width"], mon["height"])  # full desktop size
		while True:
			if listener_toggle.stop:
				break
			if use_dx and camera is not None:
				img = camera.get_latest_frame()
				if img is None:
					continue
				# dxcam returns BGRA
				frame_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
				# If frame is black (e.g., protected/hardware-accelerated window), auto-fallback to MSS
				if np.mean(frame_bgr) < 1.0:
					use_dx = False
					try:
						camera.stop()
					except Exception:
						pass
					img = np.asarray(sct.grab(mon))
					frame_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
			else:
				img = np.asarray(sct.grab(mon))  # BGRA
				frame_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
			if SCREEN_SCALE != 1.0:
				frame_bgr = cv2.resize(frame_bgr, None, fx=SCREEN_SCALE, fy=SCREEN_SCALE, interpolation=cv2.INTER_AREA)

			display = frame_bgr.copy()
			# Optionally mask out our own preview window from detection to avoid mirror hits
			preview_rect = None
			if WINDOW_EXCLUDE and win32gui is not None:
				try:
					hwnd = win32gui.FindWindow(None, win_name)
					if hwnd:
						# rect: (left, top, right, bottom)
						preview_rect = win32gui.GetWindowRect(hwnd)
				except Exception:
					preview_rect = None
			if listener_toggle.running:
				if USE_ORB:
					# ORB path: ignore preview exclusion for simplicity (feature match is robust)
					orb_results, best_scores = orb_match_all(frame_bgr, templates)
					for name, conf, quad in orb_results:
						quad = quad.astype(int)
						color = (0, 200, 255) if conf >= 0.8 else (0, 255, 0) if conf >= 0.6 else (0, 165, 255)
						# Draw polygon on either overlay or preview
						if USE_OVERLAY and overlay is not None:
							canvas = np.zeros((display.shape[0], display.shape[1], 4), dtype=np.uint8)
							cv2.polylines(canvas, [quad], True, (*color, 255), thickness=int(3 * UI_SCALE), lineType=cv2.LINE_AA)
							# Label
							xmin = int(np.min(quad[:, 0])); ymin = int(np.min(quad[:, 1]))
							label = f"{name} {conf*100:.1f}%"
							txt_bg = (0, 0, 0, 140)
							cv2.rectangle(canvas, (xmin, max(0, ymin - int(22 * UI_SCALE))), (xmin + int(240 * UI_SCALE), ymin), txt_bg, -1)
							cv2.putText(canvas, label, (xmin + 4, max(16, ymin - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.7 * UI_SCALE, (*color, 255), int(2 * UI_SCALE), cv2.LINE_AA)
							success = overlay.update(canvas)
							if not success:
								# Auto-disable overlay on error
								globals()["USE_OVERLAY"] = False
								cv2.polylines(display, [quad], isClosed=True, color=color, thickness=int(2 * UI_SCALE))
								cv2.putText(display, label, (xmin, max(14, ymin - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.7 * UI_SCALE, color, int(2 * UI_SCALE), cv2.LINE_AA)
						else:
							cv2.polylines(display, [quad], isClosed=True, color=color, thickness=int(2 * UI_SCALE))
							xmin = int(np.min(quad[:, 0])); xmax = int(np.max(quad[:, 0]))
							ymin = int(np.min(quad[:, 1])); ymax = int(np.max(quad[:, 1]))
							cv2.rectangle(display, (xmin, ymin), (xmax, ymax), color, 1)
							label = f"{name} {conf*100:.1f}%"
							cv2.putText(display, label, (xmin, max(14, ymin - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.7 * UI_SCALE, color, int(2 * UI_SCALE), cv2.LINE_AA)
					status = "RUNNING"
				else:
					# Template path (fallback)
					if preview_rect is not None:
						l, t, r, b = preview_rect
						l = max(0, int(l)); t = max(0, int(t)); r = max(0, int(r)); b = max(0, int(b))
						l = min(l, frame_bgr.shape[1] - 1)
						r = min(r, frame_bgr.shape[1])
						t = min(t, frame_bgr.shape[0] - 1)
						b = min(b, frame_bgr.shape[0])
						cv2.rectangle(display, (l, t), (r, b), (32, 32, 32), 2)
						frame_for_match = frame_bgr.copy()
						cv2.rectangle(frame_for_match, (l, t), (r, b), (0, 0, 0), -1)
						all_matches, best_scores = match_all_multiscale(frame_for_match, templates)
					else:
						all_matches, best_scores = match_all_multiscale(frame_bgr, templates)
					boxes = [m[2] for m in all_matches]
					scores = [m[1] for m in all_matches]
					keep_idx = nms_boxes(boxes, scores, iou_threshold=0.3)
					for i in keep_idx:
						name, conf, (x, y, w, h) = all_matches[i]
						color = (0, 200, 255) if conf >= 0.8 else (0, 255, 0) if conf >= 0.7 else (0, 165, 255)
						cv2.rectangle(display, (x, y), (x + w, y + h), color, 2)
						label = f"{name} {conf*100:.1f}%"
						cv2.putText(display, label, (x, max(14, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.7 * UI_SCALE, color, int(2 * UI_SCALE), cv2.LINE_AA)
					status = "RUNNING"
			else:
				status = "PAUSED"

			# If overlay is active, show compact HUD; otherwise show the full preview with boxes
			if USE_OVERLAY and overlay is not None:
				hud = np.zeros((160, 420, 3), dtype=np.uint8)
				cv2.putText(hud, f"{status} - Space: toggle, Esc: quit", (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
				if listener_toggle.running and 'best_scores' in locals():
					y0 = 50
					for idx, info in enumerate(templates.values()):
						name = info["name"]
						best = best_scores.get(name, 0.0)
						cv2.putText(hud, f"{name}: {best:.0f}", (10, y0 + idx * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 255, 180), 1, cv2.LINE_AA)
				cv2.imshow(win_name, hud)
			else:
				cv2.putText(display, f"{status} - Space: toggle, Esc: quit", (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
				cv2.imshow(win_name, display)

			key = cv2.waitKey(1) & 0xFF
			if key == 27:  # Esc
				break
			time.sleep(COOLDOWN_SECONDS)

	if not USE_OVERLAY:
		cv2.destroyAllWindows()
	listener.stop()
	if use_dx and camera is not None:
		try:
			camera.stop()
		except Exception:
			pass


if __name__ == "__main__":
	main()


