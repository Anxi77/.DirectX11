#pragma once
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <d3d11.h>
#include <directxmath.h>
#include <iostream>
#include <vector>
#include <string>
#include <algorithm>

// DirectX 그래픽스 관리 클래스
// 렌더링 파이프라인과 그래픽스 리소스를 초기화하고 관리
class Graphics
{
public:
    Graphics();
    ~Graphics();

    // DirectX 초기화 함수
    // hwnd: 렌더링할 윈도우 핸들
    // width, height: 렌더링 영역의 크기
    bool Initialize(HWND hwnd, int width, int height);
    
    // 프레임 렌더링 함수
    void Render();
    
    // 그래픽스 리소스 정리 함수
    void Cleanup();

private:
    ID3D11Device *device;              // 그래픽 디바이스: 리소스 생성 및 관리
    ID3D11DeviceContext *deviceContext; // 디바이스 컨텍스트: 렌더링 명령 실행
    IDXGISwapChain *swapChain;         // 스왑 체인: 더블 버퍼링 관리
    ID3D11RenderTargetView *renderTargetView; // 렌더 타겟 뷰: 렌더링 출력 대상

    // 셰이더 관련 멤버 변수
    ID3D11VertexShader* vertexShader;
    ID3D11PixelShader* pixelShader;
    ID3D11InputLayout* inputLayout;

    bool LoadShaders();  // 셰이더 로드 함수 추가
};