import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import backend

st.set_page_config(
    page_title="ValueGuard",
    page_icon="favicon_valueguard.png",
    layout="wide",
    # "auto": Streamlit decide según el ancho de pantalla — abierta en escritorio,
    # cerrada en móvil (donde nuestra barra lateral pasa a ser un panel deslizante).
    initial_sidebar_state="auto",
)

COLOR_TEXTO_PRINCIPAL = "#0F172A"
COLOR_TEXTO_SECUNDARIO = "#475569"
COLOR_TEXTO_TERCIARIO = "#64748B"
COLOR_AZUL = "#035AA6"
COLOR_AZUL_OSCURO = "#02426F"
COLOR_AZUL_TINTE = "#E6F0FA"
COLOR_AMARILLO = "#FDC900"
COLOR_NAVY_MARCA = "#00254A"
COLOR_NAVY_PROFUNDO = "#00152B"
COLOR_EXITO = "#16A34A"
COLOR_RIESGO = "#D97706"
COLOR_NEUTRO = "#64748B"
COLOR_BORDE = "#E2E8F0"
COLOR_FONDO = "#F5F7FA"

HORIZONTES_SEMANAS = [13, 26, 52, 104]
HORIZONTE_POR_DEFECTO = 52
SEMANAS_HISTORIAL = 102

ETIQUETAS_HORIZONTE = {
    13: "13 semanas (1 trimestre)",
    26: "26 semanas (medio año)",
    52: "52 semanas (1 año)",
    104: "104 semanas (2 años)",
}

SECCIONES = ["Resultados", "Clientes a contactar", "Explicación", "Consulta por cliente"]

CLAVES_RESULTADO = [
    'tabla_resultado',
    'pct_cartera_protegida',
    'retorno_incremental_total',
    'presupuesto',
    'horizonte_semanas',
    'coste_por_hogar',
    'pct_cartera_protegida_igual',
    'retorno_incremental_total_igual',
    'excedente_presupuesto_total',
    'cliente_buscado',
    'seccion',
]

FONDO_CAPAS = (
    "radial-gradient(circle at 8% 0%, rgba(0,37,74,0.10) 0%, rgba(0,37,74,0) 42%), "
    "radial-gradient(circle at 100% 18%, rgba(253,201,0,0.12) 0%, rgba(253,201,0,0) 38%)"
)


def _rgb(color_hex):
    color_hex = color_hex.lstrip("#")
    return ", ".join(str(int(color_hex[i:i + 2], 16)) for i in (0, 2, 4))


RGB_NAVY_MARCA = _rgb(COLOR_NAVY_MARCA)
RGB_AMARILLO = _rgb(COLOR_AMARILLO)

# Red neuronal animada de fondo (canvas + JS), con un pequeño parallax al mover el ratón.
# Se inyecta como componente aparte (components.html) porque Streamlit no ejecuta <script>
# dentro de st.markdown; el CSS de más abajo fija ese iframe a pantalla completa, por detrás
# de todo el contenido y sin capturar clics (pointer-events: none).
HTML_RED_FONDO = f"""
<!doctype html>
<html><head><meta charset="utf-8"><style>
  html, body {{ margin:0; padding:0; width:100%; height:100%; overflow:hidden; background:transparent; }}
  canvas {{ display:block; }}
</style></head>
<body>
<canvas id="vg-bg"></canvas>
<script>
(function () {{
  var canvas = document.getElementById('vg-bg');
  var ctx = canvas.getContext('2d');
  var COLOR_NAVY = '{RGB_NAVY_MARCA}';
  var COLOR_GOLD = '{RGB_AMARILLO}';
  var W, H, DPR;
  var nodos = [];
  var N = 58;
  var DIST_MAX = 150;
  var mouse = {{ x: 0, y: 0 }};
  var mouseTarget = {{ x: 0, y: 0 }};
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function resize() {{
    DPR = Math.min(window.devicePixelRatio || 1, 2);
    W = window.innerWidth; H = window.innerHeight;
    canvas.width = W * DPR; canvas.height = H * DPR;
    canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  }}

  function crearNodos() {{
    nodos = [];
    for (var i = 0; i < N; i++) {{
      var esOro = Math.random() < 0.12;
      nodos.push({{
        x: Math.random() * W, y: Math.random() * H,
        vx: (Math.random() - 0.5) * 0.12, vy: (Math.random() - 0.5) * 0.12,
        r: esOro ? (2.6 + Math.random() * 1.6) : (1.6 + Math.random() * 1.4),
        oro: esOro, profundidad: 0.5 + Math.random() * 0.9,
      }});
    }}
  }}

  // El ratón real se mueve sobre la página de Streamlit (el iframe no captura clics),
  // así que escuchamos en window.parent; si el navegador lo bloquea por origen,
  // la red sigue funcionando, solo que sin parallax.
  function escucharRaton() {{
    try {{
      window.parent.document.addEventListener('mousemove', function (e) {{
        mouseTarget.x = (e.clientX / window.parent.innerWidth - 0.5) * 2;
        mouseTarget.y = (e.clientY / window.parent.innerHeight - 0.5) * 2;
      }}, {{ passive: true }});
    }} catch (err) {{
      window.addEventListener('mousemove', function (e) {{
        mouseTarget.x = (e.clientX / W - 0.5) * 2;
        mouseTarget.y = (e.clientY / H - 0.5) * 2;
      }}, {{ passive: true }});
    }}
  }}

  function paso() {{
    mouse.x += (mouseTarget.x - mouse.x) * 0.05;
    mouse.y += (mouseTarget.y - mouse.y) * 0.05;
    for (var i = 0; i < nodos.length; i++) {{
      var n = nodos[i];
      n.x += n.vx; n.y += n.vy;
      if (n.x < -20) n.x = W + 20; else if (n.x > W + 20) n.x = -20;
      if (n.y < -20) n.y = H + 20; else if (n.y > H + 20) n.y = -20;
    }}
    ctx.clearRect(0, 0, W, H);
    var MAXD = 16;
    for (var i = 0; i < nodos.length; i++) {{
      var a = nodos[i];
      var ax = a.x + mouse.x * MAXD * a.profundidad, ay = a.y + mouse.y * MAXD * a.profundidad;
      for (var j = i + 1; j < nodos.length; j++) {{
        var b = nodos[j];
        var bx = b.x + mouse.x * MAXD * b.profundidad, by = b.y + mouse.y * MAXD * b.profundidad;
        var dx = ax - bx, dy = ay - by, dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < DIST_MAX) {{
          var op = (1 - dist / DIST_MAX) * 0.42;
          ctx.strokeStyle = 'rgba(' + COLOR_NAVY + ',' + op.toFixed(3) + ')';
          ctx.lineWidth = 1;
          ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(bx, by); ctx.stroke();
        }}
      }}
    }}
    for (var i = 0; i < nodos.length; i++) {{
      var n = nodos[i];
      var nx = n.x + mouse.x * MAXD * n.profundidad, ny = n.y + mouse.y * MAXD * n.profundidad;
      ctx.beginPath(); ctx.arc(nx, ny, n.r, 0, Math.PI * 2);
      ctx.fillStyle = n.oro ? 'rgba(' + COLOR_GOLD + ',0.85)' : 'rgba(' + COLOR_NAVY + ',0.5)';
      ctx.fill();
    }}
    if (!reduceMotion) requestAnimationFrame(paso);
  }}

  window.addEventListener('resize', resize);
  resize(); crearNodos(); escucharRaton(); paso();
}})();
</script>
</body></html>
"""

components.html(HTML_RED_FONDO, height=0, scrolling=False)

# Velo semitransparente de fondo (solo se ve en móvil, con la barra lateral abierta —
# ver CSS más abajo). Es HTML normal insertado con st.markdown, así que su atributo
# onclick funciona sin problema (a diferencia de las etiquetas <script>, que Streamlit
# no ejecuta dentro de st.markdown). Abrir/cerrar la barra es una clase propia en <body>
# (JS_TOGGLE_SIDEBAR, ver más abajo) — no depende de ningún control interno de Streamlit.
st.markdown(
    '<div class="vg-velo" onclick="document.body.classList.remove(\'vg-sidebar-abierta\')"></div>',
    unsafe_allow_html=True,
)

