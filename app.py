"""Observatorio del Litio - Flask compatible con Vercel.
Los datos se obtienen al consultar fuentes oficiales. No se inventan cifras.
"""
from flask import Flask, jsonify, request, send_file
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from pathlib import Path
import json, time

app=Flask(__name__)
ROOT=Path(__file__).parent
INDICATORS={'FP.CPI.TOTL.ZG','BX.KLT.DINV.WD.GD.ZS','NY.GDP.MKTP.CD'}

def fetch_json(url):
    req=Request(url,headers={'User-Agent':'ObservatorioLitio/2.0 (public academic dashboard)','Accept':'application/json'})
    with urlopen(req,timeout=11) as response:
        data=response.read(2_500_001)
        if len(data)>2_500_000: raise ValueError('Respuesta demasiado extensa')
        return json.loads(data)

def failure(source, exc):
    return jsonify(error='Fuente externa no disponible',source=source,detail=str(exc)[:250]),502

@app.get('/')
@app.get('/index.html')
def index(): return send_file(ROOT/'index.html')

@app.get('/api/health')
def health():
    return jsonify(ok=True,backend='flask-vercel',build='2.1',note='Este endpoint no prueba las fuentes externas.')

@app.get('/api/worldbank')
def worldbank():
    ind=request.args.get('indicator','')
    if ind not in INDICATORS:return jsonify(error='Indicador no permitido'),400
    try:
        result=fetch_json(f'https://api.worldbank.org/v2/country/ARG/indicator/{ind}?format=json&per_page=80')
        if not isinstance(result,list) or len(result)<2 or not isinstance(result[1],list):raise ValueError('Formato Banco Mundial inesperado')
        resp=jsonify(result)
        resp.headers['Cache-Control']='public, s-maxage=3600'
        return resp
    except (HTTPError,URLError,ValueError,OSError,TimeoutError) as exc:return failure('worldbank',exc)

def comtrade(year,partner='0'):
    params={'reporterCode':'32','flowCode':'X','cmdCode':'283691','period':str(year),'partnerCode':partner,'maxRecords':'500'}
    return fetch_json('https://comtradeapi.un.org/public/v1/preview/C/A/HS?'+urlencode(params))

def records(j):
    return j.get('data',[]) if isinstance(j,dict) and isinstance(j.get('data'),list) else []

@app.get('/api/lithium')
def lithium():
    y=request.args.get('year','latest')
    if y not in {'latest','2023','2024','2025','2026'}:return jsonify(error='Año no permitido'),400
    errors=[]
    for year in ([2025,2024,2023] if y=='latest' else [int(y)]):
        try:
            rows=records(comtrade(year))
            world=next((p for p in rows if str(p.get('partnerCode'))=='0' and isinstance(p.get('primaryValue'),(int,float)) and p['primaryValue']>0),None)
            if not world: errors.append(f'{year}: sin dato FOB total');continue
            quantity=world.get('netWgt') if isinstance(world.get('netWgt'),(int,float)) else None
            partners=[]
            try:
                for p in records(comtrade(year,'all')):
                    if p.get('partnerCode') in (0,'0',None) or not isinstance(p.get('primaryValue'),(float,int)) or p['primaryValue']<=0:continue
                    partners.append({'code':p['partnerCode'],'name':p.get('partnerDesc') or f'País código {p["partnerCode"]}','value_usd':p['primaryValue']})
                partners.sort(key=lambda x:x['value_usd'],reverse=True)
            except Exception:pass # El total mundial se conserva aunque falle el desglose
            res=jsonify(status='ok',source='UN Comtrade',dataset='public/v1/preview/C/A/HS',reporter='Argentina',product_code='283691',product='Carbonato de litio',year=year,total={'value_usd':world['primaryValue'],'net_kg':quantity},partners=partners,partner_detail_complete=False,warning='Datos aduaneros HS 283691; no equivalen al total de litio exportado. La vista previa puede ser parcial.')
            res.headers['Cache-Control']='public, s-maxage=3600'
            return res
        except (HTTPError,URLError,ValueError,OSError,TimeoutError) as exc:errors.append(f'{year}: {str(exc)[:100]}')
    return jsonify(status='unavailable',error='; '.join(errors),source='UN Comtrade'),502

@app.get('/api/trade')
def trade_legacy():
    year=request.args.get('period','2024')
    if year not in {'2023','2024','2025','2026'}:return jsonify(error='Año no permitido'),400
    partner=request.args.get('partnerCode','0')
    if partner not in {'0','all'}:return jsonify(error='Socio no permitido'),400
    try:return jsonify(comtrade(year,partner))
    except (HTTPError,URLError,ValueError,OSError,TimeoutError) as exc:return failure('trade',exc)

@app.get('/api/catalog')
def catalog():
    return jsonify(status='not_integrated',source='SIACAM',error='Este conjunto todavía no tiene un recurso CSV comprobado y procesado. El catálogo anterior devolvía 404.',url='https://datos.gob.ar/ar/dataset/produccion-exportaciones-argentinas-litio-tablero-global-litio---siacam'),200


@app.get('/api/lithium/history')
def lithium_history():
    result=[];errors=[]
    for y in (2022,2023,2024,2025):
        try:
            candidates=records(comtrade(y,'0'))
            row=next((r for r in candidates if str(r.get('partnerCode'))=='0' and isinstance(r.get('primaryValue'),(int,float)) and r['primaryValue']>0),None)
            if not row:errors.append(f'{y}: no publicado en vista previa');continue
            result.append({'year':y,'value_usd':row['primaryValue'],'net_kg':row.get('netWgt') if isinstance(row.get('netWgt'),(float,int)) else None,'classification':row.get('classificationCode'),'is_reported':row.get('isReported')})
        except Exception as exc:errors.append(f'{y}: {str(exc)[:100]}')
    response=jsonify(status='ok' if result else 'unavailable',source='UN Comtrade (vista previa)',product='Carbonato de litio',hs='283691',rows=result,errors=errors,warning='La vista previa puede contener estimaciones; no corresponde al total del sector litio.')
    response.headers['Cache-Control']='public, s-maxage=3600'
    return response if result else (response,502)

@app.get('/api/status')
def api_status():
    return jsonify(backend='online',worldbank='endpoint disponible: consultar /api/worldbank',comtrade='endpoint disponible: consultar /api/lithium/history',siacam='no integrado: recurso CSV pendiente de verificar',usgs='datos anuales de referencia, sin API en vivo',version='2.1')

@app.errorhandler(404)
def missing(e):return jsonify(error='Ruta no encontrada',path=request.path),404

if __name__=='__main__':app.run(port=8765,debug=True)
