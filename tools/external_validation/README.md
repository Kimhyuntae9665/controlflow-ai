# 외부 양식으로 기존 엔진을 시험하기

이 시험기는 기존 `engine.py` 함수를 불러와 서로 다른 공개 PDF 양식을 읽습니다. 원래 앱의 `evidence/`, `runs/current.json`, 검토 이력을 변경하지 않습니다. 테스트 코드는 Codex의 지원으로 작성했습니다.

[2026-10-13 결과 보고서](../../docs/external-tests-20261013/report.md) · [저장 결과 화면](../../docs/external-tests-20261013/index.html)

## 준비

프로젝트 README의 Python 의존성을 설치하고, `127.0.0.1:11435`에서 Ollama의 `qwen2.5:1.5b`를 사용할 수 있게 합니다. 다른 모델로 자동 대체하지 않습니다.

프로젝트 루트에서 아래를 실행하세요. Windows는 `python` 대신 `.venv/Scripts/python.exe -X utf8`을 사용할 수 있습니다.

```powershell
python tools/external_validation/prepare.py
python tools/external_validation/build_inputs.py
python tools/external_validation/run_external.py
python tools/external_validation/test_formats.py
```

다운로드와 결과는 Git에서 제외된 `external-test-output/`에 저장됩니다. 약 60MB의 원본 자료와 미리보기·모델 응답을 저장할 공간이 필요합니다. 이전 실행 응답이 있으면 덮어쓰지 않고 중단합니다. 기존 폴더 이름을 `external-test-output-보관날짜` 등으로 바꿔 보존한 뒤 다시 실행하세요. 일부 공식 URL은 변경되거나 접근이 제한될 수 있으므로 실패 기록과 지문을 확인하세요. 샘플 문서의 과거 세율을 현재 세법으로 적용하는 시험은 아닙니다.

실행 결과의 `errors`에 실패가 있을 때만 한 번 명시적으로 재실행합니다. 원래 실패를 보존하며 모델·추출 지침·원문 검증을 바꾸지 않습니다.

```powershell
python tools/external_validation/retest_failed.py
```

그 뒤 원문 파일 지문, 실제 마지막 모델 출력, 분리된 모집단의 조서 출력 차단을 확인하고 보고서를 만듭니다.

```powershell
python tools/external_validation/post_verify.py
python tools/external_validation/write_report.py
python tools/external_validation/build_report.py
```

`external-test-output/index.html`을 브라우저로 열면 원문 페이지와 추출·통제 결과를 비교할 수 있습니다. 공개 저장소의 결과 화면에는 제3자 PDF 전체와 전체 원문 텍스트를 넣지 않았으며 출처 링크를 제공합니다.

## 해석 범위

- 외부 원본 8개, 같은 원본의 이미지 변환 2개, 합성 기준점 6개를 따로 집계합니다.
- 외부 문서에는 원래 없는 발주·입고·승인 정보가 있습니다. 고정 9개 항목 전체를 일반적인 값 정확도의 분모로 사용하지 않습니다.
- 원문 근거 수, 실제 값·누락 정답 대조, 상태 초안 형식 검증은 서로 다른 지표입니다.
- XML/JSON은 문서 읽기 단계만 시험합니다. 전자송장 스키마나 전자서명 검증 결과로 표시하지 않습니다.
- 모델 HTTP 실패를 fixture 값이나 모의 응답으로 바꾸지 않습니다. 마지막 선택 모델 응답을 보고서 값과 직접 대조합니다.
- 원본·변환·합성 그룹을 따로 계산하고, 실제 `Engine.review()` / `Engine.export()`도 그룹별 격리 경로에서 호출합니다. 변환본이 원본의 중복 지급처럼 보이지 않게 했습니다.
- 동일한 seed·temperature가 모든 Ollama·OCR·운영체제 버전에서 같은 출력을 보장하지는 않습니다. 2026-10-13 수치는 해당 저장 실행의 결과입니다.