JS_TOGGLE_SIDEBAR = "document.body.classList.toggle('vg-sidebar-abierta')"
JS_CERRAR_SIDEBAR = "document.body.classList.remove('vg-sidebar-abierta')"

st.markdown(f"""
<style>
    html, body {{ font-size: 15px; }}

    /* Red neuronal de fondo: el iframe del componente se fija a toda la pantalla,
       por detrás del contenido, y no captura clics (pointer-events: none). Si en el
       futuro se añade otro componente con iframe, este selector habría que acotarlo. */
    iframe {{
        position: fixed !important;
        top: 0 !important; left: 0 !important;
        width: 100vw !important; height: 100vh !important;
        z-index: 0 !important;
        border: none !important;
        pointer-events: none !important;
    }}

    [data-testid="stAppViewContainer"] {{
        color: {COLOR_TEXTO_SECUNDARIO};
        background-color: transparent;
        background-image: {FONDO_CAPAS};
        background-repeat: no-repeat, no-repeat;
        background-attachment: fixed, fixed;
        background-position: center top;
        position: relative;
        z-index: 1;
    }}
    [data-testid="stApp"] {{ background-color: {COLOR_FONDO}; }}
    [data-testid="stHeader"] {{ background: transparent !important; }}
    [data-testid="stToolbar"],
    [data-testid="stToolbarActions"],
    [data-testid="stAppDeployButton"],
    [data-testid="stStatusWidget"],
    [data-testid="stDecoration"],
    [data-testid="stMainMenu"],
    .stAppDeployButton,
    .stDeployButton,
    #MainMenu,
    footer {{ display: none !important; visibility: hidden !important; }}
    [data-testid="stAppViewBlockContainer"],
    .block-container {{ padding-top: 2.5rem !important; }}

    h1 {{
        font-size: 28px !important; font-weight: 700 !important; color: {COLOR_TEXTO_PRINCIPAL} !important;
        margin-bottom: 4px !important;
    }}
    h1::after {{
        content: ""; display: block; width: 56px; height: 4px; margin-top: 10px;
        background: {COLOR_AMARILLO}; border-radius: 2px;
    }}
    h2, h3 {{ color: {COLOR_TEXTO_PRINCIPAL} !important; }}

    [data-testid="stSidebar"] {{
        background-color: #FFFFFF;
        border-right: 1px solid {COLOR_BORDE};
        border-top: 4px solid {COLOR_AMARILLO};
        position: relative;
    }}
    [data-testid="stSidebar"] > div:first-child {{ height: 100vh; overflow-y: auto; }}
    [data-testid="stSidebarUserContent"] {{ padding-top: 1.25rem; padding-left: 1.4rem; padding-right: 1.4rem; }}
    /* Los controles nativos de Streamlit para abrir/cerrar la barra se ocultan siempre: en
       escritorio no hacen falta (la barra queda fija) y en móvil no se usan — la apertura y
       cierre del panel la controla directamente nuestra propia burbuja de parámetros (más
       abajo), con una clase en <body>, sin depender del mecanismo interno de Streamlit. */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarResizeHandle"],
    [data-testid="stSidebarNavCollapseIcon"] {{ display: none !important; }}

    /* Escritorio/tablet ancho: la barra lateral se mantiene siempre visible, como hasta
       ahora — y no se muestra la burbuja de parámetros (es solo móvil). */
    @media (min-width: 769px) {{
        [data-testid="stSidebar"] {{
            width: 300px !important;
            min-width: 300px !important;
            max-width: 300px !important;
            transform: none !important;
            visibility: visible !important;
            margin-left: 0 !important;
        }}
        [data-testid="stSidebar"][aria-expanded="false"] {{
            transform: none !important;
            visibility: visible !important;
            margin-left: 0 !important;
        }}
        .vg-chip-parametros, .vg-velo, .vg-drawer-cerrar {{ display: none !important; }}
    }}

    /* Móvil: la barra lateral deja de estar fija y pasa a ser un panel deslizante (drawer)
       que no empuja el contenido, priorizando que el contenido de la página ocupe toda la
       pantalla. Se controla con una clase propia en <body> (no con el mecanismo interno de
       Streamlit, que en algunas versiones no reacciona a un clic disparado por JS) — así que
       abrir/cerrar es 100% nuestro y no depende de qué versión de Streamlit esté corriendo. */
    @media (max-width: 768px) {{
        [data-testid="stSidebar"] {{
            width: 82vw !important;
            min-width: 260px !important;
            max-width: 340px !important;
            box-shadow: 4px 0 24px rgba(0,0,0,0.18);
            transform: translateX(-100%) !important;
            visibility: hidden !important;
            transition: transform .25s ease;
        }}
        body.vg-sidebar-abierta [data-testid="stSidebar"] {{
            transform: translateX(0) !important;
            visibility: visible !important;
        }}

        .vg-chip-parametros {{
            display: flex; align-items: center; justify-content: space-between; gap: 8px;
            background: #FFFFFF; border: 1px solid {COLOR_BORDE}; border-radius: 999px;
            padding: 9px 14px; margin: 4px 0 18px 0; font-size: 12.5px; color: {COLOR_TEXTO_SECUNDARIO};
            box-shadow: 0 1px 4px rgba(0,0,0,0.06); cursor: pointer;
        }}
        .vg-chip-parametros b {{ color: {COLOR_NAVY_MARCA}; }}
        .vg-chip-parametros .vg-chip-flecha {{ color: {COLOR_AMARILLO}; font-weight: 900; }}

        /* Velo semitransparente detrás del panel: solo visible (y solo capta toques) con la
           barra abierta; tocarlo también cierra el panel. */
        .vg-velo {{
            position: fixed; inset: 0; background: rgba(15,23,42,0.35);
            opacity: 0; pointer-events: none; transition: opacity .25s ease;
            z-index: 999998;
        }}
        body.vg-sidebar-abierta .vg-velo {{ opacity: 1; pointer-events: auto; }}

        /* Botón "✕" dentro de la propia barra lateral, para cerrarla sin tener que tocar
           fuera del panel. */
        .vg-drawer-cerrar {{
            position: absolute; top: 10px; right: 14px;
            font-size: 15px; color: {COLOR_TEXTO_TERCIARIO}; cursor: pointer; z-index: 2;
        }}
    }}

    /* Botón "Inicio": única acción secundaria de la barra lateral (la otra es "Calcular
       reparto", type="primary") — se le da un estilo tipo "ghost", más ligero. */
    [data-testid="stSidebar"] button[kind="secondary"],
    [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] {{
        background-color: transparent !important;
        border: 1px solid {COLOR_NAVY_MARCA} !important;
        padding: 4px 14px !important;
    }}
    [data-testid="stSidebar"] button[kind="secondary"] p,
    [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] p {{
        color: {COLOR_NAVY_MARCA} !important;
        font-size: 13px !important;
    }}
    [data-testid="stSidebar"] button[kind="secondary"]:hover,
    [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover {{
        background-color: {COLOR_AZUL_TINTE} !important;
        border-color: {COLOR_NAVY_MARCA} !important;
    }}

    /* Inputs de la barra lateral: borde y foco en navy de marca */
    [data-testid="stSidebar"] [data-testid="stNumberInput"] div[data-baseweb="input"],
    [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
        border-radius: 8px !important;
        border-color: {COLOR_BORDE} !important;
    }}
    [data-testid="stSidebar"] [data-testid="stNumberInput"] div[data-baseweb="input"]:focus-within,
    [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within {{
        border-color: {COLOR_NAVY_MARCA} !important;
        box-shadow: 0 0 0 3px {COLOR_AZUL_TINTE} !important;
    }}
    [data-testid="stSidebar"] .vg-seccion {{ margin: 2px 0 10px 0; }}

    [data-testid="stWidgetLabel"] p {{ font-size: 12px !important; font-weight: 500 !important; color: {COLOR_TEXTO_TERCIARIO} !important; text-transform: none; }}
    [data-testid="stMarkdownContainer"] p {{ font-size: 14px !important; color: {COLOR_TEXTO_SECUNDARIO} !important; }}
    [data-testid="stDataFrame"] {{ font-size: 14px !important; }}

    .stButton button[kind="primary"],
    button[data-testid="stBaseButton-primary"],
    button[data-testid="baseButton-primary"] {{
        background-color: {COLOR_NAVY_MARCA} !important;
        border: 1px solid {COLOR_NAVY_MARCA} !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        font-weight: 600 !important;
    }}
    .stButton button[kind="primary"] p,
    .stButton button[kind="primary"] div,
    .stButton button[kind="primary"] span,
    button[data-testid="stBaseButton-primary"] p,
    button[data-testid="stBaseButton-primary"] div,
    button[data-testid="stBaseButton-primary"] span,
    button[data-testid="baseButton-primary"] p,
    button[data-testid="baseButton-primary"] div,
    button[data-testid="baseButton-primary"] span {{
        color: #FFFFFF !important;
        font-size: 14px !important;
        font-weight: 600 !important;
    }}
    .stButton button[kind="primary"]:hover,
    button[data-testid="stBaseButton-primary"]:hover,
    button[data-testid="baseButton-primary"]:hover {{
        background-color: {COLOR_NAVY_PROFUNDO} !important;
        border-color: {COLOR_NAVY_PROFUNDO} !important;
    }}
    .stButton button[kind="primary"]:focus,
    .stButton button[kind="primary"]:active,
    button[data-testid="stBaseButton-primary"]:focus,
    button[data-testid="stBaseButton-primary"]:active,
    button[data-testid="baseButton-primary"]:focus,
    button[data-testid="baseButton-primary"]:active {{
        background-color: {COLOR_NAVY_PROFUNDO} !important;
        border-color: {COLOR_NAVY_PROFUNDO} !important;
        box-shadow: 0 0 0 3px rgba(253,201,0,0.28) !important;
    }}

    .stButton button[kind="secondary"],
    button[data-testid="stBaseButton-secondary"],
    button[data-testid="baseButton-secondary"],
    [data-testid="stDownloadButton"] button,
    [data-testid="stFormSubmitButton"] button {{
        background-color: #FFFFFF !important;
        border: 1px solid {COLOR_BORDE} !important;
        border-radius: 8px !important;
        box-shadow: none !important;
    }}
    .stButton button[kind="secondary"] p,
    button[data-testid="stBaseButton-secondary"] p,
    button[data-testid="baseButton-secondary"] p,
    [data-testid="stDownloadButton"] button p,
    [data-testid="stFormSubmitButton"] button p {{
        color: {COLOR_TEXTO_PRINCIPAL} !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }}
    .stButton button[kind="secondary"]:hover,
    button[data-testid="stBaseButton-secondary"]:hover,
    button[data-testid="baseButton-secondary"]:hover,
    [data-testid="stDownloadButton"] button:hover,
    [data-testid="stFormSubmitButton"] button:hover {{
        border-color: {COLOR_AZUL} !important;
        background-color: {COLOR_AZUL_TINTE} !important;
    }}

    [data-testid="stRadio"] > div[role="radiogroup"] {{
        display: flex;
        flex-direction: row;
        gap: 28px;
        border-bottom: 1px solid {COLOR_BORDE};
        margin-bottom: 4px;
    }}
    [data-testid="stRadio"] div[role="radiogroup"] > label {{
        margin: 0 !important;
        padding: 10px 2px !important;
        border-bottom: 2px solid transparent;
        cursor: pointer;
        background: transparent !important;
    }}
    [data-testid="stRadio"] div[role="radiogroup"] label div:empty,
    [data-testid="stRadio"] div[role="radiogroup"] label div:has(> div:empty:only-child) {{ display: none !important; }}
    [data-testid="stRadio"] div[role="radiogroup"] > label p {{
        font-size: 14px !important;
        font-weight: 500 !important;
        color: {COLOR_TEXTO_TERCIARIO} !important;
        white-space: nowrap;
    }}
    [data-testid="stRadio"] div[role="radiogroup"] > label:hover p {{ color: {COLOR_TEXTO_SECUNDARIO} !important; }}
    [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked),
    [data-testid="stRadio"] div[role="radiogroup"] > label[data-selected="true"],
    [data-testid="stRadio"] div[role="radiogroup"] > label[aria-checked="true"] {{ border-bottom-color: {COLOR_AZUL}; }}
    [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) p,
    [data-testid="stRadio"] div[role="radiogroup"] > label[data-selected="true"] p,
    [data-testid="stRadio"] div[role="radiogroup"] > label[aria-checked="true"] p {{
        color: {COLOR_TEXTO_PRINCIPAL} !important;
        font-weight: 600 !important;
    }}

    .vg-tarjeta {{
        background: #FFFFFF;
        border: 1px solid {COLOR_BORDE};
        border-top: 3px solid {COLOR_AMARILLO};
        border-radius: 12px;
        padding: 22px 22px 20px;
        height: 100%;
        box-shadow: 0 4px 14px rgba(0,37,74,0.08);
        transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
    }}
    .vg-tarjeta:hover {{
        transform: translateY(-4px);
        box-shadow: 0 14px 30px rgba(0,37,74,0.16);
        border-color: #BFD6EC;
    }}
    .vg-etiqueta {{
        font-size: 12px; font-weight: 600; color: {COLOR_TEXTO_TERCIARIO};
        text-transform: uppercase; letter-spacing: 0.03em;
    }}
    .vg-cifra {{ font-size: 30px; font-weight: 800; margin-top: 6px; font-variant-numeric: tabular-nums; line-height: 1.15; }}
    .vg-nota {{ font-size: 13px; margin-top: 6px; line-height: 1.5; }}
    .vg-seccion {{
        font-size: 12px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
        color: {COLOR_NAVY_MARCA}; margin: 30px 0 14px 0;
        display: flex; align-items: center; gap: 8px;
    }}
    .vg-seccion::before {{
        content: ""; width: 14px; height: 3px; background: {COLOR_AMARILLO};
        border-radius: 2px; display: inline-block; flex-shrink: 0;
    }}

    .vg-hero {{
        position: relative;
        overflow: hidden;
        border-radius: 16px;
        padding: 34px 36px;
        background: linear-gradient(120deg, {COLOR_NAVY_PROFUNDO} 0%, {COLOR_NAVY_MARCA} 46%, #04437A 100%);
        box-shadow: 0 16px 40px rgba(0,37,74,0.28);
    }}
    .vg-hero::after {{
        content: ""; position: absolute; top: -40%; right: -10%; width: 70%; height: 180%;
        background: radial-gradient(circle, rgba(253,201,0,0.16) 0%, rgba(253,201,0,0) 60%);
        pointer-events: none;
    }}
    .vg-hero-red {{
        position: absolute; top: 0; left: -8%; width: 116%; height: 100%;
        opacity: 0.5; animation: vg-deriva 26s ease-in-out infinite alternate;
    }}
    @keyframes vg-deriva {{ from {{ transform: translate3d(0,0,0); }} to {{ transform: translate3d(-56px,-10px,0); }} }}
    .vg-hero-contenido {{ position: relative; z-index: 1; max-width: 780px; }}
    .vg-hero-kicker {{
        display: inline-block; font-size: 12px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
        color: {COLOR_NAVY_PROFUNDO}; background: {COLOR_AMARILLO}; padding: 5px 12px; border-radius: 999px;
        margin-bottom: 14px;
    }}
    .vg-hero-titulo {{ font-size: 27px; font-weight: 700; color: #FFFFFF; line-height: 1.25; }}
    .vg-hero-sub {{ font-size: 15px; color: #D6E6F5; margin-top: 12px; line-height: 1.6; }}
    .vg-hero-sub strong {{ color: {COLOR_AMARILLO}; }}

    .vg-chip {{
        display: inline-block; padding: 4px 10px; border-radius: 999px;
        font-size: 12px; font-weight: 600;
    }}
    .vg-ficha {{
        background: #FFFFFF; border: 1px solid {COLOR_BORDE}; border-top: 3px solid {COLOR_AMARILLO}; border-radius: 12px; padding: 24px;
        box-shadow: 0 4px 14px rgba(0,37,74,0.08);
    }}
    .vg-dato {{ font-size: 12px; font-weight: 500; color: {COLOR_TEXTO_TERCIARIO}; }}
    .vg-dato-valor {{ font-size: 20px; font-weight: 700; color: {COLOR_TEXTO_PRINCIPAL}; margin-top: 2px; }}

    @media (prefers-reduced-motion: reduce) {{
        .vg-hero-red {{ animation: none; }}
        .vg-tarjeta {{ transition: none; }}
    }}
</style>
""", unsafe_allow_html=True)

