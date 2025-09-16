import streamlit as st
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import contextily as ctx
import tempfile
import zipfile
import os
import io
from shapely.geometry import Polygon, LineString

st.set_page_config(layout="centered")

st.title("📌 Generator Peta KKPRL")

# === Upload SHP ===
uploaded_file = st.file_uploader("Upload file SHP (zip)", type=["zip"])

if uploaded_file is not None:
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "data.zip")
        with open(zip_path, "wb") as f:
            f.write(uploaded_file.read())
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(tmpdir)

        # Cari file shp
        shp_files = [f for f in os.listdir(tmpdir) if f.endswith(".shp")]
        if len(shp_files) > 0:
            shp_path = os.path.join(tmpdir, shp_files[0])
            gdf_rekom = gpd.read_file(shp_path).to_crs(3857)
        else:
            st.error("❌ File SHP tidak ditemukan dalam ZIP")
            st.stop()
else:
    st.info("⬆️ Silakan upload file SHP (format ZIP)")
    st.stop()

# Dummy layer tambahan (Terminal & Area lain) – bisa diganti jika ada data asli
line_terminal = LineString([(108.787, -3.074), (108.791, -3.0755)])
poly_area = Polygon([
    (108.785, -3.072),
    (108.7865, -3.072),
    (108.7865, -3.070),
    (108.785, -3.070)
])

gdf_terminal = gpd.GeoDataFrame({"label":["Terminal"]}, geometry=[line_terminal], crs="EPSG:4326").to_crs(3857)
gdf_area = gpd.GeoDataFrame({"label":["Area Lain"]}, geometry=[poly_area], crs="EPSG:4326").to_crs(3857)

# === Render Peta Final ===
fig = plt.figure(figsize=(11.7, 8.3))  # A4 Landscape
gs = fig.add_gridspec(1, 2, width_ratios=[3,1])

# Peta utama
ax = fig.add_subplot(gs[0,0])
gdf_rekom.plot(ax=ax, color="green", alpha=0.4, edgecolor="black", linewidth=1)
gdf_terminal.plot(ax=ax, color="black", linewidth=2)
gdf_area.plot(ax=ax, color="orange", alpha=0.5, edgecolor="black")

ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery)
ax.set_axis_off()
ax.set_title("LAMPIRAN BERITA ACARA HASIL PENILAIAN TEKNIS\n"
             "KESESUAIAN KEGIATAN PEMANFAATAN RUANG LAUT", 
             fontsize=12, fontweight="bold", loc="center", pad=10)

# Panel kanan
ax_leg = fig.add_subplot(gs[0,1])
ax_leg.axis("off")

ax_leg.text(0.5, 0.95, "KEMENTERIAN KELAUTAN DAN PERIKANAN\nREPUBLIK INDONESIA", 
            fontsize=10, ha="center", va="top", fontweight="bold")

ax_leg.text(0.5, 0.85, "PETA REKOMENDASI PERSETUJUAN\n"
                       "KESESUAIAN KEGIATAN PEMANFAATAN RUANG LAUT (PERSETUJUAN)\n\n"
                       "TERMINAL KHUSUS PENUNJANG\n"
                       "PERTAMBANGAN PASIR KUARSA DAN TANAH LIAT\n"
                       "PT HERO PROGRES INTERNATIONAL\n\n"
                       "Kabupaten Belitung Timur, Provinsi Kepulauan Bangka Belitung", 
            fontsize=8, ha="center", va="top")

legend_patches = [
    mpatches.Patch(color="green", alpha=0.4, label="Rekomendasi KKPRL"),
    mpatches.Patch(color="orange", alpha=0.5, label="Area Pemanfaatan Lain"),
    mpatches.Patch(color="black", alpha=1, label="Terminal Khusus")
]
ax_leg.legend(handles=legend_patches, loc="upper center", fontsize=7, frameon=False)

ax_leg.text(0, 0.25, "SUMBER:\n"
                     "1. Penilaian Teknis Permohonan KKPRL Tanggal 26 Februari 2025\n"
                     "2. Perbaikan Dokumen Permohonan KKPRL Tanggal 3 Maret 2025\n"
                     "3. Peraturan Daerah Provinsi Bangka Belitung Nomor 3 Tahun 2020\n"
                     "4. Rencana Zonasi Wilayah Pesisir dan Pulau-Pulau Kecil\n"
                     "   Provinsi Kepulauan Bangka Belitung Tahun 2020-2040", 
            fontsize=6.5, ha="left")

ax_leg.text(0, 0.05, "CATATAN:\nPeta ini bukan merupakan acuan/referensi resmi mengenai nama-nama\n"
                     "dan batas-batas administrasi nasional maupun internasional.", fontsize=6.5)

# Skala grafis
ax_leg.hlines(y=0.6, xmin=0.1, xmax=0.5, colors="black")
ax_leg.vlines(x=[0.1,0.3,0.5], ymin=0.59, ymax=0.61, colors="black")
ax_leg.text(0.1,0.62,"0 km", fontsize=6, ha="center")
ax_leg.text(0.3,0.62,"1 km", fontsize=6, ha="center")
ax_leg.text(0.5,0.62,"2 km", fontsize=6, ha="center")

plt.tight_layout()

# === Export ke JPG ===
buf = io.BytesIO()
fig.savefig(buf, format="jpg", dpi=300, bbox_inches="tight")
st.download_button("📥 Download Peta (JPG)", data=buf.getvalue(),
                   file_name="peta_kkprl.jpg", mime="image/jpeg")
