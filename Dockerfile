FROM rocm/pytorch:latest

COPY requirements.txt ./
RUN pip install -r requirements.txt

RUN CMAKE_ARGS="-D WITH_FFMPEG=ON" pip install --force-reinstall --no-binary opencv-python-headless --no-deps opencv-python-headless==4.12.0.88