CONFIG_PLOTLY = {"displayModeBar": False, "displaylogo": False, "staticPlot": False}

GRUPOS_TENDENCIA = {
    "Valor en riesgo": COLOR_RIESGO,
    "Valor en crecimiento": COLOR_AZUL,
    "Sin tendencia": COLOR_NEUTRO,
}

NOMBRES_COLUMNAS_SEGMENTOS = {
    'cuadrante': 'Segmento',
    'n_hogares': 'Clientes totales',
    'hogares_cubiertos': 'Clientes cubiertos',
    'pct_hogares_cubiertos': '% cubierto',
    'presupuesto_asignado': 'Presupuesto asignado (€)',
    'techo_segmento': 'Límite máximo (€)',
    'prioridad': 'Prioridad',
}

NOMBRES_COLUMNAS_HOGARES = {
    'household_key': 'ID de cliente',
    'clv_futuro_predicho': 'Valor futuro estimado (€)',
    'invertir': '¿Se cubre con el presupuesto?',
}

ETIQUETAS_CORTAS = {
    'Alto valor / Descendente': 'Alto valor ↓',
    'Alto valor / Ascendente': 'Alto valor ↑',
    'Bajo valor / Descendente': 'Bajo valor ↓',
    'Bajo valor / Ascendente': 'Bajo valor ↑',
    'Sin tendencia disponible': 'Sin tendencia',
}

