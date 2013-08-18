/*
 * Adapted from Open Shading Language with this license:
 *
 * Copyright (c) 2009-2010 Sony Pictures Imageworks Inc., et al.
 * All Rights Reserved.
 *
 * Modifications Copyright 2011, Blender Foundation.
 * 
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met:
 * * Redistributions of source code must retain the above copyright
 *   notice, this list of conditions and the following disclaimer.
 * * Redistributions in binary form must reproduce the above copyright
 *   notice, this list of conditions and the following disclaimer in the
 *   documentation and/or other materials provided with the distribution.
 * * Neither the name of Sony Pictures Imageworks nor the names of its
 *   contributors may be used to endorse or promote products derived from
 *   this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#include <OpenImageIO/fmath.h>

#include <OSL/genclosure.h>

#include "osl_bssrdf.h"
#include "osl_closures.h"

#include "kernel_types.h"
#include "kernel_montecarlo.h"

#include "closure/bsdf_diffuse.h"
#include "closure/bssrdf.h"

CCL_NAMESPACE_BEGIN

using namespace OSL;

/* Cubic */

class CubicBSSRDFClosure : public CBSSRDFClosure {
public:
	size_t memsize() const { return sizeof(*this); }
	const char *name() const { return "bssrdf_cubic"; }

	void setup()
	{
		sc.type = CLOSURE_BSSRDF_COMPATIBLE_ID;
		sc.prim = NULL;
		sc.data0 = fabsf(average(radius));
		sc.data1 = 0.0f; // XXX texture blur
	}

	bool mergeable(const ClosurePrimitive *other) const
	{
		return false;
	}

	void print_on(std::ostream &out) const
	{
		out << name() << " ((" << sc.N[0] << ", " << sc.N[1] << ", " << sc.N[2] << "))";
	}
};

ClosureParam *closure_bssrdf_cubic_params()
{
	static ClosureParam params[] = {
		CLOSURE_FLOAT3_PARAM(CubicBSSRDFClosure, sc.N),
		CLOSURE_FLOAT3_PARAM(CubicBSSRDFClosure, radius),
		//CLOSURE_FLOAT_PARAM(CubicBSSRDFClosure, sc.data1),
	    CLOSURE_STRING_KEYPARAM("label"),
	    CLOSURE_FINISH_PARAM(CubicBSSRDFClosure)
	};
	return params;
}

CLOSURE_PREPARE(closure_bssrdf_cubic_prepare, CubicBSSRDFClosure)

/* Gaussian */

class GaussianBSSRDFClosure : public CBSSRDFClosure {
public:
	size_t memsize() const { return sizeof(*this); }
	const char *name() const { return "bssrdf_gaussian"; }

	void setup()
	{
		sc.type = CLOSURE_BSSRDF_GAUSSIAN_ID;
		sc.prim = NULL;
		sc.data0 = fabsf(average(radius));
		sc.data1 = 0.0f; // XXX texture blurring!
	}

	bool mergeable(const ClosurePrimitive *other) const
	{
		return false;
	}

	void print_on(std::ostream &out) const
	{
		out << name() << " ((" << sc.N[0] << ", " << sc.N[1] << ", " << sc.N[2] << "))";
	}
};

ClosureParam *closure_bssrdf_gaussian_params()
{
	static ClosureParam params[] = {
		CLOSURE_FLOAT3_PARAM(GaussianBSSRDFClosure, sc.N),
		CLOSURE_FLOAT3_PARAM(GaussianBSSRDFClosure, radius),
		//CLOSURE_FLOAT_PARAM(GaussianBSSRDFClosure, sc.data1),
	    CLOSURE_STRING_KEYPARAM("label"),
	    CLOSURE_FINISH_PARAM(GaussianBSSRDFClosure)
	};
	return params;
}

CLOSURE_PREPARE(closure_bssrdf_gaussian_prepare, GaussianBSSRDFClosure)

CCL_NAMESPACE_END

