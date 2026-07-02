# 복지지출 잔차 LISA 3D 지도

시군구 1인당 복지지출 결산액 회귀 잔차의 국지적 공간자기상관(Local Moran's I, LISA)을
3D 인터랙티브 지도로 보여주는 대시보드입니다. GitHub Pages로 서비스됩니다.

## 구성

```
├── index.html                  대시보드 (MapLibre GL JS, 토큰 불필요)
├── data/
│   ├── boundaries.json         시군구/시도 경계 (gpkg에서 생성, 고정)
│   └── values.json             변수값 (엑셀에서 자동 생성)
├── upload/
│   └── 잔차LISA_데이터.xlsx      ★ 데이터 업데이트용 엑셀 (여기에 새 파일 업로드)
├── tools/
│   ├── make_from_gpkg.py       gpkg → boundaries.json + 엑셀 템플릿 (로컬 1회)
│   └── build_values.py         엑셀 → values.json 변환
└── .github/workflows/update-data.yml   엑셀 업로드 시 자동 변환
```

## 최초 배포 (1회)

1. GitHub에서 새 저장소 생성 (예: `lisa-dashboard`, Public)
2. 이 폴더를 푸시:
   ```
   git remote add origin https://github.com/<계정명>/lisa-dashboard.git
   git push -u origin main
   ```
3. 저장소 **Settings → Pages → Source: Deploy from a branch**,
   Branch: `main` / `(root)` 선택 후 저장
4. 1~2분 뒤 `https://<계정명>.github.io/lisa-dashboard/` 에서 접속 가능

## 데이터 업데이트 방법 (엑셀 업로드)

1. `upload/잔차LISA_데이터.xlsx`를 내려받아 값 수정 (또는 같은 형식으로 새로 작성)
2. GitHub 저장소 웹화면에서 `upload` 폴더 열기 → **Add file → Upload files** 로 업로드 → Commit
3. GitHub Actions가 자동으로 `data/values.json`을 재생성해서 커밋 (Actions 탭에서 진행 확인)
4. 1~2분 뒤 대시보드에 반영됨 (브라우저 새로고침)

### 엑셀 형식 (첫 번째 시트)

| 열 | 설명 |
|---|---|
| `SIGUNGU_CD` | 시군구 코드 (5자리) — 경계 데이터와 매칭 키 |
| `SIGUNGU_NM` | 시군구명 |
| `시도명` | 시도명 |
| `{변수명}_resid` | 잔차값 (숫자) |
| `{변수명}_residLISA_clu` | LISA 군집: `HH(양+ 군집)` / `LL(음- 군집)` / `HL(고립 과다)` / `LH(고립 과소)` / `비유의` |
| `{변수명}_residLISA_p` | 유사 p값 |
| `{변수명}_residLISA_FDR유의` | FDR 보정 유의 여부 (TRUE/FALSE) |

변수 열 세트(4개 묶음)는 자유롭게 추가/삭제할 수 있으며 `*_resid` 열을 기준으로
자동 인식됩니다. 대시보드의 변수 버튼도 자동으로 늘어나거나 줄어듭니다.

## 경계(지오메트리)가 바뀌는 경우

행정구역 개편 등으로 경계 자체가 바뀌면 로컬에서 재생성 후 커밋:

```
conda activate spatial
python tools/make_from_gpkg.py <새 gpkg 경로>
git add data/boundaries.json upload/
git commit -m "경계 데이터 갱신" && git push
```

## 로컬에서 미리보기

`file://`로는 데이터 fetch가 막히므로 간이 서버로 실행:

```
python -m http.server 8000
# 브라우저에서 http://localhost:8000
```
