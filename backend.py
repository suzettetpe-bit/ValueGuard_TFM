import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

PESOS_PRIORIDAD = {
    'Alto valor / Descendente': 5,
    'Alto valor / Ascendente': 4,
    'Bajo valor / Descendente': 3,
    'Bajo valor / Ascendente': 2,
    'Sin tendencia disponible': 1,
}
EFECTO_CAUSAL_SEMANAL = 17.79

def cargar_datos(ruta_hogares='hogares_procesado.csv', ruta_predicciones='predicciones_clv_futuro.csv'):
    hogares = pd.read_csv(ruta_hogares)
    predicciones = pd.read_csv(ruta_predicciones)
    # Las seis últimas columnas (comportamiento de compra + exposición histórica a
    # campañas) no las usa el reparto de presupuesto — se cargan para la pestaña
    # "Perfil de segmentos" (ver construir_tabla_perfil_segmentos).
    segmentos = hogares[[
        'household_key', 'cuadrante', 'nivel_valor', 'nivel_tendencia', 'clv_historico',
        'gasto_medio_cesta', 'tamano_medio_cesta', 'frecuencia_cestas', 'n_categorias_distintas',
        'descuento_total', 'n_campanas',
    ]].merge(
        predicciones, on='household_key', how='inner'
    )
    return segmentos

def construir_tabla_segmentos(segmentos):
    tabla = segmentos.groupby('cuadrante').agg(
        n_hogares=('household_key', 'count'),
        valor_futuro_total=('clv_futuro_predicho', 'sum'),
        valor_futuro_medio=('clv_futuro_predicho', 'mean')
    ).reset_index()

    tabla['pct_hogares'] = tabla['n_hogares'] / segmentos.shape[0] * 100
    tabla['pct_valor_futuro'] = tabla['valor_futuro_total'] / segmentos['clv_futuro_predicho'].sum() * 100
    tabla['peso_prioridad'] = tabla['cuadrante'].map(PESOS_PRIORIDAD)
    tabla['score'] = tabla['peso_prioridad'] * tabla['valor_futuro_total']

    return tabla

def construir_tabla_perfil_segmentos(segmentos):
    """Cómo compra cada segmento y cuánto marketing ha recibido hasta ahora — pensada para
    la pestaña 'Perfil de segmentos' de la app, no para el cálculo del reparto en sí."""
    tabla = segmentos.groupby('cuadrante').agg(
        gasto_medio_cesta=('gasto_medio_cesta', 'mean'),
        tamano_medio_cesta=('tamano_medio_cesta', 'mean'),
        frecuencia_cestas=('frecuencia_cestas', 'mean'),
        n_categorias_distintas=('n_categorias_distintas', 'mean'),
        descuento_total=('descuento_total', 'mean'),
        n_campanas=('n_campanas', 'mean'),
    ).reset_index()
    tabla['peso_prioridad'] = tabla['cuadrante'].map(PESOS_PRIORIDAD)
    return tabla.sort_values('peso_prioridad', ascending=False).reset_index(drop=True)

def repartir_presupuesto(presupuesto_total, tabla_segmentos, horizonte_semanas=52, efecto_semanal=EFECTO_CAUSAL_SEMANAL, coste_por_hogar=3.0):
    tabla = tabla_segmentos.copy()
    tabla['techo_hogar'] = efecto_semanal * horizonte_semanas
    # Tope de retorno: lo máximo que tiene sentido invertir según el retorno esperado
    # por hogar. Por sí solo es demasiado laxo (~925€/hogar/año) y casi nunca se
    # alcanza con presupuestos reales, así que el reparto proporcional por score
    # seguía empujando dinero a segmentos ya saturados en vez de redistribuirlo.
    tabla['techo_retorno'] = tabla['techo_hogar'] * tabla['n_hogares']
    # Tope de saturación: lo máximo que el segmento puede absorber de forma útil,
    # es decir, el coste de cubrir al 100% sus hogares. Al alcanzarlo, el segmento
    # queda saturado y cualquier euro adicional se redistribuye al resto.
    tabla['techo_saturacion'] = tabla['n_hogares'] * coste_por_hogar
    tabla['techo_segmento'] = tabla[['techo_retorno', 'techo_saturacion']].min(axis=1)
    tabla['presupuesto_asignado'] = 0.0

    pendiente = presupuesto_total
    activos = list(tabla.index)

    while pendiente > 0.01 and activos:
        score_activo = tabla.loc[activos, 'score'].sum()
        if score_activo == 0:
            break
        tabla.loc[activos, 'presupuesto_asignado'] += pendiente * (
            tabla.loc[activos, 'score'] / score_activo
        )
        excedidos = [
            i for i in activos
            if tabla.loc[i, 'presupuesto_asignado'] > tabla.loc[i, 'techo_segmento']
        ]
        if not excedidos:
            pendiente = 0.0
            break
        exceso = 0.0
        for i in excedidos:
            exceso += tabla.loc[i, 'presupuesto_asignado'] - tabla.loc[i, 'techo_segmento']
            tabla.loc[i, 'presupuesto_asignado'] = tabla.loc[i, 'techo_segmento']
            activos.remove(i)
        pendiente = exceso

    tabla['presupuesto_no_asignado'] = pendiente if pendiente > 0.01 else 0.0
    tabla['pct_presupuesto'] = tabla['presupuesto_asignado'] / presupuesto_total * 100

    return tabla

