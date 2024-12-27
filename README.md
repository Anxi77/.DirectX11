# DirectX 11 Graphics Engine

## Today's TODO (2024-03-21)

<details>
<summary>셰이더 시스템 기초 작업</summary>

* [ ] 프로젝트에 Shader 폴더 생성
* [ ] 기본 버텍스 셰이더 파일 생성
  * [ ] 단순 위치 정보만 처리하는 기본 셰이더 작성
  * [ ] 색상 정보를 포함하는 확장 셰이더 작성
* [ ] 기본 픽셀 셰이더 파일 생성
  * [ ] 단색 출력 셰이더 작성
  * [ ] 버텍스 색상 출력 셰이더 작성
</details>

<details>
<summary>기본 도형 렌더링 준비</summary>

* [ ] Vertex 구조체 정의
  * [ ] 위치 정보 구조체
  * [ ] 색상 정보 포함 구조체
* [ ] VertexBuffer 클래스 기본 구조 작성
  * [ ] 생성자/소멸자 구현
  * [ ] 버퍼 생성 메서드 구현
  * [ ] 버퍼 바인딩 메서드 구현
</details>

<details>
<summary>첫 도형 렌더링 목표</summary>

* [ ] 화면에 단일 점 그리기
* [ ] 화면에 선 그리기
* [ ] 화면에 삼각형 그리기
</details>

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

## TODO List

<details>
<summary>1. 셰이더 시스템 구현</summary>

* [ ] Shader 클래스 생성
  * [ ] 기본 셰이더 파일 구조 설정 (.hlsl)
  * [ ] 버텍스 셰이더 로더 구현
  * [ ] 픽셀 셰이더 로더 구현
  * [ ] 셰이더 컴파일러 구현
  * [ ] 셰이더 에러 핸들링
</details>

<details>
<summary>2. 버퍼 관리 시스템</summary>

* [ ] VertexBuffer 클래스 구현
  * [ ] 정점 구조체 정의
  * [ ] 버퍼 생성 기능
  * [ ] 버퍼 업데이트 기능
* [ ] IndexBuffer 클래스 구현
  * [ ] 인덱스 버퍼 생성
  * [ ] 인덱스 데이터 관리
</details>

<details>
<summary>3. 기본 도형 렌더링</summary>

* [ ] Primitive 클래스 구현
  * [ ] 점 그리기 기능
    * [ ] 단일 점 렌더링
    * [ ] 다중 점 렌더링
  * [ ] 선 그리기 기능
    * [ ] 단일 선 렌더링
    * [ ] 연결된 선 렌더링
  * [ ] 삼각형 그리기 기능
    * [ ] 단일 삼각형
    * [ ] 삼각형 스트립
  * [ ] 사각형 그리기 기능
</details>

<details>
<summary>4. 입력 시스템</summary>

* [ ] Input 클래스 구현
  * [ ] 키보드 입력 처리
  * [ ] 마우스 입력 처리
  * [ ] 입력 상태 관리
</details>

<details>
<summary>5. 수학 유틸리티</summary>

* [ ] Math 네임스페이스 구현
  * [ ] Vector2/3/4 구현
  * [ ] Matrix 구현
  * [ ] 변환 행렬 유틸리티 함수
  * [ ] 수학 헬퍼 함수
</details>

<details>
<summary>6. 리소스 관리</summary>

* [ ] ResourceManager 클래스 구현
  * [ ] 셰이더 리소스 관리
  * [ ] 버퍼 리소스 관리
  * [ ] 메모리 누수 방지
</details>

<details>
<summary>7. 디버깅 시스템</summary>

* [ ] Debug 클래스 구현
  * [ ] DirectX 디버그 레이어 활성화
  * [ ] 에러 로깅 시스템
  * [ ] 성능 측정 도구
  * [ ] 디버그 렌더링 기능
</details>

<details>
<summary>8. 최적화</summary>

* [ ] 성능 프로파일링 구현
* [ ] 렌더링 상태 캐싱
* [ ] 배치 처리 시스템
* [ ] 메모리 풀링
</details>

## 다음 단계 구현 사항

1. 셰이더 관리 클래스 생성
   - 셰이더 파일 로딩
   - 셰이더 컴파일
   - 셰이더 리소스 관리

2. 정점 버퍼 관리 클래스 생성
   - 버퍼 생성 및 관리
   - 다양한 정점 형식 지원
   - 동적 버퍼 업데이트

3. 기본 도형 렌더링 구현
   - 점 그리기
   - 선 그리기
   - 삼각형 그리기
   - 사각형 그리기

## 빌드 요구사항

- Visual Studio 2019 이상
- Windows SDK 10.0
- CMake 3.20 이상

## 빌드 방법

- bash
- mkdir build
- cd build
- cmake ..
- cmake --build .

## 참고 자료

- [DirectX 11 Programming Guide](https://docs.microsoft.com/en-us/windows/win32/direct3d11/atoc-dx-graphics-direct3d-11)
- [MSDN DirectX Graphics Documentation](https://docs.microsoft.com/en-us/windows/win32/directx)
- [Frank Luna's Introduction to 3D Game Programming with DirectX 11](http://www.d3dcoder.net/d3d11.htm)
