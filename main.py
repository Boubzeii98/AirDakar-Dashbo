import sys
import os

# ============================================================
# CHEMINS - chemins relatifs pour GitHub Actions
# ============================================================
DOSSIER_TRAVAIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "files")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
import pandas as pd
import geopandas as gpd
import folium
import json
import math
import base64
from datetime import datetime
from dashboard_html import generer_dashboard

# ============================================================
# CONFIG
# ============================================================

API_KEY     = "cfb71a7180f965f61b7f40e94abe1544d8b303c79995470917122e1060cb3656"
HEADERS     = {"X-API-Key": API_KEY}
OUTPUT_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
RAYON_M     = 200

CHEMIN_SHP_COMMUNES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "Dakar_communes.shp")

STATIONS_IDS = [
    1531944, 3315287, 3400976, 3431595, 3439881,
    6096080, 6133773, 6133848, 6167229, 6167230,
    6167231, 6167232, 6192633, 6196278, 5261049, 6134928,
]

communes_data_global = {}

# ============================================================
# CHARGEMENT FICHIERS BASE64
# ============================================================

def charger_b64(chemin):
    try:
        with open(chemin, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print("[WARN] Fichier non trouve : " + chemin + " - " + str(e))
        return None

logo_b64     = charger_b64(os.path.join(DOSSIER_TRAVAIL, "Air_Dakar.png"))
monument_b64 = charger_b64(os.path.join(DOSSIER_TRAVAIL, "Monument.jpg"))

print("[INFO] Logo     : " + ("OK" if logo_b64 else "non trouve"))
print("[INFO] Monument : " + ("OK" if monument_b64 else "non trouve"))

# ============================================================
# CHARGEMENT SHAPEFILE COMMUNES
# ============================================================

def charger_shapefile_communes(chemin):
    try:
        gdf = gpd.read_file(chemin)
        if gdf.crs and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)
        print("[INFO] Shapefile communes charge : " + str(len(gdf)) + " entites")
        print("[INFO] Colonnes disponibles      : " + str(list(gdf.columns)))
        return gdf
    except Exception as e:
        print("[ERR ] Impossible de charger le shapefile : " + str(e))
        return None


def filtrer_dakar_gdf(gdf):
    if gdf is None:
        return None
    bounds = gdf.geometry.bounds
    masque = (
        (bounds["miny"] < 15.0) &
        (bounds["maxy"] > 14.5) &
        (bounds["minx"] < -16.8) &
        (bounds["maxx"] > -17.7)
    )
    result = gdf[masque].copy().reset_index(drop=True)
    print("[INFO] Communes apres filtre Dakar : " + str(len(result)))
    return result


gdf_communes = filtrer_dakar_gdf(charger_shapefile_communes(CHEMIN_SHP_COMMUNES))

CHAMP_NOM_COMMUNE = None
if gdf_communes is not None:
    for candidat in ["NAME_3", "NAME_2", "shapeName", "nom", "name", "NAME", "ADM3_FR", "ADM3_EN", "commune", "COMMUNE", "GID_3"]:
        if candidat in gdf_communes.columns:
            CHAMP_NOM_COMMUNE = candidat
            break
    if CHAMP_NOM_COMMUNE is None:
        cols = [c for c in gdf_communes.columns if c != "geometry"]
        CHAMP_NOM_COMMUNE = cols[0] if cols else "id"
    print("[INFO] Champ nom utilise : " + str(CHAMP_NOM_COMMUNE))

# ============================================================
# COLLECTE DONNEES API
# ============================================================

