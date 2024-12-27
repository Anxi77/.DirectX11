# DirectX 11 Graphics Engine

DirectX 11을 사용한 기초적인 그래픽스 엔진 프로젝트입니다.

## 프로젝트 구조

- `src/Window.h`, `src/Window.cpp`: 윈도우 생성 및 관리
- `src/Graphics.h`, `src/Graphics.cpp`: DirectX 그래픽스 초기화 및 렌더링
- `src/main.cpp`: 프로그램 진입점

## 학습 로드맵

1. **기초 설정** (현재 단계)
   - 윈도우 생성
   - DirectX 초기화
   - 기본 렌더링 파이프라인 설정

2. **셰이더 프로그래밍**
   - 버텍스 셰이더 작성
   - 픽셀 셰이더 작성
   - HLSL 기초 학습

3. **기본 도형 렌더링**
   - 정점 버퍼 생성
   - 인덱스 버퍼 사용
   - 기본 도형 (점, 선, 삼각형) 그리기

4. **변환 행렬**
   - World 변환
   - View 변환
   - Projection 변환
   - 카메라 시스템 구현

5. **텍스처와 조명**
   - 텍스처 로딩 및 매핑
   - 기본 조명 모델 구현
   - 재질 시스템 구현

6. **고급 기능**
   - 인스턴싱
   - 파티클 시스템
   - 포스트 프로세싱
   - 그림자 렌더링

## 참고 자료

- [DirectX 11 Programming Guide](https://docs.microsoft.com/en-us/windows/win32/direct3d11/atoc-dx-graphics-direct3d-11)
- [MSDN DirectX Graphics Documentation](https://docs.microsoft.com/en-us/windows/win32/directx)
- [Frank Luna's Introduction to 3D Game Programming with DirectX 11](http://www.d3dcoder.net/d3d11.htm)
