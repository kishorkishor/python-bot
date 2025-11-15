# GPU Acceleration for Detection

## Current Status
- Detection runs on **CPU** (slow)
- Uses `cv2.matchTemplate()` which is CPU-only
- Sequential processing (one template at a time)

## GPU Options

### Option 1: OpenCV CUDA (NVIDIA GPUs)
- Requires: `opencv-contrib-python` with CUDA support
- Fastest option if you have NVIDIA GPU
- 5-10x speedup

### Option 2: OpenCV OpenCL (AMD/Intel/NVIDIA)
- Built into OpenCV
- Works on most GPUs
- 2-5x speedup

### Option 3: Parallel CPU Processing
- Use multiprocessing to scan multiple templates at once
- Works on any system
- 2-4x speedup (depends on CPU cores)

## Recommendation
Start with **Option 3** (parallel CPU) - works immediately, no setup needed.
Then try **Option 2** (OpenCL) - usually works out of the box.