POSICIONES_ETIQUETA = {
    'Alto valor / Descendente': 'bottom center',
    'Alto valor / Ascendente': 'top center',
    'Bajo valor / Descendente': 'top center',
    'Bajo valor / Ascendente': 'bottom center',
    'Sin tendencia disponible': 'middle right',
}

SVG_RED_HERO = (
    '<svg class="vg-hero-red" viewBox="0 0 1200 240" preserveAspectRatio="none" aria-hidden="true">'
    '<g stroke="#7FC4F2" stroke-width="1" fill="none" opacity="0.45">'
    '<path d="M60 42 L250 130 L120 210 M250 130 L470 60 L690 140 M470 60 L520 200 M690 140 L900 52 L1140 128'
    ' M900 52 L860 206 M1140 128 L1050 214 M250 130 L520 200 M690 140 L860 206 M120 210 L520 200"/>'
    '</g><g fill="#BFE3FB">'
    '<circle cx="60" cy="42" r="3.4" opacity="0.85"><animate attributeName="r" values="3.4;5.2;3.4" dur="5s" repeatCount="indefinite"/></circle>'
    '<circle cx="250" cy="130" r="4.4" opacity="0.9"><animate attributeName="r" values="4.4;6.4;4.4" dur="6.5s" repeatCount="indefinite"/></circle>'
    '<circle cx="470" cy="60" r="3.6" opacity="0.8"><animate attributeName="opacity" values="0.8;0.35;0.8" dur="4.5s" repeatCount="indefinite"/></circle>'
    '<circle cx="690" cy="140" r="4.6" opacity="0.9"><animate attributeName="r" values="4.6;6.8;4.6" dur="7.5s" repeatCount="indefinite"/></circle>'
    '<circle cx="900" cy="52" r="3.4" opacity="0.85"><animate attributeName="opacity" values="0.85;0.4;0.85" dur="5.5s" repeatCount="indefinite"/></circle>'
    '<circle cx="1140" cy="128" r="4" opacity="0.85"><animate attributeName="r" values="4;5.8;4" dur="6s" repeatCount="indefinite"/></circle>'
    '<circle cx="120" cy="210" r="3" opacity="0.7"/>'
    '<circle cx="520" cy="200" r="3.6" opacity="0.75"><animate attributeName="opacity" values="0.75;0.3;0.75" dur="6.2s" repeatCount="indefinite"/></circle>'
    '<circle cx="860" cy="206" r="3.2" opacity="0.7"/>'
    '<circle cx="1050" cy="214" r="2.8" opacity="0.65"/>'
    '</g><g fill="#FDC900">'
    '<circle cx="470" cy="60" r="4.4" opacity="0.9"><animate attributeName="r" values="4.4;6.6;4.4" dur="5.8s" repeatCount="indefinite"/></circle>'
    '<circle cx="900" cy="52" r="4.2" opacity="0.9"><animate attributeName="r" values="4.2;6.2;4.2" dur="6.4s" repeatCount="indefinite"/></circle>'
    '</g></svg>'
)


def euros(valor, decimales=0):
    texto = f"{valor:,.{decimales}f}"
    texto = texto.replace(",", "@").replace(".", ",").replace("@", ".")
    return f"{texto} €"


def miles(valor):
    return f"{int(valor):,}".replace(",", ".")


def porcentaje(valor, decimales=1, con_signo=False):
    formato = f"{{:+.{decimales}f}}" if con_signo else f"{{:.{decimales}f}}"
    return formato.format(valor).replace(".", ",") + " %"


def grupo_tendencia(nombre_segmento):
    if "Descendente" in nombre_segmento:
        return "Valor en riesgo"
    if "Ascendente" in nombre_segmento:
        return "Valor en crecimiento"
    return "Sin tendencia"


def etiqueta_corta(nombre_segmento):
    return ETIQUETAS_CORTAS.get(nombre_segmento, nombre_segmento.replace(" / ", " "))


def tarjeta_kpi(etiqueta, cifra, nota=None, color_nota=COLOR_TEXTO_TERCIARIO, color_cifra=COLOR_NAVY_MARCA, color_borde=None):
    nota_html = f"<div class='vg-nota' style='color:{color_nota};'>{nota}</div>" if nota else ""
    estilo_borde = f" style='border-top-color:{color_borde};'" if color_borde else ""
    st.markdown(f"""
    <div class="vg-tarjeta"{estilo_borde}>
        <div class="vg-etiqueta">{etiqueta}</div>
        <div class="vg-cifra" style="color:{color_cifra};">{cifra}</div>
        {nota_html}
    </div>
    """, unsafe_allow_html=True)


def encabezado_bloque(titulo, subtitulo):
    st.markdown(f"<div style='font-size:15px; font-weight:600; color:{COLOR_TEXTO_PRINCIPAL};'>{titulo}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:13px; color:{COLOR_TEXTO_SECUNDARIO}; margin-bottom:12px;'>{subtitulo}</div>", unsafe_allow_html=True)


def titulo_seccion(texto):
    st.markdown(f"<div class='vg-seccion'>{texto}</div>", unsafe_allow_html=True)