def repartir_presupuesto_equitativo(presupuesto_total, tabla_segmentos, horizonte_semanas=52, efecto_semanal=EFECTO_CAUSAL_SEMANAL, coste_por_hogar=3.0):
    tabla_igual = tabla_segmentos.copy()
    tabla_igual['score'] = 1.0
    return repartir_presupuesto(presupuesto_total, tabla_igual, horizonte_semanas, efecto_semanal, coste_por_hogar)

def curva_sensibilidad_presupuesto(tabla_segmentos, segmentos, coste_por_hogar=3.0, horizonte_semanas=52, presupuesto_max=None, n_puntos=25, funcion_reparto=repartir_presupuesto):
    total_hogares = tabla_segmentos['n_hogares'].sum()
    if not presupuesto_max or presupuesto_max <= 0:
        presupuesto_max = total_hogares * coste_por_hogar * 1.4

    filas = []
    for punto in np.linspace(0, presupuesto_max, n_puntos):
        presupuesto = max(punto, 1.0)
        reparto = funcion_reparto(presupuesto, tabla_segmentos, horizonte_semanas=horizonte_semanas, coste_por_hogar=coste_por_hogar)
        _, pct_cartera_protegida, _, _, _ = calcular_cobertura_y_kpi(reparto, segmentos, coste_por_hogar=coste_por_hogar)
        filas.append({'presupuesto': presupuesto, 'pct_cartera_protegida': pct_cartera_protegida})

    return pd.DataFrame(filas)

def calcular_cobertura_y_kpi(tabla_reparto, segmentos, coste_por_hogar=3.0):
    tabla = tabla_reparto.copy()
    tabla['hogares_cubiertos'] = (tabla['presupuesto_asignado'] / coste_por_hogar).apply(np.floor).astype(int)
    tabla['hogares_cubiertos'] = tabla[['hogares_cubiertos', 'n_hogares']].min(axis=1)
    tabla['pct_hogares_cubiertos'] = tabla['hogares_cubiertos'] / tabla['n_hogares'] * 100

    valor_protegido_total = 0.0
    for _, fila in tabla.iterrows():
        hogares_segmento = segmentos[segmentos['cuadrante'] == fila['cuadrante']].sort_values(
            'clv_futuro_predicho', ascending=False
        )
        top_n = hogares_segmento.head(int(fila['hogares_cubiertos']))
        valor_protegido_total += top_n['clv_futuro_predicho'].sum()

    valor_futuro_total_cartera = segmentos['clv_futuro_predicho'].sum()
    pct_cartera_protegida = valor_protegido_total / valor_futuro_total_cartera * 100

    retorno_incremental_total = (tabla['hogares_cubiertos'] * tabla['techo_hogar']).sum()

    tabla['excedente_presupuesto'] = (
        tabla['presupuesto_asignado'] - tabla['n_hogares'] * coste_por_hogar
    ).clip(lower=0.0)
    excedente_presupuesto_total = tabla['excedente_presupuesto'].sum()

    return tabla, pct_cartera_protegida, retorno_incremental_total, valor_protegido_total, excedente_presupuesto_total

