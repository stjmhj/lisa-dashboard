# -*- coding: utf-8 -*-
"""
잔차LISA_전체.gpkg → 대시보드용 초기 데이터 생성 (로컬에서 1회 실행)

생성물:
  data/boundaries.json      시군구/시도 경계 (GeoJSON, WGS84, 단순화)
  upload/잔차LISA_데이터.xlsx  속성 테이블 엑셀 (데이터 업데이트용 템플릿)

이후 데이터 갱신은 upload/ 폴더에 같은 형식의 엑셀을 올리면
tools/build_values.py (GitHub Actions)가 data/values.json을 재생성한다.

실행 (spatial conda 환경):
  python tools/make_from_gpkg.py [gpkg경로]
"""
import sys, io, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import geopandas as gpd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPKG = sys.argv[1] if len(sys.argv) > 1 else \
    r'C:\Users\KH\Documents\spatial_project\output\sgg_weight_output\잔차LISA_전체.gpkg'

SGG_SIMPLIFY_M = 150   # 시군구 경계 단순화 허용오차 (m, EPSG:5186)
SIDO_SIMPLIFY_M = 200


def round_coords(obj, nd=5):
    if isinstance(obj, (list, tuple)):
        if obj and isinstance(obj[0], (int, float)):
            return [round(float(v), nd) for v in obj]
        return [round_coords(v, nd) for v in obj]
    return obj


def fc_to_json(gdf, prop_map, nd=5):
    """GeoDataFrame → GeoJSON dict (좌표 반올림, 지정 속성만)."""
    feats = []
    for _, row in gdf.iterrows():
        geom = row.geometry.__geo_interface__
        feats.append({
            'type': 'Feature',
            'properties': {out: row[src] for out, src in prop_map.items()},
            'geometry': {'type': geom['type'],
                         'coordinates': round_coords(geom['coordinates'], nd)},
        })
    return {'type': 'FeatureCollection', 'features': feats}


def main():
    print('reading', GPKG)
    g = gpd.read_file(GPKG)
    g['SIGUNGU_CD'] = g['SIGUNGU_CD'].astype(str).str.zfill(5)

    # --- 시군구 경계 ---
    sgg = g[['SIGUNGU_CD', 'SIGUNGU_NM', '시도명', 'geometry']].copy()
    sgg['geometry'] = sgg.geometry.simplify(SGG_SIMPLIFY_M, preserve_topology=True)
    sgg = sgg.to_crs(4326)
    sgg_fc = fc_to_json(sgg, {'code': 'SIGUNGU_CD', 'name': 'SIGUNGU_NM', 'sido': '시도명'})

    # --- 시도 경계 (dissolve) ---
    sido = g[['시도명', 'geometry']].dissolve(by='시도명').reset_index()
    sido['geometry'] = sido.geometry.simplify(SIDO_SIMPLIFY_M, preserve_topology=True)
    sido = sido.to_crs(4326)
    sido_fc = fc_to_json(sido, {'name': '시도명'})

    # --- 라벨 좌표 (대표점) ---
    pts = g.copy()
    pts['geometry'] = pts.geometry.representative_point()
    pts = pts.to_crs(4326)
    sgg_labels = {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature',
         'properties': {'name': r['SIGUNGU_NM'], 'sido': r['시도명']},
         'geometry': {'type': 'Point',
                      'coordinates': [round(r.geometry.x, 5), round(r.geometry.y, 5)]}}
        for _, r in pts.iterrows()]}

    spts = g[['시도명', 'geometry']].dissolve(by='시도명').reset_index()
    spts['geometry'] = spts.geometry.representative_point()
    spts = spts.to_crs(4326)
    sido_labels = {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature', 'properties': {'name': r['시도명']},
         'geometry': {'type': 'Point',
                      'coordinates': [round(r.geometry.x, 5), round(r.geometry.y, 5)]}}
        for _, r in spts.iterrows()]}

    out = {'sgg': sgg_fc, 'sido': sido_fc,
           'sggLabels': sgg_labels, 'sidoLabels': sido_labels}
    os.makedirs(os.path.join(ROOT, 'data'), exist_ok=True)
    bpath = os.path.join(ROOT, 'data', 'boundaries.json')
    with open(bpath, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print('wrote', bpath, f'{os.path.getsize(bpath)/1e6:.1f} MB')

    # --- 엑셀 템플릿 (속성 테이블 전체) ---
    os.makedirs(os.path.join(ROOT, 'upload'), exist_ok=True)
    xpath = os.path.join(ROOT, 'upload', '잔차LISA_데이터.xlsx')
    df = g.drop(columns='geometry')
    df.to_excel(xpath, index=False, sheet_name='데이터')
    print('wrote', xpath, len(df), 'rows')


if __name__ == '__main__':
    main()
