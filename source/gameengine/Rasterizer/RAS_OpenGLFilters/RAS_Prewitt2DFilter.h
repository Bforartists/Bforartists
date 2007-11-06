#ifndef __RAS_PREWITT2DFILTER
#define __RAS_PREWITT2DFILTER

char * PrewittFragmentShader=STRINGIFY(
uniform sampler2D bgl_RenderedTexture;
uniform vec2 bgl_TextureCoordinateOffset[9];

void main(void)
{
    vec4 sample[9];

    for (int i = 0; i < 9; i++)
    {
        sample[i] = texture2D(bgl_RenderedTexture, 
                              gl_TexCoord[0].st + bgl_TextureCoordinateOffset[i]);
    }

    vec4 horizEdge = sample[2] + sample[5] + sample[8] -
                     (sample[0] + sample[3] + sample[6]);

    vec4 vertEdge = sample[0] + sample[1] + sample[2] -
                    (sample[6] + sample[7] + sample[8]);

    gl_FragColor.rgb = sqrt((horizEdge.rgb * horizEdge.rgb) + 
                            (vertEdge.rgb * vertEdge.rgb));
    gl_FragColor.a = 1.0;
}

);
#endif