def mapa_cartera(tabla_base):
    datos = tabla_base.copy()
    datos['grupo'] = datos['cuadrante'].apply(grupo_tendencia)
    datos['etiqueta'] = datos['cuadrante'].apply(etiqueta_corta)
    datos['posicion'] = datos['cuadrante'].map(POSICIONES_ETIQUETA).fillna('top center')
    datos['valor_total_texto'] = datos['valor_futuro_total'].apply(lambda v: euros(v))
    datos['valor_medio_texto'] = datos['valor_futuro_medio'].apply(lambda v: euros(v, 2))
    limite_x = datos['valor_futuro_medio'].max() * 1.18
    limite_y = datos['n_hogares'].max() * 1.22

    figura = px.scatter(
        datos,
        x='valor_futuro_medio',
        y='n_hogares',
        size='valor_futuro_total',
        color='grupo',
        text='etiqueta',
        size_max=54,
        color_discrete_map=GRUPOS_TENDENCIA,
        category_orders={'grupo': list(GRUPOS_TENDENCIA.keys())},
        custom_data=['cuadrante', 'valor_medio_texto', 'valor_total_texto', 'n_hogares'],
        labels={
            'valor_futuro_medio': 'Valor futuro medio por cliente (€)',
            'n_hogares': 'Clientes en el segmento',
            'grupo': '',
        },
    )
    figura.update_traces(
        textfont=dict(size=12, color=COLOR_TEXTO_SECUNDARIO),
        marker=dict(opacity=0.9, line=dict(color='#FFFFFF', width=2)),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Clientes: %{customdata[3]}<br>"
            "Valor medio por cliente: %{customdata[1]}<br>"
            "Valor futuro del segmento: %{customdata[2]}"
            "<extra></extra>"
        ),
    )
    for traza in figura.data:
        subconjunto = datos[datos['grupo'] == traza.name]
        traza.textposition = list(subconjunto['posicion'])

    figura.update_xaxes(
        range=[0, limite_x],
        tickfont=dict(size=11, color=COLOR_TEXTO_TERCIARIO),
        title_font=dict(size=12, color=COLOR_TEXTO_TERCIARIO),
        title_standoff=12,
        gridcolor=COLOR_BORDE, zeroline=False, automargin=True,
    )
    figura.update_yaxes(
        range=[0, limite_y],
        tickfont=dict(size=11, color=COLOR_TEXTO_TERCIARIO),
        title_font=dict(size=12, color=COLOR_TEXTO_TERCIARIO),
        title_standoff=14,
        gridcolor=COLOR_BORDE, zeroline=False, automargin=True,
    )
    figura.update_layout(
        plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF',
        height=420,
        margin=dict(l=20, r=40, t=40, b=30),
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0,
            font=dict(size=12, color=COLOR_TEXTO_SECUNDARIO),
            title_text='',
        ),
        hoverlabel=dict(bgcolor='#FFFFFF', bordercolor=COLOR_BORDE, font=dict(size=12, color=COLOR_TEXTO_PRINCIPAL)),
    )
    return figura


def grafico_presupuesto(tabla_resultado):
    datos = tabla_resultado.sort_values('presupuesto_asignado', ascending=True).copy()
    datos['grupo'] = datos['cuadrante'].apply(grupo_tendencia)
    datos['texto'] = datos['presupuesto_asignado'].apply(lambda v: euros(v))

    figura = px.bar(
        datos, x='presupuesto_asignado', y='cuadrante', orientation='h',
        text='texto', color='grupo',
        color_discrete_map=GRUPOS_TENDENCIA,
        category_orders={'grupo': list(GRUPOS_TENDENCIA.keys())},
    )
    figura.update_traces(
        textposition='outside',
        textfont=dict(color=COLOR_TEXTO_SECUNDARIO, size=12),
        marker_line=dict(color='#FFFFFF', width=2),
        hovertemplate="<b>%{y}</b><br>Presupuesto asignado: %{text}<extra></extra>",
    )
    figura.update_yaxes(
        automargin=True,
        categoryorder='array',
        categoryarray=list(datos['cuadrante']),
        tickfont=dict(size=13, color=COLOR_TEXTO_SECUNDARIO),
    )
    figura.update_xaxes(tickfont=dict(size=11, color=COLOR_TEXTO_TERCIARIO), gridcolor=COLOR_BORDE)
    figura.update_layout(
        plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF',
        xaxis_title=None, yaxis_title=None,
        height=max(300, 70 * len(datos) + 60),
        bargap=0.55,
        margin=dict(l=10, r=90, t=40, b=30),
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0,
            font=dict(size=12, color=COLOR_TEXTO_SECUNDARIO), title_text='',
        ),
        hoverlabel=dict(bgcolor='#FFFFFF', bordercolor=COLOR_BORDE, font=dict(size=12, color=COLOR_TEXTO_PRINCIPAL)),
    )
    return figura


def grafico_sensibilidad(curva, curva_igual, presupuesto_actual, pct_actual):
    datos = curva.copy()
    datos['presupuesto_texto'] = datos['presupuesto'].apply(lambda v: euros(v))
    datos['pct_texto'] = datos['pct_cartera_protegida'].apply(lambda v: porcentaje(v))

    datos_igual = curva_igual.copy()
    datos_igual['presupuesto_texto'] = datos_igual['presupuesto'].apply(lambda v: euros(v))
    datos_igual['pct_texto'] = datos_igual['pct_cartera_protegida'].apply(lambda v: porcentaje(v))

    figura = px.line(
        datos, x='presupuesto', y='pct_cartera_protegida',
        custom_data=['presupuesto_texto', 'pct_texto'],
    )
    figura.update_traces(
        name='Reparto priorizado', showlegend=True,
        line=dict(color=COLOR_AMARILLO, width=3),
        hovertemplate="<b>Priorizado</b><br>Presupuesto: %{customdata[0]}<br>Cartera protegida: %{customdata[1]}<extra></extra>",
    )
    figura.add_scatter(
        x=datos_igual['presupuesto'], y=datos_igual['pct_cartera_protegida'],
        mode='lines', name='Reparto equitativo', showlegend=True,
        line=dict(color=COLOR_TEXTO_TERCIARIO, width=2, dash='dash'),
        customdata=datos_igual[['presupuesto_texto', 'pct_texto']],
        hovertemplate="<b>Equitativo</b><br>Presupuesto: %{customdata[0]}<br>Cartera protegida: %{customdata[1]}<extra></extra>",
    )
    figura.add_scatter(
        x=[presupuesto_actual], y=[pct_actual], mode='markers', showlegend=False,
        marker=dict(color=COLOR_NAVY_MARCA, size=12, line=dict(color='#FFFFFF', width=2)),
        hovertemplate=f"Tu presupuesto: {euros(presupuesto_actual)}<br>Cartera protegida: {porcentaje(pct_actual)}<extra></extra>",
    )
    figura.update_xaxes(
        title='Presupuesto (€)',
        tickfont=dict(size=11, color=COLOR_TEXTO_TERCIARIO),
        title_font=dict(size=12, color=COLOR_TEXTO_TERCIARIO),
        gridcolor=COLOR_BORDE, zeroline=False, automargin=True,
    )
    figura.update_yaxes(
        title='% de cartera protegida', range=[0, 100],
        tickfont=dict(size=11, color=COLOR_TEXTO_TERCIARIO),
        title_font=dict(size=12, color=COLOR_TEXTO_TERCIARIO),
        gridcolor=COLOR_BORDE, zeroline=False, automargin=True,
    )
    figura.update_layout(
        plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF',
        height=340,
        margin=dict(l=10, r=20, t=40, b=40),
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0,
            font=dict(size=12, color=COLOR_TEXTO_SECUNDARIO), title_text='',
        ),
        hoverlabel=dict(bgcolor='#FFFFFF', bordercolor=COLOR_BORDE, font=dict(size=12, color=COLOR_TEXTO_PRINCIPAL)),
    )
    return figura


