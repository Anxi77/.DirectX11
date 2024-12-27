#include "Window.h"

Window::Window() : hwnd(nullptr)
{
}

Window::~Window()
{
    if (hwnd)
    {
        DestroyWindow(hwnd);
    }
}

// 윈도우 프로시저: 윈도우 메시지를 처리하는 콜백 함수
// hwnd: 메시지를 받은 윈도우의 핸들
// msg: 메시지 타입 (WM_CREATE, WM_DESTROY 등)
// wParam, lParam: 메시지와 함께 전달되는 추가 데이터
LRESULT CALLBACK Window::WindowProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam)
{
    switch (msg)
    {
    case WM_CLOSE: // 윈도우 닫기 버튼 클릭 시
        DestroyWindow(hwnd);
        return 0;
    case WM_DESTROY:        // 윈도우가 파괴될 때
        PostQuitMessage(0); // 메시지 루프를 종료하도록 WM_QUIT 메시지를 포스트
        return 0;
    }
    return DefWindowProc(hwnd, msg, wParam, lParam); // 기본 메시지 처리
}

bool Window::Initialize(const wchar_t *title, int width, int height)
{
    // 1. 윈도우 클래스 정의
    WNDCLASSEXW wc = {};                     // 윈도우 클래스 구조체 초기화
    wc.cbSize = sizeof(WNDCLASSEXW);         // 구조체 크기
    wc.lpfnWndProc = WindowProc;             // 윈도우 프로시저 함수 지정
    wc.hInstance = GetModuleHandle(nullptr); // 현재 프로그램의 인스턴스 핸들
    wc.lpszClassName = L"DX11WindowClass";   // 윈도우 클래스 이름

    // 2. 윈도우 클래스 등록
    // Windows에 여기서 정의한 윈도우 클래스를 등록
    if (!RegisterClassExW(&wc))
    {
        return false; // 등록 실패 시
    }

    // 3. 윈도우 생성
    hwnd = CreateWindowExW(
        0,                        // 확장 윈도우 스타일
        L"DX11WindowClass",       // 등록된 클래스 이름
        title,                    // 윈도우 제목
        WS_OVERLAPPEDWINDOW,      // 기본 윈도우 스타일 (최소화/최대화/크기조절 가능)
        CW_USEDEFAULT,            // X 위치 (기본값)
        CW_USEDEFAULT,            // Y 위치 (기본값)
        width,                    // 윈도우 너비
        height,                   // 윈도우 높이
        nullptr,                  // 부모 윈도우 없음
        nullptr,                  // 메뉴 없음
        GetModuleHandle(nullptr), // 프로그램 인스턴스 핸들
        nullptr);                 // 추가 데이터 없음

    // 윈도우 생성 실패 체크
    if (!hwnd)
    {
        return false;
    }

    // 4. 윈도우를 화면에 표시
    ShowWindow(hwnd, SW_SHOW);
    return true;
}

// 윈도우 메시지 처리 함수
bool Window::ProcessMessages()
{
    MSG msg = {};
    // PeekMessage: 메시지 큐에서 메시지를 확인
    // PM_REMOVE: 메시지를 큐에서 제거
    while (PeekMessage(&msg, nullptr, 0, 0, PM_REMOVE))
    {
        if (msg.message == WM_QUIT) // 종료 메시지 수신 시
        {
            return false; // 프로그램 종료를 위해 false 반환
        }
        TranslateMessage(&msg); // 키보드 입력 메시지 변환
        DispatchMessage(&msg);  // 윈도우 프로시저로 메시지 전달
    }
    return true; // 계속 실행
}