def construir_prompt(presupuesto_total, tabla_resultado, pct_cartera_protegida, retorno_incremental_total):
    resumen_segmentos = "\n".join(
        f"- {fila['cuadrante']}: {int(fila['hogares_cubiertos'])} hogares cubiertos de {int(fila['n_hogares'])}, "
        f"{fila['presupuesto_asignado']:.0f}€ asignados"
        for _, fila in tabla_resultado.iterrows()
    )
    prompt = f"""Eres un asistente que explica en lenguaje claro y de negocio (no técnico) el resultado de un reparto de presupuesto de fidelización de clientes.

Presupuesto total: {presupuesto_total:.0f}€
% de cartera de valor futuro protegida: {pct_cartera_protegida:.2f}%
Retorno incremental esperado: {retorno_incremental_total:.2f}€

Reparto por segmento:
{resumen_segmentos}

Redacta un párrafo breve (máximo 5 líneas) dirigido a un responsable de marketing, explicando qué significa este reparto y por qué tiene sentido, sin usar jerga técnica."""
    return prompt

def generar_explicacion_respaldo(presupuesto_total, tabla_resultado, pct_cartera_protegida, retorno_incremental_total):
    segmento_principal = tabla_resultado.sort_values('presupuesto_asignado', ascending=False).iloc[0]
    return (
        f"Con un presupuesto de {presupuesto_total:,.0f}€ se protege el {pct_cartera_protegida:.2f}% del valor futuro "
        f"de la cartera de clientes, con un retorno incremental esperado de {retorno_incremental_total:,.2f}€. "
        f"El segmento con mayor inversión es '{segmento_principal['cuadrante']}', "
        f"cubriendo {int(segmento_principal['hogares_cubiertos'])} de {int(segmento_principal['n_hogares'])} hogares. "
        f"El reparto prioriza primero los segmentos de mayor riesgo de pérdida de valor, y a valor igual, "
        f"los de mayor tamaño económico."
    )

def generar_explicacion(presupuesto_total, tabla_resultado, pct_cartera_protegida, retorno_incremental_total):
    prompt = construir_prompt(presupuesto_total, tabla_resultado, pct_cartera_protegida, retorno_incremental_total)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        respuesta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=200,
        )
        return respuesta.choices[0].message.content, True
    except Exception:
        return generar_explicacion_respaldo(presupuesto_total, tabla_resultado, pct_cartera_protegida, retorno_incremental_total), False

def buscar_hogar(household_key, segmentos, tabla_cobertura):
    hogar = segmentos[segmentos['household_key'] == household_key]
    if hogar.empty:
        return None
    hogar = hogar.iloc[0]
    fila_segmento = tabla_cobertura[tabla_cobertura['cuadrante'] == hogar['cuadrante']]
    if fila_segmento.empty:
        cubierto = False
    else:
        fila_segmento = fila_segmento.iloc[0]
        hogares_segmento_ordenados = segmentos[segmentos['cuadrante'] == hogar['cuadrante']].sort_values(
            'clv_futuro_predicho', ascending=False
        ).reset_index()
        posicion = hogares_segmento_ordenados[hogares_segmento_ordenados['household_key'] == household_key].index[0]
        cubierto = posicion < fila_segmento['hogares_cubiertos']

    return {
        'household_key': household_key,
        'cuadrante': hogar['cuadrante'],
        'clv_futuro_predicho': hogar['clv_futuro_predicho'],
        'clv_historico': hogar['clv_historico'],
        'cubierto': bool(cubierto),
    }

def obtener_hogares_por_cuadrante(cuadrante, segmentos, tabla_cobertura=None):
    """tabla_cobertura es opcional: sin ella (p. ej. buscando un cliente antes de calcular
    ningún reparto, desde la pantalla de Inicio) se puede seguir ordenando el segmento por
    valor y saber la posición de un cliente, solo que ninguno se marca como 'invertir' porque
    todavía no hay presupuesto asignado."""
    hogares_segmento = segmentos[segmentos['cuadrante'] == cuadrante].sort_values(
        'clv_futuro_predicho', ascending=False
    ).reset_index(drop=True)

    n_cubiertos = 0
    if tabla_cobertura is not None:
        fila = tabla_cobertura[tabla_cobertura['cuadrante'] == cuadrante]
        n_cubiertos = int(fila.iloc[0]['hogares_cubiertos']) if not fila.empty else 0

    hogares_segmento['invertir'] = False
    if n_cubiertos > 0:
        hogares_segmento.loc[:n_cubiertos - 1, 'invertir'] = True

    return hogares_segmento[['household_key', 'clv_futuro_predicho', 'invertir']]