def ficha_cliente(datos_cliente, coste_por_hogar):
    cubierto = datos_cliente['cubierto']
    color_chip = COLOR_EXITO if cubierto else COLOR_RIESGO
    fondo_chip = "#E8F6EC" if cubierto else "#FDF3E3"
    texto_chip = "Entra en el plan" if cubierto else "Fuera del plan"
    grupo = grupo_tendencia(datos_cliente['cuadrante'])
    color_grupo = GRUPOS_TENDENCIA[grupo]

    if cubierto:
        explicacion = (
            f"Está en la posición <strong>{miles(datos_cliente['posicion'])}</strong> por valor dentro de su segmento "
            f"y el presupuesto cubre a los <strong>{miles(datos_cliente['cubiertos'])}</strong> primeros, "
            f"así que entra en la lista de contacto."
        )
    elif datos_cliente['cubiertos'] == 0:
        explicacion = (
            "Su segmento no ha recibido presupuesto en este reparto, así que ningún cliente de este grupo entra en la lista."
        )
    else:
        faltan = datos_cliente['posicion'] - datos_cliente['cubiertos']
        explicacion = (
            f"Está en la posición <strong>{miles(datos_cliente['posicion'])}</strong> y el presupuesto llega hasta la "
            f"<strong>{miles(datos_cliente['cubiertos'])}</strong>. Harían falta unos "
            f"<strong>{euros(faltan * coste_por_hogar)}</strong> más en su segmento para alcanzarlo."
        )

    st.markdown(f"""
    <div class="vg-ficha" style="border-top-color:{color_chip};">
        <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:12px;">
            <div>
                <div class="vg-dato">Cliente</div>
                <div style="font-size:26px; font-weight:700; color:{COLOR_TEXTO_PRINCIPAL};">
                    #{datos_cliente['household_key']}
                </div>
            </div>
            <div class="vg-chip" style="background:{fondo_chip}; color:{color_chip};">{texto_chip}</div>
        </div>
        <div style="height:1px; background:{COLOR_BORDE}; margin:20px 0;"></div>
        <div style="display:flex; flex-wrap:wrap; gap:36px;">
            <div>
                <div class="vg-dato">Valor histórico</div>
                <div class="vg-dato-valor">{euros(datos_cliente['valor_historico'], 2)}</div>
            </div>
            <div>
                <div class="vg-dato">Valor futuro estimado</div>
                <div class="vg-dato-valor">{euros(datos_cliente['valor_futuro'], 2)}</div>
            </div>
            <div>
                <div class="vg-dato">Segmento</div>
                <div class="vg-dato-valor" style="font-size:16px; padding-top:4px;">
                    <span style="display:inline-block; width:9px; height:9px; border-radius:50%; background:{color_grupo}; margin-right:7px;"></span>
                    {datos_cliente['cuadrante']}
                </div>
            </div>
            <div>
                <div class="vg-dato">Posición por valor en su segmento</div>
                <div class="vg-dato-valor">{miles(datos_cliente['posicion'])} de {miles(datos_cliente['total_segmento'])}</div>
            </div>
        </div>
        <div style="height:1px; background:{COLOR_BORDE}; margin:20px 0;"></div>
        <div style="font-size:14px; color:{COLOR_TEXTO_SECUNDARIO}; line-height:1.6;">{explicacion}</div>
    </div>
    """, unsafe_allow_html=True)


def consultar_cliente(household_key, segmentos, tabla_resultado):
    fila = segmentos[segmentos['household_key'] == household_key]
    if fila.empty:
        return None
    fila = fila.iloc[0]
    cuadrante = fila['cuadrante']
    lista_segmento = backend.obtener_hogares_por_cuadrante(cuadrante, segmentos, tabla_resultado)
    coincidencias = lista_segmento.index[lista_segmento['household_key'] == household_key]
    posicion = int(coincidencias[0]) + 1 if len(coincidencias) else 0
    fila_segmento = tabla_resultado[tabla_resultado['cuadrante'] == cuadrante]
    cubiertos = int(fila_segmento.iloc[0]['hogares_cubiertos']) if not fila_segmento.empty else 0
    return {
        'household_key': int(household_key),
        'cuadrante': cuadrante,
        'valor_futuro': float(fila['clv_futuro_predicho']),
        'valor_historico': float(fila['clv_historico']),
        'posicion': posicion,
        'total_segmento': int(len(lista_segmento)),
        'cubiertos': cubiertos,
        'cubierto': bool(0 < posicion <= cubiertos),
    }


def volver_al_inicio():
    for clave in CLAVES_RESULTADO:
        st.session_state.pop(clave, None)


col_logo, col_meta = st.columns([3, 1])
with col_logo:
    st.image("logo_valueguard_transparente.png", width=220)
with col_meta:
    st.markdown(
        f"<div style='text-align:right; color:{COLOR_TEXTO_TERCIARIO}; font-size:12px; padding-top:1.2rem;'>"
        f"Modelo v1 · datos: 03/09/2026</div>",
        unsafe_allow_html=True
    )
st.title("Motor de inversión en fidelización")


@st.cache_data
def obtener_segmentos():
    return backend.cargar_datos()


@st.cache_data
def obtener_tabla_base(_segmentos):
    return backend.construir_tabla_segmentos(_segmentos)


@st.cache_data
def obtener_curva_sensibilidad(_tabla_base, _segmentos, coste_por_hogar, horizonte_semanas, presupuesto_max, equitativo=False):
    funcion_reparto = backend.repartir_presupuesto_equitativo if equitativo else backend.repartir_presupuesto
    return backend.curva_sensibilidad_presupuesto(
        _tabla_base, _segmentos,
        coste_por_hogar=coste_por_hogar,
        horizonte_semanas=horizonte_semanas,
        presupuesto_max=presupuesto_max,
        funcion_reparto=funcion_reparto,
    )


segmentos = obtener_segmentos()
tabla_base = obtener_tabla_base(segmentos)

with st.sidebar:
    st.markdown(
        f'<div class="vg-drawer-cerrar" onclick="{JS_CERRAR_SIDEBAR}">✕</div>',
        unsafe_allow_html=True,
    )
    st.button("🏠  Inicio", use_container_width=False, on_click=volver_al_inicio, help="Limpia los resultados y vuelve a la pantalla inicial")
    st.markdown(f"<div style='height:1px; background:{COLOR_BORDE}; margin:14px 0 18px 0;'></div>", unsafe_allow_html=True)
    titulo_seccion("Parámetros")
    st.caption("Reparte tu presupuesto priorizando a los clientes con más valor y más riesgo de perderse.")
    presupuesto = st.number_input("Presupuesto (€)", min_value=0, value=5000, step=500)
    coste_por_hogar = st.number_input("Coste por cliente (€)", min_value=0.1, value=3.0, step=0.5)
    horizonte_semanas = st.selectbox(
        "Horizonte de evaluación",
        HORIZONTES_SEMANAS,
        index=HORIZONTES_SEMANAS.index(HORIZONTE_POR_DEFECTO),
        format_func=lambda semanas: ETIQUETAS_HORIZONTE.get(semanas, f"{semanas} semanas"),
    )
    calcular = st.button("Calcular reparto", type="primary", use_container_width=True)

# Burbuja con el resumen de los parámetros actuales (solo visible en móvil): además del
# botón de hamburguesa, es el segundo indicio de que hay ajustes disponibles, y también
# abre el mismo panel deslizante al tocarla.
_etq_horizonte_larga = ETIQUETAS_HORIZONTE.get(horizonte_semanas, f"{horizonte_semanas} semanas")
_etq_horizonte_corta = _etq_horizonte_larga.split("(")[-1].rstrip(")") if "(" in _etq_horizonte_larga else _etq_horizonte_larga
st.markdown(
    f'<div class="vg-chip-parametros" onclick="{JS_TOGGLE_SIDEBAR}">'
    f'<span>⚙ <b>{euros(presupuesto)}</b> · {euros(coste_por_hogar, 2)}/cliente · {_etq_horizonte_corta}</span>'
    f'<span class="vg-chip-flecha">›</span>'
    f'</div>',
    unsafe_allow_html=True,
)

