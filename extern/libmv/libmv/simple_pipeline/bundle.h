// Copyright (c) 2011 libmv authors.
// 
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to
// deal in the Software without restriction, including without limitation the
// rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
// sell copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
// 
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
// 
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
// FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
// IN THE SOFTWARE.

#ifndef LIBMV_SIMPLE_PIPELINE_BUNDLE_H
#define LIBMV_SIMPLE_PIPELINE_BUNDLE_H

namespace libmv {

class Reconstruction;
class Tracks;

/*!
    Refine camera poses and 3D coordinates using bundle adjustment.

    This routine adjusts all cameras and points in \a *reconstruction. This
    assumes a full observation for reconstructed tracks; this implies that if
    there is a reconstructed 3D point (a bundle) for a track, then all markers
    for that track will be included in the minimization. \a tracks should
    contain markers used in the initial reconstruction.

    The cameras and bundles (3D points) are refined in-place.

    \note This assumes an outlier-free set of markers.
    \note This assumes a calibrated reconstruction, e.g. the markers are
          already corrected for camera intrinsics and radial distortion.

    \sa Resect, Intersect, ReconstructTwoFrames
*/
void Bundle(const Tracks &tracks, Reconstruction *reconstruction);

}  // namespace libmv

#endif   // LIBMV_SIMPLE_PIPELINE_BUNDLE_H
