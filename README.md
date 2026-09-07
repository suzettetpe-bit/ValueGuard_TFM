# ValueGuard

ValueGuard — Motor de priorización de inversión en fidelización basado en CLV, tendencia de valor e inferencia causal.

Motor de marketing analytics para la priorización de inversión en fidelización de clientes, basado en CLV, trayectoria de valor e inferencia causal.

## Qué hace

Sustituye el reparto intuitivo del presupuesto de fidelización por una decisión basada en datos: predice el valor futuro de cada cliente, detecta quién de alto valor está cayendo, y estima —mediante propensity score matching y diferencia-en-diferencias— el efecto real de las campañas pasadas. Con eso, reparte el presupuesto por segmento y genera una explicación en lenguaje natural para cada recomendación.

## Dataset

[Dunnhumby - The Complete Journey](https://www.kaggle.com/datasets/frtgnn/dunnhumby-the-complete-journey) — transacciones reales de 2.500 hogares, 102 semanas, con demografía y campañas de fidelización.

## Modelado

Para predecir el valor futuro del cliente (CLV) se compararon 6 modelos: regresión lineal, Ridge, Random Forest, Random Forest ajustado (`GridSearchCV` sobre profundidad y tamaño de hoja), XGBoost y Gradient Boosting. Se eligió **Random Forest ajustado** por ser el que mejor controla el sobreajuste sin perder precisión (MAE test 174,20€, MAE medio en validación cruzada de 5 folds 189,98€).

Para el efecto causal de las campañas, el propensity score se estima con una regresión logística (scikit-learn) y el emparejamiento se hace por vecino más próximo con caliper; el efecto final se formaliza como una diferencia-en-diferencias mediante una regresión ponderada (statsmodels), dando +17,79€/semana por hogar tratado (p<0,001).

## Tecnologías

Python · Pandas · scikit-learn · statsmodels (diferencia-en-diferencias) · Streamlit · API de OpenAI (gpt-4o-mini)

## Estructura

```
├── notebooks/
│   ├── EDA.ipynb
│   ├── Preprocesado.ipynb
│   ├── Modelado_CLV.ipynb
│   └── Estimacion_Causal.ipynb
├── app.py
├── backend.py
├── requirements.txt
├── hogares_procesado.csv
├── predicciones_clv_futuro.csv
├── logo_valueguard_transparente.png
├── favicon_valueguard.png
└── .streamlit/
    └── config.toml
```

## Ejecutar la app

```
pip install -r requirements.txt
streamlit run app.py
```

## Nota

Estimación causal cuasi-experimental (matching, no aleatorización); modelo de CLV con error relativo ~39%. Detalle completo en la memoria del TFM.

TFM — Máster en Data Science, Big Data & Business Analytics, UCM.