if calcular:
    with st.spinner("Calculando…"):
        reparto = backend.repartir_presupuesto(presupuesto, tabla_base, horizonte_semanas=horizonte_semanas, coste_por_hogar=coste_por_hogar)
        tabla_resultado, pct_cartera_protegida, retorno_incremental_total, valor_protegido_total, excedente_presupuesto_total = backend.calcular_cobertura_y_kpi(
            reparto, segmentos, coste_por_hogar=coste_por_hogar
        )
        reparto_igual = backend.repartir_presupuesto_equitativo(presupuesto, tabla_base, horizonte_semanas=horizonte_semanas, coste_por_hogar=coste_por_hogar)
        _, pct_cartera_protegida_igual, retorno_incremental_total_igual, _, _ = backend.calcular_cobertura_y_kpi(
            reparto_igual, segmentos, coste_por_hogar=coste_por_hogar
        )

    st.session_state['tabla_resultado'] = tabla_resultado
    st.session_state['pct_cartera_protegida'] = pct_cartera_protegida
    st.session_state['retorno_incremental_total'] = retorno_incremental_total
    st.session_state['presupuesto'] = presupuesto
    st.session_state['horizonte_semanas'] = horizonte_semanas
    st.session_state['coste_por_hogar'] = coste_por_hogar
    st.session_state['pct_cartera_protegida_igual'] = pct_cartera_protegida_igual
    st.session_state['retorno_incremental_total_igual'] = retorno_incremental_total_igual
    st.session_state['excedente_presupuesto_total'] = excedente_presupuesto_total
    st.session_state.pop('cliente_buscado', None)

