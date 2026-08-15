# RFdiffusion, built for Blackwell (RTX 5090, sm_120) GPUs.
#
# Adapted from JMB-Scripts/RFdiffusion-dockerfile-nvidia-RTX5090, with one change:
# line 40 originally pointed at PyTorch's nightly cu128 index, which pulled in a
# torchvision/torch version pair that didn't resolve. Switched to the stable cu128
# index instead — verified working on this hardware (see README.md / raw notes).
#
# DGL has no official Blackwell/CUDA-12.8 support as of when this was built, so
# it's compiled from source here rather than installed via pip.
#
# Built and tested on an RTX 5090 (32GB VRAM). Build takes ~25 minutes.
#-----------------------------------------------------------------------
# STAGE 1: THE "BUILDER"
#-----------------------------------------------------------------------
FROM ubuntu:22.04 AS builder
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get -q update && \
    apt-get install -y --no-install-recommends \
        git wget curl ca-certificates gnupg \
        build-essential ninja-build g++-11 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV CMAKE_VERSION=3.29.3
RUN wget https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION}/cmake-${CMAKE_VERSION}-linux-x86_64.tar.gz && \
    tar -xzf cmake-${CMAKE_VERSION}-linux-x86_64.tar.gz --strip-components=1 -C /usr/local && \
    rm cmake-${CMAKE_VERSION}-linux-x86_64.tar.gz

RUN wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb && \
    dpkg -i cuda-keyring_1.1-1_all.deb && \
    apt-get -q update && \
    apt-get -y install cuda-toolkit-12-8 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm cuda-keyring_1.1-1_all.deb

ENV PATH="/usr/local/cuda-12.8/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/cuda-12.8/lib64"
ENV CUDA_HOME="/usr/local/cuda-12.8"
ENV CUDA_TOOLKIT_ROOT_DIR="/usr/local/cuda-12.8"

ENV CONDA_DIR=/opt/conda
RUN wget --quiet "https://github.com/conda-forge/miniforge/releases/download/24.3.0-0/Mambaforge-24.3.0-0-Linux-x86_64.sh" -O ~/mambaforge.sh && \
    /bin/bash ~/mambaforge.sh -b -p /opt/conda && \
    rm ~/mambaforge.sh
ENV PATH=$CONDA_DIR/bin:$PATH

RUN mamba create -n rfdiffusion python=3.11 -y
SHELL ["conda", "run", "-n", "rfdiffusion", "/bin/bash", "-c"]

RUN pip install -U --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

WORKDIR /tmp
RUN git clone --recursive https://github.com/dmlc/dgl.git && \
    cd dgl && \
    mkdir build && \
    cd build && \
    cmake -D USE_CUDA=ON -D CUDA_TOOLKIT_ROOT_DIR=/usr/local/cuda-12.8 .. && \
    make -j20 && \
    cd ../python && \
    pip install .

RUN pip install --no-cache-dir \
    hydra-core==1.3.2 pyrsistent>=0.19.3 pandas pydantic>=2.0 \
    wandb pynvml torchdata e3nn decorator gitpython
RUN pip install --no-cache-dir git+https://github.com/NVIDIA/dllogger.git

WORKDIR /app/RFdiffusion
COPY . .
RUN cd env/SE3Transformer && \
    pip install -r requirements.txt && \
    python setup.py install && \
    cd /app/RFdiffusion && \
    pip install -e .

# e3nn ships a torch.load() call that breaks under newer PyTorch's default
# weights_only=True. Patched directly rather than pinning an older e3nn.
RUN sed -i "s/torch.load(os.path.join(os.path.dirname(__file__), 'constants.pt'))/torch.load(os.path.join(os.path.dirname(__file__), 'constants.pt'), weights_only=False)/" /opt/conda/envs/rfdiffusion/lib/python3.11/site-packages/e3nn/o3/_wigner.py

RUN pip install --no-cache-dir "numpy<2"

#-----------------------------------------------------------------------
# STAGE 2: THE FINAL IMAGE
#-----------------------------------------------------------------------
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get -q update && \
    apt-get install -y --no-install-recommends curl ca-certificates gnupg wget && \
    wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb && \
    dpkg -i cuda-keyring_1.1-1_all.deb && \
    apt-get -q update && \
    apt-get -y install cuda-compat-12-8 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm cuda-keyring_1.1-1_all.deb

ENV CONDA_DIR=/opt/conda
COPY --from=builder /opt/conda /opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH

WORKDIR /app/RFdiffusion
COPY --from=builder /app/RFdiffusion .

ENV DGLBACKEND="pytorch"
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["conda", "run", "-n", "rfdiffusion"]
CMD ["python", "scripts/run_inference.py"]
