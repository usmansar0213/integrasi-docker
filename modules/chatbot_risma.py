import os
import json
import streamlit as st
from PIL import Image
import pandas as pd
import openai

# Fungsi untuk menampilkan judul dan logo
def display_title():
    logo_path = os.path.join("static", "via_icon.jpg")

    if os.path.exists(logo_path):
        logo = Image.open(logo_path)
    else:
        st.warning("Logo tidak ditemukan di folder static/")
        return

    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown(
            '<div style="display: flex; justify-content: center; align-items: center; height: 100%; margin-top: 40px;">',
            unsafe_allow_html=True
        )
        st.image(logo, width=150)
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(
            '<div style="display: flex; flex-direction: column; justify-content: center;">',
            unsafe_allow_html=True
        )
        st.markdown("<h1 style='font-size: 40px; font-weight: bold; color: inherit;'>Chat Bot RISMA</h1>", unsafe_allow_html=True)
        st.markdown("""
            <p style='font-size: 18px; color: #666;'>RISMA adalah asisten virtual pintar yang dirancang untuk menjawab pertanyaan seputar tema Pelindo dan tema umum. 
            Membantu Anda dalam berbagai analisis risiko dan pengambilan keputusan berbasis data. Dengan menggunakan teknologi 
            terkini seperti simulasi Monte Carlo dan analisis regresi linear, VIA akan memberikan solusi yang dapat diandalkan 
            untuk kebutuhan bisnis Anda.</p>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# Fungsi untuk menghitung bobot berdasarkan kata kunci
def calculate_weight(teks, kata_kunci, jenis_kolom):
    teks_split = teks.lower().split()
    kata_kunci_split = kata_kunci.lower().split()
    match_count = sum(1 for suku in kata_kunci_split if suku in teks_split)
    return match_count * {"title": 50, "subtitle": 40, "text": 30}.get(jenis_kolom, 0)

# Fungsi untuk mencari data berdasarkan query
def search_data(data, query):
    IGNORED_WORDS = ["apa", "bagaimana", "siapa", "mengapa", "jelaskan", "jabarkan", "tunjukan", "kenapa", "dimana"]
    keywords = [word for word in query.lower().split() if word not in IGNORED_WORDS]
    phrase = ' '.join(keywords)
    results = [
        {"item": item, "score": calculate_weight(item.get('Title', ''), phrase, 'title') +
                              calculate_weight(item.get('Subtitle', ''), phrase, 'subtitle') +
                              calculate_weight(item.get('Text', ''), phrase, 'text')}
        for item in data
    ]
    results = [result for result in results if result["score"] > 0]
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:2]

# Fungsi untuk mengambil data dari Excel
def load_data_from_excel(excel_path):
    df = pd.read_excel(excel_path, engine='openpyxl')
    df = df.fillna('')
    return df.to_dict(orient='records')

# Fungsi untuk mendapatkan respons dari GPT
def get_gpt_response(query, is_keyword_search=False):
    try:
        prompt = f"""
        Berikan penjelasan dengan format bisnis, fokus pada esensi dari informasi dan elaborasi angka angka, nama tempat dan peristiwa dari informasi berikut:
        {query}
        """ if not is_keyword_search else f"""
        Jelaskan secara esensial tentang kata kunci berikut:
        Kata Kunci: {query}
        """
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error: {str(e)}"

def tampilkan_rangkuman_gpt(gpt_response: str):
    st.subheader("📄 Rangkuman GPT:")
    st.write(gpt_response)
    st.download_button(
        label="📥 Unduh Rangkuman",
        data=gpt_response.encode("utf-8"),
        file_name="rangkuman_gpt.txt",
        mime="text/plain"
    )

def main():
    openai.api_key = st.secrets["openai_api_key"]

    display_title()
    query = st.text_input("Masukkan pertanyaan atau kata kunci:")

    excel_path = os.path.join("saved", "Laporan_Tahunan_2023_Normalized.xlsx")
    if os.path.exists(excel_path):
        df = pd.read_excel(excel_path)
        st.success("✅ File berhasil dimuat.")
    else:
        st.error(f"❌ File Excel tidak ditemukan di: `{excel_path}`")

    if st.button("Cari"):
        if os.path.exists(excel_path):
            data = load_data_from_excel(excel_path)
            results = search_data(data, query)
            if results:
                structured_results = json.dumps([r["item"] for r in results])
                gpt_response = get_gpt_response(structured_results)
                tampilkan_rangkuman_gpt(gpt_response)
            else:
                gpt_response = get_gpt_response(query, is_keyword_search=True)
                st.subheader("Rangkuman GPT:")
                st.write(gpt_response)
        else:
            st.error(f"File Excel tidak ditemukan di {excel_path}")

if __name__ == "__main__":
    main()