if 'tabla_resultado' not in st.session_state:
    total_clientes = int(tabla_base['n_hogares'].sum())
    valor_futuro_cartera = tabla_base['valor_futuro_total'].sum()
    en_riesgo = tabla_base[tabla_base['cuadrante'].str.contains('Descendente')]
    valor_en_riesgo = en_riesgo['valor_futuro_total'].sum()
    clientes_en_riesgo = int(en_riesgo['n_hogares'].sum())
    pct_valor_en_riesgo = valor_en_riesgo / valor_futuro_cartera * 100 if valor_futuro_cartera else 0
    alto_valor_riesgo = tabla_base[tabla_base['cuadrante'] == 'Alto valor / Descendente']
    clientes_alto_riesgo = int(alto_valor_riesgo['n_hogares'].sum()) if not alto_valor_riesgo.empty else 0
    valor_anual_cliente = backend.EFECTO_CAUSAL_SEMANAL * 52
    retorno_por_euro = valor_anual_cliente / coste_por_hogar if coste_por_hogar else 0

    hero_html = (
        '<div class="vg-hero">'
        + SVG_RED_HERO
        + '<div class="vg-hero-contenido">'
        + f'<div class="vg-hero-kicker">{miles(total_clientes)} clientes · {SEMANAS_HISTORIAL} semanas de compras</div>'
        + '<div class="vg-hero-titulo">Ya sabes cuánto vale cada cliente.<br>Ahora sabes en quién invertir.</div>'
        + '<div class="vg-hero-sub">ValueGuard estima el valor futuro de cada cliente, detecta cuál se está apagando '
        + 'y reparte tu presupuesto de fidelización donde más valor salva. Hoy hay '
        + f'<strong>{euros(valor_en_riesgo)}</strong> de valor futuro en clientes que están comprando menos que antes.</div>'
        + '</div></div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    titulo_seccion("Lo que ya sabemos de tu cartera")
    col_d1, col_d2, col_d3, col_d4 = st.columns(4)
    with col_d1:
        tarjeta_kpi("Clientes analizados", miles(total_clientes), f"{len(tabla_base)} segmentos de valor y tendencia")
    with col_d2:
        tarjeta_kpi("Historial de compra", f"{SEMANAS_HISTORIAL} semanas", "cestas, categorías, demografía y campañas")
    with col_d3:
        tarjeta_kpi("Valor futuro estimado", euros(valor_futuro_cartera), "lo que vale la cartera si nada cambia")
    with col_d4:
        tarjeta_kpi(
            "Valor en riesgo",
            euros(valor_en_riesgo),
            f"{porcentaje(pct_valor_en_riesgo)} de la cartera · {miles(clientes_en_riesgo)} clientes en descenso",
            COLOR_RIESGO,
            color_cifra=COLOR_RIESGO,
            color_borde=COLOR_RIESGO,
        )

    titulo_seccion("Dónde está el valor")
    with st.container(border=True):
        encabezado_bloque(
            "Mapa de la cartera",
            "Cada burbuja es un segmento: su tamaño es el valor futuro que representa y su color, si ese valor crece o se está perdiendo",
        )
        st.plotly_chart(mapa_cartera(tabla_base), use_container_width=True, theme=None, config=CONFIG_PLOTLY)

    titulo_seccion("Lo que ganas con la herramienta")
    col_g1, col_g2, col_g3 = st.columns(3)
    with col_g1:
        tarjeta_kpi(
            "Retorno de mantener a un cliente",
            euros(valor_anual_cliente),
            f"retorno incremental estimado a un año, según el efecto causal medido "
            f"({euros(backend.EFECTO_CAUSAL_SEMANAL, 2)} por semana)",
            color_cifra=COLOR_AZUL,
        )
    with col_g2:
        tarjeta_kpi(
            "Por cada euro invertido en contacto",
            f"{euros(retorno_por_euro)} de retorno",
            f"con el coste actual de {euros(coste_por_hogar, 2)} por cliente contactado",
            color_cifra=COLOR_AZUL,
        )
    with col_g3:
        tarjeta_kpi(
            "Primer grupo del plan",
            f"{miles(clientes_alto_riesgo)} clientes",
            "de alto valor y en descenso: el grupo al que va el presupuesto antes que a nadie",
            color_cifra=COLOR_RIESGO,
            color_borde=COLOR_RIESGO,
        )

    st.markdown(
        f"<div style='font-size:12px; color:{COLOR_TEXTO_TERCIARIO}; margin-top:18px; line-height:1.6;'>"
        f"Fija el presupuesto en el panel de la izquierda y pulsa <strong>Calcular reparto</strong> "
        f"para obtener la lista de clientes a contactar.</div>",
        unsafe_allow_html=True
    )
else:
    tabla_resultado = st.session_state['tabla_resultado'].copy()
    pct_cartera_protegida = st.session_state['pct_cartera_protegida']
    retorno_incremental_total = st.session_state['retorno_incremental_total']
    pct_igual = st.session_state.get('pct_cartera_protegida_igual', 0)
    retorno_igual = st.session_state.get('retorno_incremental_total_igual', 0)
    excedente_presupuesto_total = st.session_state.get('excedente_presupuesto_total', 0.0)
    coste_usado = st.session_state.get('coste_por_hogar', coste_por_hogar)
    horizonte_usado = st.session_state.get('horizonte_semanas', HORIZONTE_POR_DEFECTO)
    diferencia_pct = pct_cartera_protegida - pct_igual
    diferencia_retorno = retorno_incremental_total - retorno_igual

    seccion = st.radio("Sección", SECCIONES, horizontal=True, label_visibility="collapsed", key="seccion")

    st.markdown(
        f"<div style='font-size:13px; color:{COLOR_TEXTO_TERCIARIO}; margin:10px 0 18px 0;'>"
        f"Presupuesto de <strong style='color:{COLOR_TEXTO_SECUNDARIO};'>{euros(st.session_state.get('presupuesto', 0))}</strong>"
        f" · coste de <strong style='color:{COLOR_TEXTO_SECUNDARIO};'>{euros(coste_usado, 2)}</strong> por cliente"
        f" · horizonte de <strong style='color:{COLOR_TEXTO_SECUNDARIO};'>"
        f"{ETIQUETAS_HORIZONTE.get(horizonte_usado, str(horizonte_usado) + ' semanas')}</strong></div>",
        unsafe_allow_html=True
    )

    if seccion == "Resultados":
        mostrar_excedente = excedente_presupuesto_total > 0.01
        columnas_kpi = st.columns(4) if mostrar_excedente else st.columns(3)
        col_k1, col_k2, col_k3 = columnas_kpi[0], columnas_kpi[1], columnas_kpi[2]
        with col_k1:
            tarjeta_kpi(
                "% de cartera protegida",
                porcentaje(pct_cartera_protegida),
                f"vs {porcentaje(pct_igual)} en un reparto equitativo",
                COLOR_EXITO if diferencia_pct > 0 else COLOR_TEXTO_TERCIARIO,
            )
        with col_k2:
            tarjeta_kpi(
                "Retorno incremental esperado",
                euros(retorno_incremental_total),
                f"vs {euros(retorno_igual)} en un reparto equitativo",
                COLOR_EXITO if diferencia_retorno > 0 else COLOR_TEXTO_TERCIARIO,
            )
        with col_k3:
            tarjeta_kpi(
                "Diferencia vs. reparto equitativo",
                f"{diferencia_pct:+.1f}".replace(".", ",") + " pp",
                "puntos porcentuales de cartera protegida",
                COLOR_TEXTO_TERCIARIO,
                color_cifra=COLOR_EXITO if diferencia_pct > 0 else COLOR_RIESGO,
            )
        if mostrar_excedente:
            with columnas_kpi[3]:
                tarjeta_kpi(
                    "Excedente ya cubierto al 100%",
                    euros(excedente_presupuesto_total),
                    "presupuesto de segmentos totalmente cubiertos: margen para una segunda ola o un canal más intensivo",
                    COLOR_TEXTO_TERCIARIO,
                )

        st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            encabezado_bloque(
                "Presupuesto asignado por segmento",
                "Ordenado de mayor a menor presupuesto; el color indica si el segmento pierde o gana valor",
            )
            st.plotly_chart(grafico_presupuesto(tabla_resultado), use_container_width=True, theme=None, config=CONFIG_PLOTLY)

        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            encabezado_bloque(
                "¿Cuánto conviene gastar?",
                "Cuanto más presupuesto, menos crece la cartera protegida — el punto navy marca dónde estás tú ahora",
            )
            presupuesto_max_curva = max(
                tabla_base['n_hogares'].sum() * coste_usado * 1.5,
                st.session_state.get('presupuesto', 0) * 1.3,
                1.0,
            )
            curva_sensibilidad = obtener_curva_sensibilidad(
                tabla_base, segmentos, coste_usado, horizonte_usado, presupuesto_max_curva
            )
            curva_sensibilidad_igual = obtener_curva_sensibilidad(
                tabla_base, segmentos, coste_usado, horizonte_usado, presupuesto_max_curva, equitativo=True
            )
            st.plotly_chart(
                grafico_sensibilidad(
                    curva_sensibilidad, curva_sensibilidad_igual,
                    st.session_state.get('presupuesto', 0), pct_cartera_protegida,
                ),
                use_container_width=True, theme=None, config=CONFIG_PLOTLY,
            )

        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            encabezado_bloque(
                "Detalle por segmento",
                "El segmento en la fila superior es el de mayor prioridad",
            )

            tabla_ordenada = tabla_resultado.sort_values('presupuesto_asignado', ascending=False).reset_index(drop=True)
            tabla_ordenada['prioridad'] = ""
            tabla_ordenada.loc[0, 'prioridad'] = "Prioridad alta"

            tabla_mostrar = tabla_ordenada[[
                'cuadrante', 'prioridad', 'n_hogares', 'hogares_cubiertos',
                'pct_hogares_cubiertos', 'presupuesto_asignado', 'techo_segmento'
            ]].rename(columns=NOMBRES_COLUMNAS_SEGMENTOS)

            def resaltar_fila_principal(fila):
                if fila.name == 0:
                    return [f'background-color: {COLOR_AZUL_TINTE}'] * len(fila)
                return [''] * len(fila)

            estilo = tabla_mostrar.style.apply(resaltar_fila_principal, axis=1).map(
                lambda v: f'color: {COLOR_RIESGO}; font-weight:600;' if v == "Prioridad alta" else '', subset=['Prioridad']
            )

            st.dataframe(
                estilo,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Presupuesto asignado (€)': st.column_config.NumberColumn(format="%.0f €"),
                    'Límite máximo (€)': st.column_config.NumberColumn(format="%.0f €"),
                    '% cubierto': st.column_config.NumberColumn(format="%.1f %%"),
                }
            )

    elif seccion == "Clientes a contactar":
        cuadrante_elegido = st.selectbox("Segmento de clientes", tabla_resultado['cuadrante'].unique())
        hogares_lista = backend.obtener_hogares_por_cuadrante(cuadrante_elegido, segmentos, st.session_state['tabla_resultado'])
        hogares_a_invertir = hogares_lista[hogares_lista['invertir']]

        st.markdown(
            f"<div style='color:{COLOR_TEXTO_SECUNDARIO}; margin-bottom:8px;'>"
            f"<strong style='color:{COLOR_TEXTO_PRINCIPAL};'>{miles(len(hogares_a_invertir))}</strong> de "
            f"<strong style='color:{COLOR_TEXTO_PRINCIPAL};'>{miles(len(hogares_lista))}</strong> clientes de este segmento se cubren con el presupuesto.</div>",
            unsafe_allow_html=True
        )

        st.dataframe(
            hogares_a_invertir.rename(columns=NOMBRES_COLUMNAS_HOGARES),
            use_container_width=True, hide_index=True,
            column_config={'Valor futuro estimado (€)': st.column_config.NumberColumn(format="%.2f €")}
        )

        csv = hogares_a_invertir.rename(columns=NOMBRES_COLUMNAS_HOGARES).to_csv(index=False).encode('utf-8')
        st.download_button("Descargar lista (CSV)", csv, f"clientes_{cuadrante_elegido}.csv", "text/csv")

    elif seccion == "Explicación":
        explicacion, es_ia = backend.generar_explicacion(
            st.session_state['presupuesto'], st.session_state['tabla_resultado'], pct_cartera_protegida, retorno_incremental_total
        )
        etiqueta_fuente = "" if es_ia else f"<div style='font-size:12px; color:{COLOR_TEXTO_TERCIARIO}; margin-top:12px;'>Generado con plantilla</div>"
        st.markdown(f"""
        <div class="vg-ficha" style="line-height:1.7;">
            {explicacion}
            {etiqueta_fuente}
        </div>
        """, unsafe_allow_html=True)

    else:
        encabezado_bloque(
            "Consulta por cliente",
            "Busca un cliente por su ID para ver su valor estimado y si el presupuesto llega hasta él",
        )

        ids_disponibles = segmentos['household_key']
        with st.form("busqueda_cliente"):
            col_input, col_boton, _ = st.columns([2, 1, 3])
            with col_input:
                id_buscado = st.number_input(
                    "ID de cliente (household_key)",
                    min_value=int(ids_disponibles.min()),
                    max_value=int(ids_disponibles.max()),
                    value=int(st.session_state.get('cliente_buscado', ids_disponibles.min())),
                    step=1,
                    format="%d",
                )
            with col_boton:
                st.markdown("<div style='height:26px;'></div>", unsafe_allow_html=True)
                buscar = st.form_submit_button("Buscar", use_container_width=True)

        st.caption(
            f"IDs disponibles entre {miles(ids_disponibles.min())} y {miles(ids_disponibles.max())}. "
            f"Pulsa Intro para buscar."
        )

        if buscar:
            st.session_state['cliente_buscado'] = int(id_buscado)

        if 'cliente_buscado' in st.session_state:
            datos_cliente = consultar_cliente(
                st.session_state['cliente_buscado'], segmentos, st.session_state['tabla_resultado']
            )
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            if datos_cliente is None:
                st.warning("Ese ID de cliente no está en la base.")
            else:
                ficha_cliente(datos_cliente, coste_usado)