def collecter_donnees():
    toutes_mesures = []
    for station_id in STATIONS_IDS:
        print("[INFO] Station " + str(station_id) + "...", end=" ")
        r = requests.get(
            "https://api.openaq.org/v3/locations/" + str(station_id),
            headers=HEADERS
        )
        if r.status_code != 200:
            print("erreur station")
            continue
        data = r.json()
        if "results" not in data or not data["results"]:
            print("aucun resultat")
            continue
        station     = data["results"][0]
        nom_station = station["name"]
        latitude    = station["coordinates"]["latitude"]
        longitude   = station["coordinates"]["longitude"]
        sensor_pm25 = None
        for s in station.get("sensors", []):
            pn = s.get("parameter", {}).get("name", "").lower()
            sn = s.get("name", "").lower()
            if "pm25" in pn or "pm2.5" in pn or "pm25" in sn or "pm2.5" in sn:
                sensor_pm25 = s["id"]
                break
        if sensor_pm25 is None:
            print("pas de PM2.5")
            continue
        r_m = requests.get(
            "https://api.openaq.org/v3/sensors/" + str(sensor_pm25) + "/measurements?limit=100",
            headers=HEADERS
        )
        if r_m.status_code != 200:
            print("erreur mesures")
            continue
        data_m = r_m.json()
        if "results" not in data_m:
            print("aucune mesure")
            continue
        nb = 0
        for m in data_m["results"]:
            try:
                toutes_mesures.append({
                    "Station"  : nom_station,
                    "Latitude" : latitude,
                    "Longitude": longitude,
                    "PM25"     : m["value"],
                    "Date"     : m["period"]["datetimeFrom"]["utc"]
                })
                nb += 1
            except Exception:
                pass
        print(str(nb) + " mesures")
    return toutes_mesures

# ============================================================
# UTILITAIRES
# ============================================================

def couleur_pm25(v):
    if v <= 5:
        return "#00e676"
    if v <= 15:
        return "#ff9800"
    return "#f44336"


def label_pm25(v):
    if v <= 5:
        return "Bon"
    if v <= 15:
        return "Modere"
    return "Mauvais"


def distance_km(lat1, lon1, lat2, lon2):
    R    = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a    = (math.sin(dlat / 2) ** 2 +
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))

# ============================================================
# CONSTRUCTION CARTE
# ============================================================

