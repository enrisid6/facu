# Observatorio del Litio — V1.5 (Vercel)

## Corrección del error FLASK_ENTRYPOINT_NOT_FOUND
Se movió la aplicación Flask a `app.py` en la raíz del proyecto, como requiere la detección automática actual de Vercel. Se eliminó el rewrite antiguo `/api/:path* -> /api/index`.

## Publicar
1. Subí **el contenido** de esta carpeta directamente a la raíz del repositorio GitHub (el mismo nivel de `app.py`, `vercel.json`, `requirements.txt` y `public/`).
2. En Vercel, Framework Preset: Flask (si se detecta automáticamente), Root Directory: `./`.
3. Quitá comandos personalizados de build o output.
4. Redeploy desde el commit actualizado.
5. Revisá `/api/health`, `/api/worldbank?indicator=FP.CPI.TOTL.ZG` y `/api/catalog`.

No se probó aún el build remoto ni la conectividad de los servicios terceros. Si Vercel no detecta `app.py`, comprobá en GitHub que esté realmente en la raíz que Vercel considera Root Directory.

Para ejecución local: `pip install -r requirements.txt` y `python app.py`.
