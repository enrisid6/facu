# Observatorio del Litio — edición Vercel 1.4

Página web estática en `public/` y API Flask serverless para Vercel. Mantiene el HTML de la versión 1.3 y cambia el servidor persistente `server.py` por una función compatible con Vercel. Vercel sirve el `public/index.html` directamente y manda únicamente `/api/*` a Flask.

## Publicar en Vercel
1. Extraé el ZIP y subí su contenido a un repositorio GitHub **en la raíz del repositorio** (no la carpeta contenedora).
2. En https://vercel.com/new elegí **Import Git Repository**, seleccioná ese repositorio.
3. Configurá Framework Preset **Other** (si no se detecta automáticamente) y **Root Directory** en la raíz del proyecto.
4. No establezcas un comando de build ni una carpeta `Output Directory` personalizada. Desplegá con **Deploy**.
5. Probá `https://TU-DOMINIO.vercel.app/api/health`, luego las opciones **Actualizar datos** del dashboard.

## Endpoints disponibles
- `/api/health` — confirma sólo funcionamiento del backend.
- `/api/worldbank?indicator=FP.CPI.TOTL.ZG` — serie de inflación Argentina.
- `/api/worldbank?indicator=BX.KLT.DINV.WD.GD.ZS` — IED neta, porcentaje PIB.
- `/api/worldbank?indicator=NY.GDP.MKTP.CD` — PIB USD corrientes.
- `/api/trade?reporterCode=32&flowCode=X&cmdCode=283691&period=2024` — UN Comtrade, clasificación comercial HS (proxy sin credenciales).
- `/api/catalog` — metadatos del dataset SIACAM en Datos Argentina.

## Limitaciones que hay que tener claras
- Los datos **no** son tiempo real. El dashboard debe mostrar el período de publicación.
- El proxy evita el CORS en el navegador, pero no corrige límites, cambios de esquema, permisos o interrupciones de las APIs externas.
- UN Comtrade puede no tener cobertura del producto o período solicitado, y los códigos HS no representan siempre todo el litio exportado.
- Datos Argentina devuelve un catálogo de datasets, no necesariamente la serie más reciente.
- Se devuelve error explícito si una fuente no responde: no se sustituyen datos por valores inventados.
- Vercel ejecuta Python serverless cuando recibe una petición; no se deja `python server.py` corriendo.

## Comprobación local (con Python y Flask instalado)
`python -m pip install -r requirements.txt`
`python api/index.py`
Abrí http://127.0.0.1:8765

## Archivos
- `public/index.html`: web del observatorio.
- `api/index.py`: servidor compatible con Vercel.
- `vercel.json`: rutas a Flask.
- `requirements.txt`: dependencia Python.