def construire_carte_html(df):
    global communes_data_global

    centre_lat = df["Latitude"].mean()
    centre_lon = df["Longitude"].mean()
    derniere   = df.sort_values("Date").groupby("Station").tail(1).reset_index(drop=True)

    m = folium.Map(location=[centre_lat, centre_lon], zoom_start=12, tiles=None)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False, control=True
    ).add_to(m)
    folium.TileLayer(tiles="CartoDB positron", name="Clair", overlay=False, control=True).add_to(m)
    folium.TileLayer(tiles="OpenStreetMap", name="OpenStreetMap", overlay=False, control=True).add_to(m)

    tt = ("background-color:#0f0f19;color:white;font-family:'Segoe UI',Arial;"
          "font-size:13px;padding:8px 12px;border-radius:8px;border:none;")

    communes_data = {}
    id_fg_contours = ""
    id_fg_qualite  = ""
    id_fg_labels   = ""

    if gdf_communes is not None and not gdf_communes.empty:
        gdf_enrichi = gdf_communes.copy()
        gdf_enrichi["pm25"]        = None
        gdf_enrichi["qualite"]     = "Inconnu"
        gdf_enrichi["couleur"]     = "#888888"
        gdf_enrichi["station_ref"] = ""

        for idx, row in gdf_enrichi.iterrows():
            clat = row.geometry.centroid.y
            clon = row.geometry.centroid.x
            best, best_d = None, float("inf")
            for _, st in derniere.iterrows():
                d = distance_km(clat, clon, float(st["Latitude"]), float(st["Longitude"]))
                if d < best_d:
                    best_d = d
                    best   = st
            nom = str(row.get(CHAMP_NOM_COMMUNE, ""))
            if best is not None:
                pm  = round(float(best["PM25"]), 1)
                c   = couleur_pm25(pm)
                ql  = label_pm25(pm)
                gdf_enrichi.at[idx, "pm25"]        = pm
                gdf_enrichi.at[idx, "qualite"]     = ql
                gdf_enrichi.at[idx, "couleur"]     = c
                gdf_enrichi.at[idx, "station_ref"] = best["Station"]
                bb = row.geometry.bounds
                if isinstance(bb, tuple):
                    minx, miny, maxx, maxy = bb
                else:
                    minx, miny, maxx, maxy = bb.minx, bb.miny, bb.maxx, bb.maxy
                communes_data[nom] = {
                    "lat_min": miny, "lat_max": maxy,
                    "lon_min": minx, "lon_max": maxx,
                    "pm25"   : pm, "couleur": c,
                    "station": best["Station"], "qualite": ql
                }

        geojson_enrichi = json.loads(gdf_enrichi.to_json())

        fg_contours = folium.FeatureGroup(name="Communes \u2014 contours", show=True)
        folium.GeoJson(
            geojson_enrichi,
            style_function=lambda f: {
                "color": "#00bcd4", "weight": 2, "opacity": 0.9,
                "fillOpacity": 0.0, "dashArray": "5 4"
            },
            tooltip=folium.GeoJsonTooltip(
                fields=[CHAMP_NOM_COMMUNE, "pm25", "qualite", "station_ref"],
                aliases=["Commune :", "PM2.5 (µg/m³) :", "Qualite :", "Station ref. :"],
                style=tt
            )
        ).add_to(fg_contours)
        fg_contours.add_to(m)
        id_fg_contours = fg_contours.get_name()

        fg_qualite = folium.FeatureGroup(name="Communes \u2014 qualite PM2.5", show=True)
        folium.GeoJson(
            geojson_enrichi,
            style_function=lambda f: {
                "fillColor"  : f["properties"].get("couleur", "#888"),
                "color"      : f["properties"].get("couleur", "#888"),
                "weight"     : 1.5,
                "fillOpacity": 0.45,
                "opacity"    : 0.8
            },
            tooltip=folium.GeoJsonTooltip(
                fields=[CHAMP_NOM_COMMUNE, "pm25", "qualite", "station_ref"],
                aliases=["Commune :", "PM2.5 (µg/m³) :", "Qualite :", "Station ref. :"],
                style=tt
            )
        ).add_to(fg_qualite)
        fg_qualite.add_to(m)
        id_fg_qualite = fg_qualite.get_name()

        fg_labels = folium.FeatureGroup(name="Communes \u2014 labels", show=True)
        for _, row in gdf_enrichi.iterrows():
            clat = row.geometry.centroid.y
            clon = row.geometry.centroid.x
            nom  = str(row.get(CHAMP_NOM_COMMUNE, ""))
            pm   = row["pm25"]
            c    = row["couleur"]
            pm_txt = (
                "<br><span style='font-size:9px;color:" + c + ";font-weight:700;'>"
                + str(pm) + " µg/m³</span>"
            ) if pm is not None else ""
            folium.Marker(
                location=[clat, clon],
                icon=folium.DivIcon(
                    icon_size=(130, 40), icon_anchor=(65, 20),
                    html=(
                        "<div style=\"font-family:'Segoe UI',Arial;font-size:10px;font-weight:600;"
                        "color:white;text-shadow:0 0 4px #000,0 0 4px #000,0 0 4px #000;"
                        "text-align:center;pointer-events:none;line-height:1.4;\">"
                        + nom + pm_txt + "</div>"
                    )
                )
            ).add_to(fg_labels)
        fg_labels.add_to(m)
        id_fg_labels = fg_labels.get_name()
        print("[ OK ] Communes rendues : " + str(len(gdf_enrichi)))

    communes_data_global = communes_data

    for _, row in derniere.iterrows():
        c        = couleur_pm25(row["PM25"])
        pm_val   = round(float(row["PM25"]), 1)
        nom      = row["Station"]
        date_str = str(row["Date"])[:16]
        lat      = float(row["Latitude"])
        lon      = float(row["Longitude"])

        fg_s = folium.FeatureGroup(name="Station : " + nom, show=True)
        folium.Circle(
            location=[lat, lon], radius=RAYON_M,
            color=c, fill=True, fill_color=c,
            fill_opacity=0.3, weight=2, opacity=0.9
        ).add_to(fg_s)
        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            color=c,
            fill=True,
            fill_color=c,
            fill_opacity=0.9,
            weight=2,
            tooltip=folium.Tooltip(
                "<b>" + nom + "</b><br>" + str(pm_val) + " µg/m³",
                style="background:#0f0f19;color:white;font-family:'Segoe UI',Arial;font-size:12px;padding:6px 10px;border-radius:6px;border:none;"
            ),
            popup=folium.Popup(
                "<b>" + nom + "</b><br>PM2.5 : <span style='color:" + c + ";font-weight:700;'>" + str(pm_val) + " µg/m³</span>",
                max_width=200
            )
        ).add_to(fg_s)
        fg_s.add_to(m)

    folium.LayerControl(position="topright", collapsed=True).add_to(m)

    nom_map = m.get_name()
    script_pont = folium.Element("""
    <script>
    (function() {
        function exposerVersParent() {
            var map = window["%(nom_map)s"];
            if (!map || typeof map.setView !== "function") {
                var keys = Object.keys(window);
                for (var i = 0; i < keys.length; i++) {
                    var k = keys[i];
                    if (k.indexOf("map_") === 0) {
                        var obj = window[k];
                        if (obj && typeof obj.setView === "function") { map = obj; break; }
                    }
                }
            }
            if (!map) { setTimeout(exposerVersParent, 200); return; }
            try {
                window.parent._iframeMap = map;
                window.parent._iframeL   = window.L;
                window.parent._iframeMapReady = true;
            } catch(e) {}
        }
        if (document.readyState === "complete") { exposerVersParent(); }
        else { window.addEventListener("load", exposerVersParent); }
    })();
    </script>
    """ % {"nom_map": nom_map})
    m.get_root().html.add_child(script_pont)

    return m._repr_html_(), centre_lat, centre_lon, id_fg_contours, id_fg_qualite, id_fg_labels

