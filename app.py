"""Observatorio del Litio: Flask API para Vercel serverless."""
from flask import Flask, request, jsonify, send_from_directory
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from pathlib import Path
import json
import time

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT
app = Flask(__name__)

WORLD_BANK_INDICATORS = ('FP.CPI.TOTL.ZG', 'BX.KLT.DINV.WD.GD.ZS', 'NY.GDP.MKTP.CD')
DATASET = 'produccion-exportaciones-argentinas-litio-tablero-global-litio---siacam'


def upstream_json(url, source):
    try:
        req = Request(url, headers={
            'User-Agent': 'ObservatorioLitio/1.4 (+academic research)',
            'Accept': 'application/json',
        })
        with urlopen(req, timeout=12) as response:
            raw = response.read(4_000_001)
            if len(raw) > 4_000_000:
                return jsonify(error='La respuesta superó el límite permitido', source=source), 502
            data = json.loads(raw)
        response = jsonify(data)
        response.headers['Cache-Control'] = 'public, s-maxage=1800, stale-while-revalidate=3600'
        return response
    except (HTTPError, URLError, OSError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return jsonify(error='Fuente externa no disponible', source=source, detail=str(exc)[:180]), 502


@app.get('/')
def homepage():
    return send_from_directory(str(PUBLIC), 'index.html')


@app.get('/api/health')
def health():
    # Sólo verifica esta función, NO los servicios de terceros.
    return jsonify(ok=True, backend='vercel-flask', sources=['worldbank', 'trade', 'catalog'],
                   note='El servidor responde. Las fuentes externas deben probarse por separado.', timestamp=int(time.time()))


@app.get('/api/worldbank')
def worldbank():
    indicator = request.args.get('indicator', '')
    if indicator not in WORLD_BANK_INDICATORS:
        return jsonify(error='Indicador no permitido'), 400
    url = f'https://api.worldbank.org/v2/country/ARG/indicator/{indicator}?format=json&per_page=80'
    return upstream_json(url, 'worldbank')


@app.get('/api/trade')
def trade():
    allowed = ('reporterCode', 'flowCode', 'cmdCode', 'period', 'partnerCode', 'aggregateBy', 'maxRecords')
    params = {key:request.args.get(key) for key in allowed if request.args.get(key) is not None}
    if params.get('reporterCode') != '32' or params.get('flowCode') != 'X' or params.get('cmdCode') != '283691' or params.get('period') not in ('2023','2024','2025','2026'):
        return jsonify(error='Consulta no permitida'), 400
    url = 'https://comtradeapi.un.org/public/v1/preview/C/A/HS?' + urlencode(params)
    return upstream_json(url, 'trade')


@app.get('/api/catalog')
def catalog():
    url = 'https://datos.gob.ar/api/3/action/package_show?' + urlencode({'id': DATASET})
    return upstream_json(url, 'catalog')


@app.route('/index.html')
@app.route('/app.py')
@app.route('/api/index.py')
def html_aliases():
    return homepage()

@app.errorhandler(404)
def not_found(error):
    # Algunos despliegues reescriben la URL raíz internamente.
    # Sólo se sirve HTML para rutas de página, nunca para endpoints /api/.
    if request.path.startswith('/api/'):
        return jsonify(error='Ruta API inexistente', path=request.path), 404
    return homepage()



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8765, debug=True)
