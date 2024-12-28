#pragma pack_matrix(row_major)

struct VSInput
{
    float3 position : POSITION;
    float4 color : COLOR;
};

struct VSOutput
{
    float4 position : SV_POSITION;
    float4 color : COLOR;
};

VSOutput main(VSInput input)
{
    VSOutput output;
    output.position = float4(input.position.x, input.position.y, input.position.z, 1.0f);
    output.color = input.color;
    return output;
} 