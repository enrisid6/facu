Observatorio del Litio v2.1 - instalación GitHub/Vercel

Subir estos cinco archivos a la RAÍZ del repositorio, reemplazando versiones anteriores: app.py, index.html, requirements.txt, vercel.json, README.txt.
Eliminar antiguas carpetas api/ y public/ si conservan versiones anteriores.
En Vercel configurar Root Directory ./, sin build command personalizado.

Endpoints para probar tras desplegar:
/api/health
/api/status
/api/worldbank?indicator=FP.CPI.TOTL.ZG
/api/lithium?year=2024
/api/lithium/history
/api/catalog (declara expresamente no integrado)

Limitaciones: no se pudo comprobar con llamadas a producción desde este entorno; la API pública de UN Comtrade puede ser incompleta o limitar solicitudes. SIACAM sigue sin datos automáticos. No incluye precios spot verificados.
