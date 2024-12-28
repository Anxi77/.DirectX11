#pragma pack_matrix(row_major)

float4 main(float3 pos : POSITION) : SV_POSITION
{
    return float4(pos, 1.0f);  // 입력된 위치를 그대로 출력
} 