#pragma pack_matrix(row_major)

struct PSInput
{
    float4 position : SV_POSITION;
    float4 color : COLOR;
};

float4 main() : SV_TARGET
{
    return float4(1.0f, 0.0f, 0.0f, 1.0f);  // 빨간색 출력
} 