# ============================================================
# CALCUL KPI
# ============================================================

def calculer_kpi(df):
    derniere    = df.sort_values("Date").groupby("Station").tail(1)
    pm_moyen    = round(derniere["PM25"].mean(), 1)
    pm_max      = round(derniere["PM25"].max(), 1)
    station_max = derniere.loc[derniere["PM25"].idxmax(), "Station"]
    nb_bonnes   = int((derniere["PM25"] <= 5).sum())
    nb_actives  = len(derniere)
    return {
        "pm_moyen"    : pm_moyen,
        "pm_max"      : pm_max,
        "station_max" : station_max,
        "nb_bonnes"   : nb_bonnes,
        "nb_actives"  : nb_actives,
        "nb_total"    : len(STATIONS_IDS),
        "derniere"    : derniere,
        "heure_maj"   : datetime.now().strftime("%H:%M"),
        "logo_b64"    : logo_b64,
        "monument_b64": monument_b64
    }

# ============================================================
# EXECUTION UNIQUE (pas de boucle)
# ============================================================

print("\n" + "=" * 50)
print("GENERATION - " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
print("=" * 50)

mesures = collecter_donnees()
if not mesures:
    print("[ERR ] Aucune donnee collectee - arret")
    exit(1)

df = pd.DataFrame(mesures)
df["Date"] = pd.to_datetime(df["Date"])
df = df.sort_values("Date")
print("[INFO] Total mesures : " + str(len(df)))

kpi                    = calculer_kpi(df)
carte_html, clat, clon, id_fg_contours, id_fg_qualite, id_fg_labels = construire_carte_html(df)
html_final             = generer_dashboard(kpi, carte_html, clat, clon, communes_data_global, id_fg_contours, id_fg_qualite, id_fg_labels)

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html_final)
print("[ OK ] Dashboard genere : " + OUTPUT_HTML)
