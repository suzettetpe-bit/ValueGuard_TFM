# ValueGuard_TFM
ValueGuard — motor de priorización de inversión en fidelización basado en CLV, tendencia de valor e inferencia causal.

**Motor de marketing analytics para la priorización de inversión en fidelización de clientes**, basado en CLV, trayectoria de valor e inferencia causal.

## Qué hace

Sustituye el reparto intuitivo del presupuesto de fidelización por una decisión basada en datos: predice el valor futuro de cada cliente, detecta quién de alto valor está cayendo, y estima —mediante propensity score matching y diferencia-en-diferencias— el efecto real de las campañas pasadas. Con eso, reparte el presupuesto por segmento y genera una explicación en lenguaje natural para cada recomendación.

## Dataset

[Dunnhumby - The Complete Journey](https://www.kaggle.com/datasets/frtgnn/dunnhumby-the-complete-journey) — transacciones reales de 2.500 hogares, 102 semanas, con demografía y campañas de fidelización.

## Tecnologías

Python · Pandas · scikit-learn · XGBoost · statsmodels (matching y diff-in-diff) · Streamlit · API de OpenAI (gpt-4o-mini)

## Estructura
├── notebooks/
│ ├── EDA.ipynb
│ ├── Preprocesado.ipynb
│ ├── Modelado_CLV.ipynb
│ └── Estimacion_Causal.ipynb
├── backend/
├── app.py
└── requirements.txt


## Ejecutar la app

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Nota

Estimación causal cuasi-experimental (matching, no aleatorización); modelo de CLV con error relativo ~39%. Detalle completo en la memoria del TFM.

---
TFM — Máster en Data Science, Big Data & Business Analytics, UCM.
