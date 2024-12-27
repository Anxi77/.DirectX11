#pragma once
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <string>

// 윈도우 관리 클래스
// 윈도우 생성, 메시지 처리, 윈도우 이벤트 관리
class Window
{
public:
    Window();
    ~Window();

    // 윈도우 초기화 함수
    // title: 윈도우 제목
    // width, height: 윈도우 크기
    bool Initialize(const wchar_t *title, int width, int height);
    
    // 윈도우 핸들 반환
    HWND GetHandle() const { return hwnd; }
    
    // 윈도우 메시지 처리 함수
    // false 반환 시 프로그램 종료
    bool ProcessMessages();

private:
    HWND hwnd; // 윈도우 핸들

    // 윈도우 프로시저: 윈도우 메시지 처리 함수
    static LRESULT CALLBACK WindowProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam);
};