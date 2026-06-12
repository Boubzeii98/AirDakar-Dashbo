import json as _json
from datetime import datetime


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


def generer_dashboard(kpi, carte_html, centre_lat, centre_lon, communes_data=None, id_fg_contours='', id_fg_qualite='', id_fg_labels='', historique_data=None):

    if communes_data is None:
        communes_data = {}
    if historique_data is None:
        historique_data = []

    derniere     = kpi["derniere"]
    pm_moyen     = kpi["pm_moyen"]
    pm_max       = kpi["pm_max"]
    station_max  = kpi["station_max"]
    nb_bonnes    = kpi["nb_bonnes"]
    nb_actives   = kpi["nb_actives"]
    nb_total     = kpi["nb_total"]
    heure_maj    = kpi["heure_maj"]
    logo_b64     = kpi.get("logo_b64")
    monument_b64 = kpi.get("monument_b64")
    date_str     = datetime.now().strftime("%d/%m/%Y")

    couleur_moy = couleur_pm25(pm_moyen)
    score       = min(int(pm_moyen / 35 * 100), 100)
    score_label = label_pm25(pm_moyen)
    score_color = couleur_pm25(pm_moyen)

    logo_html = (
        '<img src="data:image/png;base64,' + logo_b64 + '" '
        'style="height:32px;width:auto;object-fit:contain;" alt="AirDakar">'
        if logo_b64 else
        '<div style="width:32px;height:32px;border-radius:50%;background:#00e676;flex-shrink:0;"></div>'
    )

    monument_css = (
        "url('data:image/jpeg;base64," + monument_b64 + "') center center / cover no-repeat"
        if monument_b64 else
        "linear-gradient(135deg,#0a0e1a 0%,#0d2d1a 50%,#0a1a2e 100%)"
    )

    # Donnees stations
    stations_data = []
    for _, row in derniere.iterrows():
        stations_data.append({
            "nom":     row["Station"],
            "lat":     float(row["Latitude"]),
            "lon":     float(row["Longitude"]),
            "pm25":    round(float(row["PM25"]), 1),
            "couleur": couleur_pm25(float(row["PM25"])),
            "qualite": label_pm25(float(row["PM25"]))
        })

    stations_json = _json.dumps(stations_data)
    communes_json = _json.dumps(communes_data)

    options_stations = "\n".join(
        '<option value="' + s["nom"] + '">' + s["nom"][:44] + '</option>'
        for s in sorted(stations_data, key=lambda x: x["nom"])
    )
    options_communes = "\n".join(
        '<option value="' + n + '">' + n + '</option>'
        for n in sorted(communes_data.keys())
    )

    # Classement
    classement_rows = ""
    top        = derniere.sort_values("PM25", ascending=False).head(8)
    pm_max_val = float(top["PM25"].max()) if len(top) > 0 else 1.0
    for _, row in top.iterrows():
        c   = couleur_pm25(row["PM25"])
        pct = int(row["PM25"] / pm_max_val * 100)
        nom = row["Station"][:28]
        classement_rows += (
            '<div class="sr">'
            '<div style="width:9px;height:9px;border-radius:50%;background:' + c + ';flex-shrink:0;"></div>'
            '<div style="flex:1;">'
            '<div style="font-size:11px;color:var(--ts);line-height:1.3;">' + nom + '</div>'
            '<div style="height:3px;background:var(--bb);border-radius:2px;margin-top:3px;">'
            '<div style="height:3px;width:' + str(pct) + '%;background:' + c + ';border-radius:2px;"></div>'
            '</div></div>'
            '<span style="font-size:12px;font-weight:600;color:' + c + ';">' + str(round(row["PM25"], 1)) + '</span>'
            '</div>'
        )

    # Alertes
    alertes_rows = ""
    dep       = derniere[derniere["PM25"] > 5].sort_values("PM25", ascending=False).head(4)
    for _, row in dep.iterrows():
        pct_dep = int((row["PM25"] / 5 - 1) * 100)
        alertes_rows += (
            '<div style="display:flex;justify-content:space-between;align-items:center;'
            'padding:5px 0;border-top:0.5px solid var(--border);">'
            '<span style="font-size:11px;color:var(--ts);">' + row["Station"][:22] + '</span>'
            '<span style="font-size:11px;font-weight:600;color:#f44336;">+' + str(pct_dep) + '%</span>'
            '</div>'
        )
    nb_alertes = len(dep)

    alertes_contenu = (
        alertes_rows if alertes_rows
        else '<div style="font-size:11px;color:var(--ts);">Aucun depassement</div>'
    )

    centre_lat_str = "{:.4f}".format(centre_lat)
    centre_lon_str = "{:.4f}".format(centre_lon)

    page = """<!DOCTYPE html>
<html lang="fr" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<title>AirDakar - Qualite de l air</title>
<style>
:root[data-theme="dark"]{
  --bg:#080c18;--nav:#0d1120;--c1:rgba(255,255,255,0.04);--c2:rgba(255,255,255,0.03);
  --inp:#0f1525;--border:rgba(255,255,255,0.07);--bor2:rgba(255,255,255,0.07);
  --tp:#e0e6f0;--ts:rgba(255,255,255,0.45);--th:rgba(255,255,255,0.25);--tm:rgba(255,255,255,0.3);
  --bb:rgba(255,255,255,0.07);
  --hero:linear-gradient(120deg,rgba(8,12,24,0.88) 0%,rgba(8,12,24,0.50) 55%,rgba(8,12,24,0.18) 100%);
  --sb1:rgba(0,230,118,0.08);--sb1b:rgba(0,230,118,0.25);
  --sb2:rgba(255,152,0,0.08);--sb2b:rgba(255,152,0,0.25);
  --sb3:rgba(244,67,54,0.08);--sb3b:rgba(244,67,54,0.25);
  --st:rgba(255,255,255,0.6);--db:rgba(255,255,255,0.05);--dbb:rgba(255,255,255,0.12);
  --fb:rgba(13,17,32,0.97);
}
:root[data-theme="light"]{
  --bg:#f0f4f8;--nav:#fff;--c1:rgba(0,0,0,0.04);--c2:rgba(0,0,0,0.03);
  --inp:#fff;--border:rgba(0,0,0,0.09);--bor2:rgba(0,0,0,0.08);
  --tp:#1a1f2e;--ts:rgba(0,0,0,0.52);--th:rgba(0,0,0,0.35);--tm:rgba(0,0,0,0.4);
  --bb:rgba(0,0,0,0.08);
  --hero:linear-gradient(120deg,rgba(240,244,248,0.92) 0%,rgba(240,244,248,0.75) 55%,rgba(240,244,248,0.30) 100%);
  --sb1:rgba(0,180,90,0.12);--sb1b:rgba(0,180,90,0.3);
  --sb2:rgba(200,120,0,0.10);--sb2b:rgba(200,120,0,0.28);
  --sb3:rgba(200,50,40,0.10);--sb3b:rgba(200,50,40,0.28);
  --st:rgba(0,0,0,0.6);--db:rgba(0,0,0,0.06);--dbb:rgba(0,0,0,0.15);
  --fb:rgba(245,248,252,0.97);
  --hero-h1:#1a1f2e;--hero-h1-span:#007a3d;
  --hero-pdef-bg:rgba(240,244,248,0.92);--hero-pdef-border:rgba(0,0,0,0.12);
  --hero-pdef-t:#007a3d;--hero-pdef-b:rgba(0,0,0,0.72);--hero-pdef-strong:#1a1f2e;
  --hero-sd:rgba(0,0,0,0.65);
  --hero-kc-bg:rgba(240,244,248,0.88);--hero-kc-border:rgba(0,0,0,0.12);
  --hero-kn:#1a1f2e;--hero-kd:rgba(0,0,0,0.55);--hero-ks:rgba(0,0,0,0.35);
}
:root[data-theme="dark"]{
  --hero-h1:#fff;--hero-h1-span:#00e676;
  --hero-pdef-bg:rgba(255,255,255,0.05);--hero-pdef-border:rgba(255,255,255,0.12);
  --hero-pdef-t:#00bcd4;--hero-pdef-b:rgba(255,255,255,0.75);--hero-pdef-strong:#fff;
  --hero-sd:rgba(255,255,255,0.6);
  --hero-kc-bg:rgba(8,12,24,0.72);--hero-kc-border:rgba(255,255,255,0.14);
  --hero-kn:#fff;--hero-kd:rgba(255,255,255,0.55);--hero-ks:rgba(255,255,255,0.3);
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;font-size:13px}
body{font-family:'Segoe UI',Arial,sans-serif;background:var(--bg);color:var(--tp);display:flex;flex-direction:column;transition:background 0.3s,color 0.3s}
.nav{display:flex;align-items:center;justify-content:space-between;padding:0 18px;height:48px;flex-shrink:0;background:var(--nav);border-bottom:0.5px solid var(--bor2)}
.nb{display:flex;align-items:center;gap:9px}
.nt{font-size:15px;font-weight:600;color:var(--tp)}
.ns{font-size:11px;color:var(--ts);margin-left:3px}
.nl{display:flex;gap:3px}
.lnk{font-size:12px;padding:5px 12px;border-radius:6px;cursor:pointer;color:var(--ts);border:none;background:transparent;transition:all 0.2s}
.lnk:hover{background:var(--c1);color:var(--tp)}
.lnk.active{background:var(--c2);color:var(--tp);border:0.5px solid var(--border)}
.nr{display:flex;align-items:center;gap:8px}
.bl{font-size:11px;padding:3px 10px;border-radius:20px;background:rgba(0,230,118,0.1);color:#00e676;border:0.5px solid rgba(0,230,118,0.25)}
.bt{font-size:11px;color:var(--ts)}
.page{display:none;flex:1;overflow-y:auto;flex-direction:column}
.page.active{display:flex}
.hw{flex:1;position:relative;overflow:hidden;display:flex;min-height:calc(100vh - 48px)}
.hbg{position:absolute;inset:0;z-index:0;animation:zbg 14s ease-in-out infinite alternate}
@keyframes zbg{0%{transform:scale(1.0)}100%{transform:scale(1.09)}}
.hov{position:absolute;inset:0;z-index:1;background:var(--hero)}
.hct{position:relative;z-index:2;padding:60px 48px 48px;max-width:820px}
.htag{display:inline-flex;align-items:center;gap:5px;font-size:11px;color:rgba(0,230,118,0.95);background:rgba(0,230,118,0.1);border:0.5px solid rgba(0,230,118,0.35);border-radius:20px;padding:4px 14px;margin-bottom:18px}
.hh1{font-size:38px;font-weight:700;line-height:1.12;margin-bottom:16px;color:var(--hero-h1);text-shadow:0 2px 16px rgba(0,0,0,0.35)}
.hh1 span{color:var(--hero-h1-span)}
.pdef{background:var(--hero-pdef-bg);border:0.5px solid var(--hero-pdef-border);border-radius:12px;padding:16px 20px;margin-bottom:20px;max-width:680px;backdrop-filter:blur(6px)}
.pdef-t{font-size:13px;font-weight:600;color:var(--hero-pdef-t);margin-bottom:8px;display:flex;align-items:center;gap:7px}
.pdef-b{font-size:12px;line-height:1.8;color:var(--hero-pdef-b)}
.pdef-b strong{color:var(--hero-pdef-strong);font-weight:500}
.sg{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:24px;max-width:680px}
.sc{border-radius:10px;padding:14px 16px;backdrop-filter:blur(6px)}
.sv{font-size:18px;font-weight:700;margin-bottom:3px}
.sl{font-size:11px;font-weight:600;margin-bottom:6px}
.sd{font-size:11px;color:var(--hero-sd);line-height:1.6}
.hkpi{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:26px;max-width:680px}
.hkc{background:var(--hero-kc-bg);border:0.5px solid var(--hero-kc-border);border-radius:12px;padding:16px 18px;backdrop-filter:blur(8px)}
.hkn{font-size:22px;font-weight:600;margin-bottom:4px;color:var(--hero-kn)}
.hkd{font-size:12px;color:var(--hero-kd);line-height:1.5}
.hks{font-size:10px;color:var(--hero-ks);margin-top:4px}
.hbtn{display:inline-flex;align-items:center;gap:7px;font-size:13px;font-weight:600;padding:12px 26px;background:#00e676;color:#041a0c;border:none;border-radius:8px;cursor:pointer}
.dc{padding:12px 16px;display:flex;flex-direction:column;gap:10px;flex:1;overflow:hidden;min-height:0}
.dt{display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
.dtl{font-size:12px;color:var(--ts)}
.dbtn{font-size:11px;padding:5px 12px;border-radius:6px;border:0.5px solid var(--border);background:var(--c2);color:var(--ts);cursor:pointer}
.dm{display:grid;grid-template-columns:1fr 260px;gap:10px;flex:1;overflow:hidden;min-height:0}
.dl{display:flex;flex-direction:column;gap:10px;overflow:hidden}
.dr{display:flex;flex-direction:column;gap:8px;overflow-y:auto}
.kr{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;flex-shrink:0}
.kc{background:var(--c1);border:0.5px solid var(--border);border-radius:8px;padding:11px 13px}
.kl{font-size:9px;color:var(--ts);letter-spacing:0.5px;text-transform:uppercase;margin-bottom:5px}
.kv{font-size:18px;font-weight:600;color:var(--tp)}
.ks{font-size:10px;color:var(--tm);margin-top:2px}
.cb{background:var(--c2);border:0.5px solid var(--border);border-radius:8px;overflow:hidden;flex:1;display:flex;flex-direction:column;min-height:0;position:relative}
.ch{display:flex;align-items:center;justify-content:space-between;padding:7px 13px;border-bottom:0.5px solid var(--border);flex-shrink:0}
.ct{font-size:12px;font-weight:500;color:var(--tp)}
.fb{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:8px 12px;border-bottom:0.5px solid var(--border);background:var(--fb);flex-shrink:0}
.fl{font-size:11px;color:var(--ts);white-space:nowrap;font-weight:500}
.fs{background:var(--inp);color:var(--tp);border:0.5px solid var(--border);border-radius:6px;padding:5px 8px;font-size:11px;cursor:pointer;font-family:'Segoe UI',Arial}
.fs:focus{outline:none;border-color:rgba(0,188,212,0.5)}
.fn{padding:5px 11px;border-radius:6px;font-size:11px;cursor:pointer;font-family:'Segoe UI',Arial;white-space:nowrap;transition:all 0.2s}
.fr{background:var(--c1);border:0.5px solid var(--border);color:var(--ts)}
.fi{display:none;padding:4px 10px;background:rgba(0,188,212,0.08);border:0.5px solid rgba(0,188,212,0.2);border-radius:6px;font-size:11px;align-items:center;gap:5px}
.fsep{width:1px;height:18px;background:var(--border);flex-shrink:0}
.fcouche{padding:5px 11px;border-radius:6px;font-size:11px;cursor:pointer;font-family:'Segoe UI',Arial;white-space:nowrap;transition:all 0.2s;background:rgba(0,188,212,0.05);border:0.5px solid rgba(0,188,212,0.15);color:rgba(0,188,212,0.6);}
.fcouche.actif{background:rgba(0,188,212,0.2);border:0.5px solid #00bcd4;color:#00bcd4;}
.cmap{flex:1;min-height:0;position:relative;overflow:hidden}
.cmap>div{width:100%!important;height:100%!important}
.ps{font-size:9px;letter-spacing:0.8px;text-transform:uppercase;color:var(--ts);margin-bottom:6px}
.pb{background:var(--c1);border:0.5px solid var(--border);border-radius:8px;padding:12px}
.sr{display:flex;align-items:center;gap:7px;padding:6px 9px;background:var(--c2);border:0.5px solid var(--border);border-radius:7px;margin-bottom:5px}
.ab{background:rgba(244,67,54,0.05);border:0.5px solid rgba(244,67,54,0.18);border-radius:8px;padding:11px}
.ah{display:flex;align-items:center;gap:7px;margin-bottom:5px}
.ai{width:20px;height:20px;border-radius:4px;background:rgba(244,67,54,0.15);display:flex;align-items:center;justify-content:center;font-size:11px;color:#f44336}
.at{font-size:12px;font-weight:500;color:#f44336}
.scb{background:var(--c1);border:0.5px solid var(--border);border-radius:8px;padding:12px;text-align:center}
.fond-card:hover{border-color:rgba(255,255,255,0.35)!important;transform:translateY(-2px);transition:all 0.2s;}
.fond-card.actif-fond{border-color:#3b82f6!important;}
.tbtn{position:fixed;bottom:24px;left:24px;z-index:9998;width:42px;height:42px;border-radius:50%;background:var(--nav);border:0.5px solid var(--border);cursor:pointer;font-size:20px;display:flex;align-items:center;justify-content:center;color:var(--tp);transition:all 0.3s}
.tbtn:hover{transform:scale(1.08)}
.footer{padding:11px 24px;border-top:0.5px solid var(--border);display:flex;justify-content:space-between;align-items:center;font-size:10px;color:var(--th);background:var(--nav);flex-shrink:0}
.ep{max-width:860px;margin:0 auto;padding:44px 32px}
.etag{display:inline-flex;align-items:center;gap:5px;font-size:11px;color:rgba(0,188,212,0.9);background:rgba(0,188,212,0.08);border:0.5px solid rgba(0,188,212,0.2);border-radius:20px;padding:4px 13px;margin-bottom:18px}
.eh1{font-size:26px;font-weight:600;line-height:1.25;margin-bottom:12px;color:var(--tp)}
.eh1 span{color:#00bcd4}
.ei{font-size:13px;color:var(--ts);line-height:1.8;max-width:600px;margin-bottom:28px}
.egrille{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:28px}
.ecard{background:var(--c1);border:0.5px solid var(--border);border-radius:10px;padding:16px}
.enum{font-size:24px;font-weight:600;margin-bottom:4px}
.edesc{font-size:11px;color:var(--ts);line-height:1.5}
.esrc{font-size:10px;color:var(--th);margin-top:5px}
.esec{font-size:9px;letter-spacing:0.8px;text-transform:uppercase;color:var(--ts);margin-bottom:12px}
.eig{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:24px}
.eic{background:var(--c1);border:0.5px solid var(--border);border-radius:8px;padding:13px;display:flex;gap:10px}
.eii{width:32px;height:32px;border-radius:7px;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:16px}
.eit{font-size:12px;font-weight:500;margin-bottom:4px;color:var(--tp)}
.eid{font-size:11px;color:var(--ts);line-height:1.6}
.ebl{display:flex;flex-direction:column;gap:7px;margin-bottom:24px}
.ebr{display:flex;align-items:flex-start;gap:10px;padding:11px 13px;background:var(--c2);border:0.5px solid var(--border);border-radius:8px}
.ebi{color:#00bcd4;font-size:16px;flex-shrink:0;margin-top:1px}
.ebt{font-size:11px;color:var(--ts);line-height:1.7}
.ebt strong{color:var(--tp);font-weight:500}
.edb{background:rgba(0,188,212,0.05);border:0.5px solid rgba(0,188,212,0.15);border-radius:8px;padding:18px;margin-bottom:8px}
.edbh{font-size:14px;font-weight:500;color:#00bcd4;margin-bottom:8px}
.edbp{font-size:12px;color:var(--ts);line-height:1.8;margin-bottom:12px}
.pills{display:flex;flex-wrap:wrap;gap:7px}
.pill{font-size:11px;padding:5px 12px;border-radius:20px;background:var(--c2);border:0.5px solid var(--border);color:var(--ts)}
.ac{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:24px}
.acc{background:var(--c1);border:0.5px solid var(--border);border-radius:8px;padding:15px}
.act{font-size:12px;font-weight:500;color:#00bcd4;margin-bottom:6px}
.acb{font-size:11px;color:var(--ts);line-height:1.7}
.aal{color:#00bcd4;text-decoration:none}
.stg{display:grid;grid-template-columns:repeat(2,1fr);gap:7px;margin-top:10px}
.sti{background:var(--c2);border:0.5px solid var(--border);border-radius:7px;padding:7px 11px;font-size:11px;color:var(--ts)}

/* ============================================================
   RESPONSIVE MOBILE  (breakpoint 768px)
   ============================================================ */

/* Hamburger menu - cache par defaut */
.nav-hamburger{display:none;flex-direction:column;gap:5px;cursor:pointer;padding:8px;border:none;background:transparent;}
.nav-hamburger span{display:block;width:20px;height:2px;background:var(--tp);border-radius:2px;transition:all 0.3s;}

/* Menu mobile overlay */
.nav-mobile{display:none;position:fixed;top:48px;left:0;right:0;bottom:0;z-index:9990;
  background:var(--nav);flex-direction:column;padding:16px;gap:4px;overflow-y:auto;
  border-top:0.5px solid var(--border);}
.nav-mobile.open{display:flex;}
.nav-mobile .lnk{font-size:14px;padding:12px 16px;border-radius:8px;text-align:left;width:100%;}

@media(max-width:768px){

  /* Navigation */
  .nl{display:none;}
  .ns{display:none;}
  .nav-hamburger{display:flex;}
  .nr .bt{display:none;}

  /* Page accueil */
  .hct{padding:32px 20px 32px;}
  .hh1{font-size:26px;}
  .sg{grid-template-columns:1fr;gap:8px;}
  .hkpi{grid-template-columns:1fr;gap:8px;}
  .pdef{max-width:100%;}

  /* Dashboard - empilement vertical */
  .dc{padding:8px 10px;gap:8px;}
  .dm{grid-template-columns:1fr;grid-template-rows:auto 1fr;gap:8px;}
  .dl{overflow:visible;}
  .dr{display:none;}  /* panneau droit masque sur mobile */

  /* KPI : 2 colonnes */
  .kr{grid-template-columns:repeat(2,1fr);gap:6px;}
  .dc{overflow-y:auto;overflow-x:hidden;}
  .dl{overflow:visible;}

  /* Carte : hauteur fixe sur mobile */
  .cb{min-height:50vh;height:50vh;}
  .cmap{min-height:42vh;height:42vh;}

  /* Barre filtres : 2 lignes sur mobile */
  .fb{flex-wrap:wrap;gap:5px;padding:6px 8px;}
  .fl{display:none;}
  .fsep{display:none;}
  .fs{flex:1;min-width:120px;font-size:11px;}
  .fcouche{font-size:10px;padding:4px 8px;}
  .fn{font-size:10px;padding:4px 8px;}

  /* Panneau fond de carte */
  #fond-panel > div{min-width:90vw !important;padding:18px 16px !important;}
  #fond-panel > div > div:last-child{grid-template-columns:repeat(2,1fr) !important;}

  /* Pages contenu */
  .ep{padding:24px 16px;}
  .egrille{grid-template-columns:1fr;gap:8px;}
  .eig{grid-template-columns:1fr;}
  .ac{grid-template-columns:1fr;}
  .stg{grid-template-columns:1fr;}
  .eh1{font-size:20px;}

  /* Footer */
  .footer{flex-direction:column;gap:4px;text-align:center;padding:8px 16px;}

  /* Bouton theme */
  .tbtn{bottom:16px;left:16px;width:38px;height:38px;font-size:17px;}
}

@media(max-width:480px){
  .hh1{font-size:22px;}
  .kr{grid-template-columns:repeat(2,1fr);}
  .hkpi{grid-template-columns:1fr;}
  .nav .nt{font-size:14px;}
}
</style>
</head>
<body>
"""

    page += '<nav class="nav">'
    page += '<div class="nb">' + logo_html
    page += '<span class="nt">AirDakar</span>'
    page += '<span class="ns">Qualite de l\'air - Region de Dakar</span></div>'
    page += '<div class="nl">'
    page += '<button class="lnk active" onclick="showPage(\'accueil\',this)">Accueil</button>'
    page += '<button class="lnk" onclick="showPage(\'dashboard\',this)">Tableau de bord</button>'
    page += '<button class="lnk" onclick="showPage(\'pourquoi\',this)">Pourquoi la qualite de l\'air ?</button>'
    page += '<button class="lnk" onclick="showPage(\'stats\',this)">Statistiques</button>'
    page += '<button class="lnk" onclick="showPage(\'apropos\',this)">A propos</button>'
    page += '</div>'
    page += '<div class="nr">'
    page += '<span class="bl">&#9679; En direct</span>'
    page += '<span class="bt">MAJ ' + heure_maj + ' &bull; ' + date_str + '</span>'
    page += '<button class="nav-hamburger" id="nav-hamburger" onclick="toggleMenu()" aria-label="Menu"><span></span><span></span><span></span></button>'
    page += '</div></nav>'
    page += '<div class="nav-mobile" id="nav-mobile">'
    page += '<button class="lnk active" id="mob-accueil" onclick="showPage(\'accueil\',this);toggleMenu()">Accueil</button>'
    page += '<button class="lnk" id="mob-dashboard" onclick="showPage(\'dashboard\',this);toggleMenu()">Tableau de bord</button>'
    page += '<button class="lnk" id="mob-pourquoi" onclick="showPage(\'pourquoi\',this);toggleMenu()">Pourquoi la qualite de l\'air ?</button>'
    page += '<button class="lnk" id="mob-stats" onclick="showPage(\'stats\',this);toggleMenu()">Statistiques</button>'
    page += '<button class="lnk" id="mob-apropos" onclick="showPage(\'apropos\',this);toggleMenu()">A propos</button>'
    page += '</div>'

    # ── PAGE ACCUEIL ───────────────────────────────────────────────────────
    page += '<div id="page-accueil" class="page active">'
    page += '<div class="hw">'
    page += '<div class="hbg" style="background:' + monument_css + ';"></div>'
    page += '<div class="hov"></div>'
    page += '<div class="hct">'
    page += '<div class="htag">&#9728; Surveillance temps reel - Dakar, Senegal</div>'
    page += '<h1 class="hh1">Respirez mieux.<br><span>Connaissez votre air.</span></h1>'
    page += '<div class="pdef">'
    page += '<div class="pdef-t"><span style="font-size:18px;">&#128168;</span> Qu\'est-ce que le PM2.5 et le µg/m³ ?</div>'
    page += '<div class="pdef-b">'
    page += '<strong>PM2.5</strong> designe les <strong>particules fines</strong> de diametre inferieur a 2,5 microns'
    page += ' - 30 fois plus fin qu\'un cheveu humain. Ces particules penetrent profondement dans les poumons,'
    page += ' passent dans le sang et atteignent tous les organes.<br><br>'
    page += 'Leur concentration se mesure en <strong>µg/m³</strong> (microgrammes par metre cube d\'air).'
    page += ' Plus ce chiffre est eleve, plus l\'air est pollue et dangereux.<br><br>'
    page += '<strong>L\'OMS fixe le seuil de securite a 5 µg/m³</strong> en moyenne annuelle.'
    page += ' Au-dela, les risques cardiaques, respiratoires et cancereux augmentent significativement.'
    page += '</div></div>'
    page += '<div class="sg">'
    page += '<div class="sc" style="background:var(--sb1);border:0.5px solid var(--sb1b);">'
    page += '<div class="sv" style="color:#00e676;">0-5 µg/m³</div>'
    page += '<div class="sl" style="color:#00e676;">Bon</div>'
    page += '<div class="sd">Air sain. Qualite acceptable pour toute la population, y compris les personnes sensibles.</div>'
    page += '</div>'
    page += '<div class="sc" style="background:var(--sb2);border:0.5px solid var(--sb2b);">'
    page += '<div class="sv" style="color:#ff9800;">5-15 µg/m³</div>'
    page += '<div class="sl" style="color:#ff9800;">Modere</div>'
    page += '<div class="sd">Risques pour les groupes vulnerables. Eviter les efforts prolonges en exterieur.</div>'
    page += '</div>'
    page += '<div class="sc" style="background:var(--sb3);border:0.5px solid var(--sb3b);">'
    page += '<div class="sv" style="color:#f44336;">&gt;15 µg/m³</div>'
    page += '<div class="sl" style="color:#f44336;">Mauvais</div>'
    page += '<div class="sd">Danger pour toute la population. Limiter les activites physiques exterieures.</div>'
    page += '</div></div>'
    page += '<div class="hkpi">'
    page += '<div class="hkc">'
    page += '<div class="hkn" style="color:' + couleur_moy + ';">' + str(pm_moyen)
    page += ' <span style="font-size:12px;font-weight:400;color:rgba(255,255,255,0.4);">µg/m³</span></div>'
    page += '<div class="hkd">PM2.5 moyen actuel sur Dakar</div>'
    page += '<div class="hks">Seuil OMS annuel : 5 µg/m³</div></div>'
    page += '<div class="hkc">'
    page += '<div class="hkn">' + str(nb_actives)
    page += '<span style="font-size:12px;font-weight:400;color:rgba(255,255,255,0.4);">/' + str(nb_total) + '</span></div>'
    page += '<div class="hkd">Stations actives en ce moment</div>'
    page += '<div class="hks">Mise a jour toutes les 60 secondes</div></div>'
    page += '<div class="hkc">'
    page += '<div class="hkn" style="color:#00e676;">' + str(nb_bonnes) + '</div>'
    page += '<div class="hkd">Stations avec un air de bonne qualite</div>'
    page += '<div class="hks">PM2.5 inferieur a 5 µg/m³</div></div>'
    page += '</div>'
    page += '<button class="hbtn" onclick="showPage(\'dashboard\', document.querySelectorAll(\'.lnk\')[1])">'
    page += 'Voir le tableau de bord &#8594;</button>'
    page += '</div></div></div>'

    # ── PAGE DASHBOARD ─────────────────────────────────────────────────────
    page += '<div id="page-dashboard" class="page">'
    page += '<div class="dc">'
    page += '<div class="dt">'
    page += '<span class="dtl">&#9679; Dakar &bull; ' + str(nb_actives) + '/' + str(nb_total) + ' stations actives &bull; MAJ ' + heure_maj + '</span>'
    page += '<button class="dbtn" onclick="location.reload()">&#8635; Actualiser</button>'
    page += '</div>'
    page += '<div class="dm"><div class="dl">'

    # KPI
    page += '<div class="kr">'
    page += '<div class="kc"><div class="kl">PM2.5 moyen</div>'
    page += '<div class="kv" style="color:' + couleur_moy + ';">' + str(pm_moyen)
    page += ' <span style="font-size:10px;font-weight:400;color:var(--tm);">µg/m³</span></div>'
    page += '<div class="ks">Seuil OMS : 5 µg/m³</div></div>'
    page += '<div class="kc"><div class="kl">Stations actives</div>'
    page += '<div class="kv">' + str(nb_actives)
    page += ' <span style="font-size:10px;font-weight:400;color:var(--tm);">/' + str(nb_total) + '</span></div>'
    page += '<div class="ks">' + str(nb_total - nb_actives) + ' hors ligne</div></div>'
    page += '<div class="kc"><div class="kl">Pic actuel</div>'
    page += '<div class="kv" style="color:#f44336;">' + str(pm_max)
    page += ' <span style="font-size:10px;font-weight:400;color:var(--tm);">µg/m³</span></div>'
    page += '<div class="ks" title="' + station_max + '">' + station_max[:22] + '</div></div>'
    page += '<div class="kc"><div class="kl">Stations bonnes</div>'
    page += '<div class="kv" style="color:#00e676;">' + str(nb_bonnes)
    page += ' <span style="font-size:10px;font-weight:400;color:var(--tm);">/' + str(nb_total) + '</span></div>'
    page += '<div class="ks">inferieur a 5 µg/m³</div></div>'
    page += '</div>'

    # Carte
    page += '<div class="cb">'
    page += '<div class="ch">'
    page += '<span class="ct">&#127759; Carte PM2.5 - Dakar</span>'
    page += '<button id="btn-fond" onclick="toggleFondPanel()" style="display:flex;align-items:center;gap:6px;font-size:11px;padding:5px 12px;border-radius:6px;cursor:pointer;background:var(--c1);border:0.5px solid var(--border);color:var(--tp);font-family:\'Segoe UI\',Arial;transition:all 0.2s;">&#128506; Fond de carte</button>'
    page += '</div>'

    # Panneau fond de carte
    page += '<div id="fond-panel" style="display:none;position:absolute;top:0;left:0;right:0;bottom:0;z-index:9999;background:rgba(0,0,0,0.55);backdrop-filter:blur(3px);align-items:center;justify-content:center;">'
    page += '<div style="background:#1a1e2e;border-radius:16px;padding:24px 28px;min-width:520px;box-shadow:0 8px 40px rgba(0,0,0,0.7);border:0.5px solid rgba(255,255,255,0.12);position:relative;">'
    page += '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">'
    page += '<div style="font-size:15px;font-weight:600;color:#e0e6f0;">&#128506; Fond de carte</div>'
    page += '<button onclick="toggleFondPanel()" style="background:none;border:none;color:rgba(255,255,255,0.5);font-size:20px;cursor:pointer;padding:2px 6px;border-radius:4px;">&#10005;</button>'
    page += '</div>'
    page += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;">'

    fonds_def = [
        ("osm",         "Standard",    "linear-gradient(135deg,#e8f4e8 0%,#d4e8f0 40%,#c8e0f4 100%)", True),
        ("clair",       "Clair",       "linear-gradient(135deg,#f5f5f5 0%,#ebebeb 40%,#e0e8f0 100%)", False),
        ("sombre",      "Sombre",      "linear-gradient(135deg,#1a1a2e 0%,#16213e 40%,#0f3460 100%)", False),
        ("satellite",   "Satellite",   "linear-gradient(135deg,#2d4a1e 0%,#3a5a28 30%,#1e3a5a 60%,#162d40 100%)", False),
        ("terrain",     "Terrain",     "linear-gradient(135deg,#d4e8c8 0%,#c8d4a0 40%,#b8c890 100%)", False),
        ("minimaliste", "Minimaliste", "#f8f8f8", False),
    ]
    for fid, flabel, fbg, factif in fonds_def:
        border = "2.5px solid #3b82f6" if factif else "2px solid rgba(255,255,255,0.1)"
        lbl    = ("&#10003; " if factif else "") + flabel
        page += '<div class="fond-card' + (" actif-fond" if factif else "") + '" id="fond-' + fid + '" onclick="changerFond(\'' + fid + '\')" style="cursor:pointer;border-radius:10px;overflow:hidden;border:' + border + ';">'
        page += '<div style="height:90px;background:' + fbg + ';"></div>'
        page += '<div style="padding:8px 10px;text-align:center;font-size:12px;font-weight:500;color:#e0e6f0;background:#1a1e2e;">' + lbl + '</div>'
        page += '</div>'

    page += '</div></div></div>'

    # Barre filtres
    page += '<div class="fb">'
    page += '<span class="fl">&#128269; Station :</span>'
    page += '<select id="f-station" class="fs" style="min-width:175px;">'
    page += '<option value="">-- Toutes --</option>' + options_stations
    page += '</select>'
    page += '<div class="fsep"></div>'
    page += '<span class="fl">&#127968; Commune :</span>'
    page += '<select id="f-commune" class="fs" style="min-width:150px;">'
    page += '<option value="">-- Toutes --</option>' + options_communes
    page += '</select>'
    page += '<div class="fsep"></div>'
    page += '<button id="btn-contours" class="fcouche actif" title="Afficher/masquer contours">&#9646; Contours</button>'
    page += '<button id="btn-qualite"  class="fcouche actif" title="Afficher/masquer qualite PM2.5">&#127758; Qualite PM2.5</button>'
    page += '<button id="btn-labels"   class="fcouche actif" title="Afficher/masquer labels">&#9874; Labels</button>'
    page += '<div class="fsep"></div>'
    page += '<button id="btn-reset" class="fn fr">&#8635; Reinitialiser</button>'
    page += '<div id="filtre-info" class="fi">'
    page += '<span id="fi-nom" style="color:#00bcd4;font-weight:500;"></span>'
    page += '<span style="color:var(--ts);">&bull;</span>'
    page += '<span id="fi-val" style="font-weight:600;"></span>'
    page += '<span id="fi-qualite" style="color:var(--ts);font-size:10px;"></span>'
    page += '</div></div>'

    # Carte Folium
    page += '<div class="cmap" id="cmap">' + carte_html + '</div>'
    page += '</div>'  # fin .cb

    page += '</div>'  # fin .dl

    # Panneau droit
    page += '<div class="dr">'
    page += '<div><div class="ps">Indice qualite global</div>'
    page += '<div class="scb">'
    page += '<div style="font-size:10px;color:var(--ts);margin-bottom:5px;">Score PM2.5 moyen</div>'
    page += '<div style="font-size:24px;font-weight:600;color:' + score_color + ';">' + str(pm_moyen) + '</div>'
    page += '<div style="font-size:12px;color:var(--ts);margin-top:2px;">µg/m³ - ' + score_label + '</div>'
    page += '<div style="margin-top:8px;height:6px;background:var(--bb);border-radius:3px;">'
    page += '<div style="height:6px;width:' + str(score) + '%;background:' + score_color + ';border-radius:3px;"></div></div>'
    page += '<div style="display:flex;justify-content:space-between;font-size:9px;color:var(--th);margin-top:4px;">'
    page += '<span style="color:#00e676;">Bon</span><span style="color:#ff9800;">Modere</span><span style="color:#f44336;">Mauvais</span>'
    page += '</div></div></div>'

    page += '<div><div class="ps">Classement stations</div>' + classement_rows + '</div>'

    page += '<div><div class="ps">Alertes OMS</div>'
    page += '<div class="ab"><div class="ah">'
    page += '<div class="ai">&#9888;</div>'
    page += '<span class="at">' + str(nb_alertes) + ' depassements OMS</span>'
    page += '</div>' + alertes_contenu + '</div></div>'

    page += '<div class="pb"><div class="ps">Legende PM2.5</div>'
    page += '<div style="display:flex;flex-direction:column;gap:6px;font-size:11px;color:var(--tp);">'
    page += '<div><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#00e676;margin-right:8px;vertical-align:middle;"></span>Bon - 0 a 5 µg/m³</div>'
    page += '<div><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#ff9800;margin-right:8px;vertical-align:middle;"></span>Moyen - 5 a 15 µg/m³</div>'
    page += '<div><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#f44336;margin-right:8px;vertical-align:middle;"></span>Mauvais - &gt;15 µg/m³</div>'
    page += '</div>'
    page += '<div style="margin-top:8px;font-size:10px;color:var(--th);">'
    page += '<span style="display:inline-block;width:18px;border-top:2px dashed #00bcd4;vertical-align:middle;margin-right:5px;"></span>Contours communes&nbsp;&nbsp;'
    page += '<span style="display:inline-block;width:12px;height:12px;background:rgba(0,230,118,0.4);border:1px solid #00e676;vertical-align:middle;margin-right:5px;border-radius:2px;"></span>Qualite PM2.5'
    page += '</div></div>'

    page += '</div>'  # fin .dr
    page += '</div>'  # fin .dm
    page += '</div>'  # fin .dc
    page += '</div>'  # fin page-dashboard

    # ── PAGE POURQUOI ──────────────────────────────────────────────────────
    page += '<div id="page-pourquoi" class="page"><div class="ep">'
    page += '<div class="etag">&#9680; Pourquoi la qualite de l\'air ?</div>'
    page += '<h1 class="eh1">La pollution de l\'air est la <span>2e cause de mortalite</span> dans le monde</h1>'
    page += '<p class="ei">Jusqu\'a 99% d\'entre nous respirons un air pollue, reduisant notre esperance de vie de 1,9 an en moyenne.</p>'
    page += '<div class="egrille">'
    page += '<div class="ecard"><div class="enum" style="color:#f44336;">8M+</div><div class="edesc">deces annuels lies a la pollution de l\'air</div><div class="esrc">State of Global Air, 2024</div></div>'
    page += '<div class="ecard"><div class="enum" style="color:#ff9800;">99%</div><div class="edesc">de la population mondiale respire un air pollue</div><div class="esrc">OMS</div></div>'
    page += '<div class="ecard"><div class="enum" style="color:#00bcd4;">2 000</div><div class="edesc">enfants de moins de 5 ans meurent chaque jour</div><div class="esrc">UNICEF</div></div>'
    page += '</div>'
    page += '<div class="esec">Impacts sur la sante</div>'
    page += '<div class="eig">'
    page += '<div class="eic"><div class="eii" style="background:rgba(244,67,54,0.1);color:#f44336;">&#10084;</div><div><div class="eit">Maladies cardiovasculaires</div><div class="eid">La pollution affecte le coeur et les vaisseaux sanguins, augmentant le risque d\'infarctus et d\'AVC.</div></div></div>'
    page += '<div class="eic"><div class="eii" style="background:rgba(255,152,0,0.1);color:#ff9800;">&#127744;</div><div><div class="eit">Maladies respiratoires</div><div class="eid">Asthme, bronchite chronique et cancer du poumon sont lies a l\'exposition aux PM2.5.</div></div></div>'
    page += '<div class="eic"><div class="eii" style="background:rgba(0,188,212,0.1);color:#00bcd4;">&#128118;</div><div><div class="eit">Enfants et femmes enceintes</div><div class="eid">Les enfants sont proportionnellement plus exposes. Les effets commencent in utero.</div></div></div>'
    page += '<div class="eic"><div class="eii" style="background:rgba(127,119,221,0.12);color:#7f77dd;">&#9878;</div><div><div class="eit">Inegalites sociales</div><div class="eid">Les communautes marginalisees respirent un air plus pollue et sont plus vulnerables.</div></div></div>'
    page += '</div>'
    page += '<div class="esec">Benefices d\'un air plus propre</div>'
    page += '<div class="ebl">'
    page += '<div class="ebr"><div class="ebi">&#10052;</div><div class="ebt"><strong>Climat plus stable</strong> - Reduire les combustibles fossiles reduit simultanement CO2 et PM2.5.</div></div>'
    page += '<div class="ebr"><div class="ebi">&#127807;</div><div class="ebt"><strong>Securite alimentaire</strong> - Un air plus propre ameliore les rendements agricoles.</div></div>'
    page += '<div class="ebr"><div class="ebi">&#127963;</div><div class="ebt"><strong>Economies plus fortes</strong> - Un air sain produit une main-d\'oeuvre plus productive.</div></div>'
    page += '<div class="ebr"><div class="ebi">&#9878;</div><div class="ebt"><strong>Plus grande equite sociale</strong> - La reduction de la pollution beneficie en priorite aux plus exposes.</div></div>'
    page += '</div>'
    page += '<div class="edb"><div class="edbh">Pourquoi les donnees sont essentielles</div>'
    page += '<p class="edbp">Seulement 61% des gouvernements mondiaux produisent des donnees sur la qualite de l\'air, laissant plus d\'un milliard de personnes sans information pour se proteger.</p>'
    page += '<div class="pills"><span class="pill">Surveillance en temps reel</span><span class="pill">Politiques publiques</span><span class="pill">Recherche scientifique</span><span class="pill">Protection des populations</span></div>'
    page += '</div>'
    page += '<div style="margin-top:14px;font-size:11px;color:var(--th);">Sources : <a href="https://openaq.org/why-air-quality/" style="color:#00bcd4;">OpenAQ</a> &bull; OMS &bull; UNICEF &bull; State of Global Air 2024</div>'
    page += '</div></div>'

    # ── PAGE STATISTIQUES ──────────────────────────────────────────────────
    page += '<div id="page-stats" class="page"><div class="ep">'
    page += '<div class="etag">Statistiques</div>'
    page += '<h1 class="eh1">Analyse de la <span>qualite de l\'air</span></h1>'
    page += '<p class="ei">Visualisez les donnees PM2.5 par station et par commune.</p>'

    # Filtre station pour graphiques
    page += '<div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;flex-wrap:wrap;">'
    page += '<label style="font-size:12px;color:var(--ts);">Station :</label>'
    page += '<select id="stats-station" class="fs" style="min-width:200px;">'
    page += '<option value="">-- Toutes les stations --</option>' + options_stations
    page += '</select>'
    page += '<button onclick="filtrerStats()" class="fn fr" style="padding:5px 14px;">Afficher</button>'
    page += '</div>'

    # Graphique 1 : Courbe temporelle
    page += '<div class="esec">Evolution temporelle PM2.5</div>'
    page += '<div style="background:var(--c1);border:0.5px solid var(--border);border-radius:10px;padding:16px;margin-bottom:20px;">'
    page += '<canvas id="chart-courbe" style="width:100%;max-height:280px;"></canvas>'
    page += '</div>'

    # Graphique 2 : Barres comparatives stations
    page += '<div class="esec">Comparaison des stations (derniere mesure)</div>'
    page += '<div style="background:var(--c1);border:0.5px solid var(--border);border-radius:10px;padding:16px;margin-bottom:20px;">'
    page += '<canvas id="chart-barres" style="width:100%;max-height:320px;"></canvas>'
    page += '</div>'

    # Graphique 3 : PM2.5 par commune
    page += '<div class="esec">PM2.5 moyen par commune</div>'
    page += '<div style="background:var(--c1);border:0.5px solid var(--border);border-radius:10px;padding:16px;margin-bottom:20px;">'
    page += '<canvas id="chart-communes" style="width:100%;max-height:400px;"></canvas>'
    page += '</div>'

    page += '</div></div>'


    # ── PAGE A PROPOS ──────────────────────────────────────────────────────
    page += '<div id="page-apropos" class="page"><div class="ep">'
    page += '<div class="etag">A propos</div>'
    page += '<h1 class="eh1">A propos d\'<span>AirDakar</span></h1>'
    page += '<p class="ei">Outil de visualisation en temps reel de la qualite de l\'air dans la region de Dakar. Donnees issues de 16 stations via l\'API OpenAQ, mis a jour toutes les 60 secondes.</p>'
    page += '<div class="ac">'
    page += '<div class="acc"><div class="act">Source des donnees</div><div class="acb">OpenAQ - API v3, acces libre.<br><a href="https://openaq.org" class="aal">openaq.org</a></div></div>'
    page += '<div class="acc"><div class="act">Limites administratives</div><div class="acb">Shapefile communes - Decoupage administratif Dakar<br>Source : donnees geographiques locales</div></div>'
    page += '<div class="acc"><div class="act">Technologies</div><div class="acb">Python 3 &bull; Folium &bull; GeoPandas &bull; Pandas &bull; Requests</div></div>'
    page += '<div class="acc"><div class="act">Polluant surveille</div><div class="acb">PM2.5 &le; 2,5 µm &bull; Seuil OMS : 5 µg/m³</div></div>'
    page += '</div>'
    page += '<div class="esec">Stations surveillees (' + str(nb_actives) + ' actives)</div>'
    page += '<div class="stg">'
    stations_apropos = [
        ("Senegal, Dakar", "1531944"), ("Ecole Elhadj Mbaye Diop", "3315287"),
        ("Dakar Plateau", "3400976"), ("Lycee de Bargny, Rufisque", "3431595"),
        ("Station reference, Pikine", "3439881"), ("ESMT Dakar", "6096080"),
        ("CEM Martin Luther King", "6133773"), ("Complexe Scolaire Limamoulaye", "6133848"),
        ("Ecole Medina Gana Sarr", "6167229"), ("Ecole Seydina Issa Laye B", "6167230"),
        ("Mairie Tivaoune Diacksao", "6167231"), ("Hopital Youssou Mbarguane", "6167232"),
        ("Lycee Blaise Diagne", "6192633"), ("Pikine, Ecole Mbaye Diouf", "6196278"),
        ("Diamniadio", "5261049"), ("Universite Amadou Mahtar Mbow", "6134928"),
    ]
    for nom_st, id_st in stations_apropos:
        page += '<div class="sti">' + nom_st + ' - ID ' + id_st + '</div>'
    page += '</div></div></div>'

    # ── BOUTON THEME + FOOTER ──────────────────────────────────────────────
    page += '<button class="tbtn" id="tbtn" onclick="toggleTheme()" title="Mode clair / sombre">&#9790;</button>'
    page += '<footer class="footer">'
    page += '<span>AirDakar &bull; OpenAQ &bull; 16 stations &bull; Dakar, Senegal</span>'
    page += '<span>Seuil OMS PM2.5 : 5 µg/m³ &bull; MAJ toutes les 60 secondes</span>'
    page += '</footer>'

    # ── JAVASCRIPT ─────────────────────────────────────────────────────────
    page += '<script>'
    page += 'var stationsDash     = ' + stations_json + ';'
    page += 'var communesDash     = ' + communes_json + ';'
    page += 'var fondPanelVisible = false;'
    page += 'var currentTheme     = "dark";'
    page += 'var etatContours     = true;'
    page += 'var etatQualite      = true;'
    page += 'var etatLabels       = true;'
    page += 'var NOM_CONTOURS     = "Communes \u2014 contours";'
    page += 'var NOM_QUALITE      = "Communes \u2014 qualite PM2.5";'
    page += 'var NOM_LABELS       = "Communes \u2014 labels";'
    page += 'var ID_FG_CONTOURS   = "' + id_fg_contours + '";'
    page += 'var ID_FG_QUALITE    = "' + id_fg_qualite + '";'
    page += 'var ID_FG_LABELS     = "' + id_fg_labels + '";'
    page += 'var historiqueStats  = ' + _json.dumps(historique_data) + ';'

    # IMPORTANT : tout le JavaScript est dans un seul bloc f-string
    # pour eviter les commentaires Python parasites injectes dans le HTML
    page += """

// Acces direct au contentWindow de l'iframe Folium
function getIframeWin() {
    var iframes = document.querySelectorAll(".cmap iframe");
    if (!iframes.length) iframes = document.querySelectorAll("iframe");
    if (!iframes.length) return null;
    try { return iframes[0].contentWindow; } catch(e) { return null; }
}

function getCarteMap() {
    var win = getIframeWin();
    if (!win) return null;
    try {
        var keys = Object.keys(win);
        for (var i = 0; i < keys.length; i++) {
            var k = keys[i];
            if (k.indexOf("map_") === 0) {
                var obj = win[k];
                if (obj && typeof obj.setView === "function") return obj;
            }
        }
    } catch(e) {}
    return null;
}

function getL() {
    var win = getIframeWin();
    try { return (win && win.L) ? win.L : null; } catch(e) { return null; }
}

// Attendre que la carte soit prete, puis executer le callback
function avecCarte(fn) {
    var map = getCarteMap();
    if (map) { fn(map); return; }
    var attempts = 0;
    var t = setInterval(function() {
        attempts++;
        var m = getCarteMap();
        if (m) { clearInterval(t); fn(m); }
        else if (attempts > 40) { clearInterval(t); }
    }, 200);
}

// Fonds de carte
var FONDS = {
    osm:         "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    clair:       "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    sombre:      "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    satellite:   "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    terrain:     "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
    minimaliste: "https://{s}.basemaps.cartocdn.com/rastertiles/voyager_nolabels/{z}/{x}/{y}{r}.png"
};

function toggleFondPanel() {
    fondPanelVisible = !fondPanelVisible;
    document.getElementById("fond-panel").style.display = fondPanelVisible ? "flex" : "none";
}

function changerFond(nom) {
    var url = FONDS[nom];
    if (!url) return;
    avecCarte(function(map) {
        var LL = getL();
        if (!LL) return;
        var layersToRemove = [];
        map.eachLayer(function(layer) {
            if (layer instanceof LL.TileLayer) {
                layersToRemove.push(layer);
            }
        });
        layersToRemove.forEach(function(layer) { map.removeLayer(layer); });
        LL.tileLayer(url, { maxZoom: 20, crossOrigin: true }).addTo(map);
        document.querySelectorAll(".fond-card").forEach(function(el) { el.classList.remove("actif-fond"); });
        var active = document.getElementById("fond-" + nom);
        if (active) { active.classList.add("actif-fond"); }
        toggleFondPanel();
    });
}

document.getElementById("fond-panel").addEventListener("click", function(e) {
    if (e.target === this) toggleFondPanel();
});

// Forcer la page accueil au chargement
document.addEventListener("DOMContentLoaded", function() {
    showPage("accueil", document.querySelector(".lnk.active"));
});

// Menu hamburger mobile
function toggleMenu() {
    var menu = document.getElementById("nav-mobile");
    var btn  = document.getElementById("nav-hamburger");
    var open = menu.classList.toggle("open");
    btn.style.opacity = open ? "0.7" : "1";
}

// Fermer le menu si clic en dehors
document.addEventListener("click", function(e) {
    var menu = document.getElementById("nav-mobile");
    var btn  = document.getElementById("nav-hamburger");
    if (menu.classList.contains("open") && !menu.contains(e.target) && !btn.contains(e.target)) {
        menu.classList.remove("open");
    }
});

// Navigation pages
function showPage(id, btn) {
    document.querySelectorAll(".page").forEach(function(p) { p.classList.remove("active"); });
    document.querySelectorAll(".lnk").forEach(function(l) { l.classList.remove("active"); });
    document.getElementById("page-" + id).classList.add("active");
    if (btn) btn.classList.add("active");
    // Synchroniser le bouton mobile correspondant
    var mobBtn = document.getElementById("mob-" + id);
    if (mobBtn) mobBtn.classList.add("active");
    if (id === "dashboard") {
        setTimeout(function() {
            avecCarte(function(map) { map.invalidateSize(); });
        }, 120);
    }
    if (id === "stats") {
        setTimeout(function() { initCharts(); }, 150);
    }
}

// Theme
function toggleTheme() {
    currentTheme = currentTheme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", currentTheme);
    document.getElementById("tbtn").textContent = currentTheme === "dark" ? "\\u263e" : "\\u2600";
}

// Bascule une couche Folium par son ID JS (variable globale dans le contentWindow)
function basculeLayerParId(idJs, visible) {
    if (!idJs) return;
    avecCarte(function(map) {
        var win = getIframeWin();
        if (!win) return;
        var layer = win[idJs];
        if (!layer) return;
        if (visible) {
            if (!map.hasLayer(layer)) map.addLayer(layer);
        } else {
            if (map.hasLayer(layer)) map.removeLayer(layer);
        }
    });
}

// Compatibilite avec l'ancien appel par nom (redirige vers ID)
function basculeLayerParNom(nomCouche, visible) {
    if (nomCouche === NOM_CONTOURS) basculeLayerParId(ID_FG_CONTOURS, visible);
    else if (nomCouche === NOM_QUALITE) basculeLayerParId(ID_FG_QUALITE, visible);
    else if (nomCouche === NOM_LABELS)  basculeLayerParId(ID_FG_LABELS, visible);
}

document.getElementById("btn-contours").addEventListener("click", function() {
    etatContours = !etatContours;
    basculeLayerParNom(NOM_CONTOURS, etatContours);
    this.classList.toggle("actif", etatContours);
});
document.getElementById("btn-qualite").addEventListener("click", function() {
    etatQualite = !etatQualite;
    basculeLayerParNom(NOM_QUALITE, etatQualite);
    this.classList.toggle("actif", etatQualite);
});
document.getElementById("btn-labels").addEventListener("click", function() {
    etatLabels = !etatLabels;
    basculeLayerParNom(NOM_LABELS, etatLabels);
    this.classList.toggle("actif", etatLabels);
});

// Zoom / filtres
function resetInfo() {
    document.getElementById("filtre-info").style.display = "none";
}

function resetZoom() {
    avecCarte(function(map) {
        map.setView([""" + centre_lat_str + """, """ + centre_lon_str + """], 12, { animate: true, duration: 1.0 });
    });
}

// Filtre station : zoom sur la station selectionnee
document.getElementById("f-station").addEventListener("change", function() {
    var nom = this.value;
    resetInfo();
    if (!nom) { resetZoom(); return; }
    var st = stationsDash.find(function(s) { return s.nom === nom; });
    if (!st) return;
    avecCarte(function(map) {
        map.flyTo([st.lat, st.lon], 15, { animate: true, duration: 1.5 });
    });
});

// Filtre commune : zoom sur la bbox de la commune selectionnee
document.getElementById("f-commune").addEventListener("change", function() {
    var nom = this.value;
    resetInfo();
    if (!nom) { resetZoom(); return; }
    var cd = communesDash[nom];
    if (!cd) return;
    avecCarte(function(map) {
        map.fitBounds(
            [[cd.lat_min, cd.lon_min], [cd.lat_max, cd.lon_max]],
            { padding: [30, 30], animate: true, duration: 1.2 }
        );
    });
    var info = document.getElementById("filtre-info");
    info.style.display = "flex";
    document.getElementById("fi-nom").textContent = cd.station || nom;
    var ve = document.getElementById("fi-val");
    ve.style.color = cd.couleur || "#fff";
    ve.textContent = (cd.pm25 !== null && cd.pm25 !== undefined) ? cd.pm25 + " \u00b5g/m\u00b3" : "N/D";
    document.getElementById("fi-qualite").textContent = cd.qualite ? "\u2014 " + cd.qualite : "";
});

// Reset general
document.getElementById("btn-reset").addEventListener("click", function() {
    document.getElementById("f-station").value = "";
    document.getElementById("f-commune").value = "";
    resetInfo();
    resetZoom();
    if (!etatContours) document.getElementById("btn-contours").click();
    if (!etatQualite)  document.getElementById("btn-qualite").click();
    if (!etatLabels)   document.getElementById("btn-labels").click();
});

"""

    page += '''


// ── STATISTIQUES ──────────────────────────────────────────────
var chartCourbe   = null;
var chartBarres   = null;
var chartCommunes = null;

function couleurPM25js(v) {
    if (v <= 5)  return "#00e676";
    if (v <= 15) return "#ff9800";
    return "#f44336";
}

function initCharts() {
    var isDark = document.documentElement.getAttribute("data-theme") !== "light";
    var textColor = isDark ? "rgba(255,255,255,0.6)" : "rgba(0,0,0,0.6)";
    var gridColor = isDark ? "rgba(255,255,255,0.07)" : "rgba(0,0,0,0.07)";
    Chart.defaults.color = textColor;

    var stationFiltre = document.getElementById("stats-station") ?
        document.getElementById("stats-station").value : "";

    // Graphique 1 : Courbe temporelle
    var stationsAff = stationFiltre ?
        historiqueStats.filter(function(s){ return s.nom === stationFiltre; }) :
        historiqueStats.slice(0, 5);

    var labelsTemps = stationsAff.length > 0 ?
        stationsAff[0].dates.map(function(d){ return d.substring(5,16); }) : [];

    var couleurs = ["#00e676","#ff9800","#f44336","#00bcd4","#7f77dd","#ffeb3b","#e91e63","#4caf50"];
    var datasetsTemps = stationsAff.map(function(s, i) {
        return {
            label: s.nom.substring(0,22),
            data: s.valeurs,
            borderColor: couleurs[i % couleurs.length],
            backgroundColor: "transparent",
            tension: 0.3, pointRadius: 2, borderWidth: 1.5
        };
    });

    if (chartCourbe) chartCourbe.destroy();
    var ctx1 = document.getElementById("chart-courbe");
    if (ctx1) {
        chartCourbe = new Chart(ctx1, {
            type: "line",
            data: { labels: labelsTemps, datasets: datasetsTemps },
            options: {
                responsive: true,
                plugins: { legend: { position: "bottom", labels: { boxWidth: 10, font: { size: 9 } } } },
                scales: {
                    y: { title: { display: true, text: "µg/m³" }, grid: { color: gridColor } },
                    x: { ticks: { maxTicksLimit: 8, maxRotation: 30, font: { size: 9 } }, grid: { color: gridColor } }
                }
            }
        });
    }

    // Graphique 2 : Barres comparatives stations
    var stationsFiltrees = stationFiltre ?
        stationsDash.filter(function(s){ return s.nom === stationFiltre; }) : stationsDash;
    var nomsS = stationsFiltrees.map(function(s){ return s.nom.substring(0,18); });
    var valeursS = stationsFiltrees.map(function(s){ return s.pm25; });
    var couleursS = stationsFiltrees.map(function(s){ return couleurPM25js(s.pm25); });

    if (chartBarres) chartBarres.destroy();
    var ctx2 = document.getElementById("chart-barres");
    if (ctx2) {
        chartBarres = new Chart(ctx2, {
            type: "bar",
            data: { labels: nomsS, datasets: [{ label: "PM2.5 µg/m³", data: valeursS, backgroundColor: couleursS, borderRadius: 4 }] },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    y: { title: { display: true, text: "µg/m³" }, grid: { color: gridColor } },
                    x: { ticks: { font: { size: 9 }, maxRotation: 45 }, grid: { display: false } }
                }
            }
        });
    }

    // Graphique 3 : PM2.5 par commune
    var nomsC = Object.keys(communesDash).sort();
    var valeursC = nomsC.map(function(n){ return communesDash[n].pm25 || 0; });
    var couleursC = valeursC.map(function(v){ return couleurPM25js(v); });

    if (chartCommunes) chartCommunes.destroy();
    var ctx3 = document.getElementById("chart-communes");
    if (ctx3) {
        chartCommunes = new Chart(ctx3, {
            type: "bar",
            data: { labels: nomsC, datasets: [{ label: "PM2.5 µg/m³", data: valeursC, backgroundColor: couleursC, borderRadius: 4 }] },
            options: {
                indexAxis: "y",
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    x: { title: { display: true, text: "µg/m³" }, grid: { color: gridColor } },
                    y: { ticks: { font: { size: 9 } }, grid: { display: false } }
                }
            }
        });
    }
}

function filtrerStats() {
    if (chartCourbe)   chartCourbe.destroy();
    if (chartBarres)   chartBarres.destroy();
    if (chartCommunes) chartCommunes.destroy();
    initCharts();
}

'''

    page += '</script></body></html>'

    return page
