# ✅ Gunakan base image yang lebih stabil (non-slim)
FROM python:3.10

# 📦 1. Install dependensi sistem
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    graphviz \
    curl \
    apt-utils \
    && rm -rf /var/lib/apt/lists/*

# 📁 2. Set direktori kerja
WORKDIR /app

# 📜 3. Salin dan install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 📂 4. Salin semua file aplikasi
COPY main.py .
COPY main_mr.py .
COPY .env .

COPY modules/ /app/modules/
COPY static/ /app/static/
COPY saved/ /app/saved/
COPY data/ /app/data/

# ✅ 5. Pastikan modules punya file __init__.py agar bisa di-import
RUN touch /app/modules/__init__.py

# 📁 6. Tambah folder penyimpanan jika belum ada
RUN mkdir -p /app/integrasi

# 🔐 7. Tambahkan ENV variable
ENV DATA_FOLDER=/app/saved
ENV INTEGRASI_FOLDER=/app/integrasi

# 🚀 8. Jalankan Streamlit
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]

# 🌐 9. Buka port 8501
EXPOSE 8501
