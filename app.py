import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import zipfile
import io
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.title("📌 Aplikasi Overlay Tata Ruang")

# Session state to store shapefile and selected attribute
if "gdf_tataruang" not in st.session_state:
    st.session_state.gdf_tataruang = None
if "atribut_tataruang" not in st.session_state:
    st.session_state.atribut_tataruang = None

# === Step 1: Upload Shapefile Tata Ruang ===
st.sidebar.header("1. Upload Shapefile Tata Ruang")
shp_file = st.sidebar.file_uploader("Upload file .zip berisi SHP", type="zip")

if shp_file:
    with zipfile.ZipFile(shp_file, 'r') as zip_ref:
        zip_ref.extractall("temp_shp")
    try:
        gdf = gpd.read_file("temp_shp")
        st.session_state.gdf_tataruang = gdf
        st.sidebar.success("Shapefile berhasil dimuat!")
        # Pilih atribut
        atribut = st.sidebar.selectbox("Pilih atribut untuk overlay:", gdf.columns)
        st.session_state.atribut_tataruang = atribut
    except Exception as e:
        st.sidebar.error(f"Gagal memuat shapefile: {e}")

# === Step 2: Upload Excel Koordinat ===
st.sidebar.header("2. Upload Excel Koordinat")
excel_file = st.sidebar.file_uploader("Upload Excel berisi id, bujur, lintang", type=["xlsx"])

if excel_file and st.session_state.gdf_tataruang is not None:
    try:
        df_excel = pd.read_excel(excel_file)
        if not set(["id", "bujur", "lintang"]).issubset(df_excel.columns):
            st.error("Kolom wajib: id, bujur, lintang tidak ditemukan.")
        else:
            # Buat GeoDataFrame dari titik koordinat
            geometry = [Point(xy) for xy in zip(df_excel.bujur, df_excel.lintang)]
            gdf_excel = gpd.GeoDataFrame(df_excel, geometry=geometry, crs="EPSG:4326")

            # Pastikan CRS sama
            gdf_tataruang = st.session_state.gdf_tataruang.to_crs("EPSG:4326")

            # Lakukan spatial join
            join_result = gpd.sjoin(gdf_excel, gdf_tataruang, how="left", predicate="within")
            hasil = join_result[["id", "bujur", "lintang", st.session_state.atribut_tataruang]]

            st.subheader("🗺️ Peta Overlay")
            m = folium.Map(location=[df_excel.lintang.mean(), df_excel.bujur.mean()], zoom_start=10)
            folium.GeoJson(gdf_tataruang).add_to(m)
            for _, row in hasil.iterrows():
                popup = f"ID: {row['id']}<br>{st.session_state.atribut_tataruang}: {row[st.session_state.atribut_tataruang]}"
                folium.Marker([row["lintang"], row["bujur"]], popup=popup).add_to(m)

            st_data = st_folium(m, width=900, height=500)

            st.subheader("📄 Hasil Overlay")
            st.dataframe(hasil)

            # Unduh hasil
            csv = hasil.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Unduh Hasil CSV", csv, "hasil_overlay.csv", "text/csv")

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses: {e}")

elif excel_file:
    st.warning("Silakan upload shapefile tata ruang terlebih dahulu.")
