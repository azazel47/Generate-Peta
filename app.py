import streamlit as st
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import contextily as ctx
import numpy as np
from PIL import Image
import io

st.set_page_config(page_title="Peta Rekomendasi KKPRL", layout="wide")
st.title("🗺️ Generator Peta KKPRL (Layout Resmi)")

# === Fungsi: Skala Bar Otomatis ===
def add_scalebar(ax, length=None, location=(0.1, 0.05), linewidth=3):
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()

    if length is None:
        x_range = xmax - xmin
        approx_len = x_range / 5
        pow10 = 10 ** int(np.log10(approx_len))
        length = int(round(approx_len / pow10) * pow10)

    x0 = xmin + (xmax - xmin) * location[0]
    y0 = ymin + (ymax - ymin) * location[1]

    ax.plot([x0, x0 + length], [y0, y0],
            color="black", linewidth=linewidth, transform=ax.transData)
    ax.text(x0, y0 - (ymax - ymin) * 0.02, "0 m",
            ha="center", va="top", fontsize=8, transform=ax.transData)
    ax.text(x0 + length, y0 - (ymax - ymin) * 0.02,
            f"{length/1000:.1f} km",
            ha="center", va="top", fontsize=8, transform=ax.transData)

# === Fungsi: Grid Koordinat ===
def add_grid(ax):
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    xticks = np.linspace(xmin, xmax, 5)
    yticks = np.linspace(ymin, ymax, 5)
    ax.set_xticks(xticks)
    ax.set_yticks(yticks)
    ax.tick_params(axis="both", which="both", length=0, labelsize=6)
    ax.grid(True, color="gray", linestyle="--", linewidth=0.5, alpha=0.7)

# Upload file SHP/GeoJSON
uploaded_file = st.file_uploader("📂 Upload file SHP (ZIP/GeoJSON)", type=["zip", "json", "geojson"])

if uploaded_file is not None:
    try:
        gdf = gpd.read_file(uploaded_file)
        if gdf.crs is None:
            gdf = gdf.set_crs("EPSG:4326")
        gdf = gdf.to_crs(epsg=3857)

        # Layout figure A4 landscape
        fig = plt.figure(figsize=(11.7, 8.3))
        ax_main = fig.add_axes([0.05, 0.25, 0.65, 0.65])  

        gdf.plot(ax=ax_main, alpha=0.6, edgecolor="black", cmap="Set2")
        ctx.add_basemap(ax_main, crs=gdf.crs, source=ctx.providers.Esri.WorldImagery)
        ax_main.set_axis_off()

        # Grid + scalebar
        add_grid(ax_main)
        add_scalebar(ax_main)

        # === Judul Utama ===
        fig.text(0.5, 0.93,
                 "REKOMENDASI PERSUTUJUAN\nKESESUAIAN KEGIATAN PEMANFAATAN RUANG LAUT",
                 ha="center", va="center", fontsize=14, weight="bold")

        # === Legenda ===
        legend_ax = fig.add_axes([0.75, 0.25, 0.2, 0.4])
        legend_ax.axis("off")
        legend_items = [
            mpatches.Patch(color="green", label="Rekomendasi KKPRL"),
            mpatches.Patch(color="orange", label="Area Pemanfaatan Lain"),
            mpatches.Patch(color="black", label="Rencana Terminal Khusus"),
        ]
        legend_ax.legend(handles=legend_items, loc="upper left", fontsize=8)

        # === Inset Peta Indonesia ===
        world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
        indonesia = world[world["name"] == "Indonesia"].to_crs(epsg=3857)
        inset_ax = fig.add_axes([0.75, 0.7, 0.2, 0.2])
        indonesia.plot(ax=inset_ax, color="lightgrey")
        gdf.plot(ax=inset_ax, color="red", markersize=5)
        inset_ax.set_axis_off()

        # === Logo Instansi ===
        try:
            logo = Image.open("logo.png")  # logo instansi di folder sama
            fig.figimage(logo, xo=60, yo=650, alpha=1, zorder=10)
        except:
            pass

        # === Footer Info ===
        fig.text(0.05, 0.05,
                 "Sumber Data: Kementerian Kelautan dan Perikanan\nSistem Informasi KKPRL",
                 ha="left", va="bottom", fontsize=7)

        # === Bingkai Hitam (border) ===
        border = mpatches.Rectangle((0, 0), 1, 1,
                                    transform=fig.transFigure,
                                    fill=False, color="black", linewidth=2)
        fig.patches.append(border)

        # Simpan ke PNG
        buf_png = io.BytesIO()
        fig.savefig(buf_png, format="png", dpi=300, bbox_inches="tight")
        buf_png.seek(0)

        # Konversi ke JPG
        img = Image.open(buf_png).convert("RGB")
        buf_jpg = io.BytesIO()
        img.save(buf_jpg, format="JPEG", quality=95)
        buf_jpg.seek(0)

        # Tombol download
        st.download_button(
            "📥 Download Peta Layout JPG",
            data=buf_jpg,
            file_name="peta_rekomendasi.jpg",
            mime="image/jpeg"
        )

        plt.close(fig)
        st.success("✅ Peta layout final dengan bingkai berhasil dibuat.")

    except Exception as e:
        st.error(f"Gagal memproses file: {e}")
