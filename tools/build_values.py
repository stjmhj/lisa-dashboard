# -*- coding: utf-8 -*-
"""
upload/ 폴더의 엑셀 → data/values.json 변환

GitHub Actions에서 엑셀 업로드 시 자동 실행되고, 로컬에서도 실행 가능:
  python tools/build_values.py [엑셀경로]

엑셀 형식 (첫 번째 시트):
  필수 열: SIGUNGU_CD, SIGUNGU_NM, 시도명
  변수 열: {변수명}_resid                  잔차값 (숫자)
          {변수명}_residLISA_clu          LISA 군집 (HH(양+ 군집) / LL(음- 군집) /
                                          HL(고립 과다) / LH(고립 과소) / 비유의)
          {변수명}_residLISA_p            유사 p값 (숫자)
          {변수명}_residLISA_FDR유의       FDR 보정 유의 여부 (TRUE/FALSE)
변수 열 세트는 자유롭게 추가/삭제 가능 — *_resid 열 기준으로 자동 인식된다.
"""
import sys, os, io, json, glob
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_excel():
    files = sorted(glob.glob(os.path.join(ROOT, 'upload', '*.xlsx')),
                   key=os.path.getmtime, reverse=True)
    files = [f for f in files if not os.path.basename(f).startswith('~$')]
    if not files:
        sys.exit('오류: upload/ 폴더에 .xlsx 파일이 없습니다.')
    return files[0]


def label_of(base):
    """열 이름에서 표시용 라벨 생성: 인당_B_사회복지 → 1인당 사회복지, B_보건 → 보건"""
    lb = base
    pc = lb.startswith('인당_')          # 1인당(per-capita) 여부 구분
    if pc:
        lb = lb[len('인당_'):]
    for pre in ('B_', '부문_'):
        if lb.startswith(pre):
            lb = lb[len(pre):]
    if lb.endswith('_B'):
        lb = lb[:-2]
    return ('1인당 ' + lb) if pc else lb


def to_bool(v):
    if isinstance(v, bool):
        return v
    s = str(v).strip().upper()
    return s in ('TRUE', '1', '1.0', 'T', 'Y', 'O', '예')


def main():
    xlsx = sys.argv[1] if len(sys.argv) > 1 else find_excel()
    print('입력 엑셀:', xlsx)
    df = pd.read_excel(xlsx, sheet_name=0)

    required = ['SIGUNGU_CD', 'SIGUNGU_NM', '시도명']
    missing = [c for c in required if c not in df.columns]
    if missing:
        sys.exit(f'오류: 필수 열 누락 {missing}')

    df['SIGUNGU_CD'] = df['SIGUNGU_CD'].astype(str).str.split('.').str[0].str.zfill(5)

    bases = [c[:-len('_resid')] for c in df.columns if c.endswith('_resid')]
    if not bases:
        sys.exit('오류: *_resid 형식의 변수 열이 없습니다.')
    print(f'변수 {len(bases)}개 인식:', ', '.join(bases))

    variables = [{'key': b, 'label': label_of(b)} for b in bases]

    regions = {}
    for _, row in df.iterrows():
        code = row['SIGUNGU_CD']
        entry = {'name': str(row['SIGUNGU_NM']), 'sido': str(row['시도명']), 'v': {}}
        for b in bases:
            resid = row.get(b + '_resid')
            clu = row.get(b + '_residLISA_clu')
            p = row.get(b + '_residLISA_p')
            fdr = row.get(b + '_residLISA_FDR유의')
            entry['v'][b] = {
                'resid': None if pd.isna(resid) else round(float(resid), 2),
                'clu': '비유의' if pd.isna(clu) else str(clu),
                'p': None if pd.isna(p) else round(float(p), 4),
                'fdr': False if pd.isna(fdr) else to_bool(fdr),
            }
        regions[code] = entry

    out = {
        'source': os.path.basename(xlsx),
        'variables': variables,
        'regions': regions,
    }
    os.makedirs(os.path.join(ROOT, 'data'), exist_ok=True)
    vpath = os.path.join(ROOT, 'data', 'values.json')
    with open(vpath, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print(f'생성 완료: {vpath} (지역 {len(regions)}개, 변수 {len(bases)}개)')

    # 검증 리포트
    n_null = sum(1 for r in regions.values() for v in r['v'].values() if v['resid'] is None)
    if n_null:
        print(f'경고: 잔차값 결측 {n_null}건 (지도에서 회색 처리됨)')


if __name__ == '__main__':
    main()
