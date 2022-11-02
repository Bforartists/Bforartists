/* Preprocess the input of the blur filter by squaring it in its alpha straight form, assuming the
 * given color is alpha premultiplied. */
vec4 gamma_correct_blur_input(vec4 color)
{
  /* Unpremultiply alpha. */
  color.rgb /= color.a > 0.0 ? color.a : 1.0;

  /* Square color channel if it is positive, otherwise zero it. */
  color.rgb *= mix(color.rgb, vec3(0.0), lessThan(color.rgb, vec3(0.0)));

  /* Premultiply alpha to undo previous alpha unpremultiplication. */
  color.rgb *= color.a > 0.0 ? color.a : 1.0;

  return color;
}

/* Postprocess the output of the blur filter by taking its square root it in its alpha straight
 * form, assuming the given color is alpha premultiplied. This essential undoes the processing done
 * by the gamma_correct_blur_input function. */
vec4 gamma_uncorrect_blur_output(vec4 color)
{
  /* Unpremultiply alpha. */
  color.rgb /= color.a > 0.0 ? color.a : 1.0;

  /* Take the square root of the color channel if it is positive, otherwise zero it. */
  color.rgb = mix(sqrt(color.rgb), vec3(0.0), lessThan(color.rgb, vec3(0.0)));

  /* Premultiply alpha to undo previous alpha unpremultiplication. */
  color.rgb *= color.a > 0.0 ? color.a : 1.0;

  return color;
}
