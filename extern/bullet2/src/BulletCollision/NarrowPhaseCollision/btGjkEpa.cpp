/*
Bullet Continuous Collision Detection and Physics Library
Copyright (c) 2003-2006 Erwin Coumans  http://continuousphysics.com/Bullet/

This software is provided 'as-is', without any express or implied warranty.
In no event will the authors be held liable for any damages arising from the 
use of this software.
Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it 
freely,
subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not 
claim that you wrote the original software. If you use this software in a 
product, an acknowledgment in the product documentation would be appreciated 
but is not required.
2. Altered source versions must be plainly marked as such, and must not be 
misrepresented as being the original software.
3. This notice may not be removed or altered from any source distribution.
*/

/*
GJK-EPA collision solver by Nathanael Presson
Nov.2006
*/


#include "btGjkEpa.h"
#include <string.h> //for memset

namespace gjkepa_impl
{

//
// Port. typedefs
//

typedef	btScalar		F;
typedef bool			Z;
typedef int				I;
typedef unsigned int	U;
typedef unsigned char	U1;
typedef unsigned short	U2;

typedef btVector3		Vector3;
typedef btMatrix3x3		Rotation;

//
// Config
//

#if 0
#define BTLOCALSUPPORT	localGetSupportingVertexWithoutMargin
#else
#define BTLOCALSUPPORT	localGetSupportingVertex
#endif

//
// Const
//

static const U			chkPrecision		=1/U(sizeof(F)==4);

static const F			cstInf				=F(1/sin(0.));
static const F			cstPi				=F(acos(-1.));
static const F			cst2Pi				=cstPi*2;

static const U			GJK_maxiterations	=128;
static const U			GJK_hashsize		=1<<6;
static const U			GJK_hashmask		=GJK_hashsize-1;
static const F			GJK_insimplex_eps	=F(0.0001);
static const F			GJK_sqinsimplex_eps	=GJK_insimplex_eps*GJK_insimplex_eps;

static const U			EPA_maxiterations	=256;
static const F			EPA_inface_eps		=F(0.01);
static const F			EPA_accuracy		=F(0.001);

//
// Utils
//

static inline F								Abs(F v)					{ return(v<0?-v:v); }
static inline F								Sign(F v)					{ return(F(v<0?-1:1)); }
template <typename T> static inline void	Swap(T& a,T& b)				{ T 
t(a);a=b;b=t; }
template <typename T> static inline T		Min(const T& a,const T& b)	{ 
return(a<b?a:b); }
template <typename T> static inline T		Max(const T& a,const T& b)	{ 
return(a>b?a:b); }
static inline void							ClearMemory(void* p,U sz)	{ memset(p,0,(size_t)sz); 
}
#if 0
template <typename T> static inline void	Raise(const T& object)		{ 
throw(object); }
#else
template <typename T> static inline void	Raise(const T&)				{}
#endif
static inline F								Det(const Vector3& a,const Vector3& b,const Vector3& 
c,const Vector3& d)
		{
		return(	-(a.z()*b.y()*c.x()) + a.y()*b.z()*c.x() + a.z()*b.x()*c.y() - 
a.x()*b.z()*c.y() - a.y()*b.x()*c.z() + a.x()*b.y()*c.z() +
				a.z()*b.y()*d.x() - a.y()*b.z()*d.x() - a.z()*c.y()*d.x() + 
b.z()*c.y()*d.x() + a.y()*c.z()*d.x() - b.y()*c.z()*d.x() -
				a.z()*b.x()*d.y() + a.x()*b.z()*d.y() + a.z()*c.x()*d.y() - 
b.z()*c.x()*d.y() - a.x()*c.z()*d.y() + b.x()*c.z()*d.y() +
				a.y()*b.x()*d.z() - a.x()*b.y()*d.z() - a.y()*c.x()*d.z() + 
b.y()*c.x()*d.z() + a.x()*c.y()*d.z() - b.x()*c.y()*d.z());
		}

//
// StackAlloc
//
struct StackAlloc
	{
	struct Block
		{
		Block*	previous;
		U1*		address;
		};
				StackAlloc()		{ ctor(); }
				StackAlloc(U size)	{ ctor();Create(size); }
				~StackAlloc()		{ Free(); }
	void		Create(U size)
		{
		Free();
		data		=	new U1[size];
		totalsize	=	size;
		}
	StackAlloc*	CreateChild(U size)
		{
		StackAlloc*	sa(Allocate<StackAlloc>());
		sa->ischild		=	true;
		sa->data		=	Allocate(size);
		sa->totalsize	=	size;
		sa->usedsize	=	0;
		sa->current		=	0;
		return(sa);
		}
	void		Free()
		{
		if(usedsize==0)
			{
			if(!ischild)		delete[] data;
			data				=	0;
			usedsize			=	0;
			} else Raise(L"StackAlloc is still in use");
		}
	Block*		BeginBlock()
		{
		Block*	pb(Allocate<Block>());
		pb->previous	=	current;
		pb->address		=	data+usedsize;
		current			=	pb;
		return(pb);
		}
	void		EndBlock(Block* block)
		{
		if(block==current)
			{
			current		=	block->previous;
			usedsize	=	(U)((block->address-data)-sizeof(Block));
			} else Raise(L"Unmatched blocks");
		}
	U1*			Allocate(U size)
		{
		const U	nus(usedsize+size);
		if(nus<totalsize)
			{
			usedsize=nus;
			return(data+(usedsize-size));
			}
		Raise(L"Not enough memory");
		return(0);
		}
	template <typename T> T*	Allocate()				{
return((T*)Allocate((U)sizeof(T))); }
	template <typename T> T*	AllocateArray(U count)	{
return((T*)Allocate((U)sizeof(T)*count)); }
	private:
	void		ctor()
		{
		data		=	0;
		totalsize	=	0;
		usedsize	=	0;
		current		=	0;
		ischild		=	false;
		}
	U1*		data;
	U		totalsize;
	U		usedsize;
	Block*	current;
	Z		ischild;
	};

//
// GJK
//
struct	GJK
	{
	struct Mkv
		{
		Vector3	w;		/* Minkowski vertice	*/
		Vector3	r;		/* Ray					*/
		};
	struct He
		{
		Vector3	v;
		He*		n;
		};
	static const U			hashsize=64;
	StackAlloc*				sa;
	StackAlloc::Block*		sablock;
	He*						table[hashsize];
	Rotation				wrotations[2];
	Vector3					positions[2];
	const btConvexShape*	shapes[2];
	Mkv						simplex[5];
	Vector3					ray;
	U						order;
	U						iterations;
	F						margin;
	Z						failed;
	//
					GJK(StackAlloc* psa,
						const Rotation& wrot0,const Vector3& pos0,const btConvexShape* shape0,
						const Rotation& wrot1,const Vector3& pos1,const btConvexShape* shape1,
						F pmargin=0)
		{
		wrotations[0]=wrot0;positions[0]=pos0;shapes[0]=shape0;
		wrotations[1]=wrot1;positions[1]=pos1;shapes[1]=shape1;
		sa		=psa;
		sablock	=sa->BeginBlock();
		margin	=pmargin;
		failed	=false;
		}
	//
					~GJK()
		{
		sa->EndBlock(sablock);
		}
	// vdh : very dumm hash
	static inline U	Hash(const Vector3& v)
		{
                const U h((U)(v[0]*15461)^(U)(v[1]*83003)^(U)(v[2]*15473));
		return(((*((const U*)&h))*169639)&GJK_hashmask);
		}
	//
	inline Vector3	LocalSupport(const Vector3& d,U i) const
		{
		return(wrotations[i]*shapes[i]->BTLOCALSUPPORT(d*wrotations[i])+positions[i]);
		}
	//
	inline void		Support(const Vector3& d,Mkv& v) const
		{
		v.r	=	d;
		v.w	=	LocalSupport(d,0)-LocalSupport(-d,1)+d*margin;
		}
	#define SPX(_i_)	simplex[_i_]
	#define SPXW(_i_)	simplex[_i_].w
	//
	inline Z		FetchSupport()
		{
		const U			h(Hash(ray));
		He*				e(table[h]);
		while(e) { if(e->v==ray) { --order;return(false); } else e=e->n; }
		e=sa->Allocate<He>();e->v=ray;e->n=table[h];table[h]=e;
		Support(ray,simplex[++order]);
		return(ray.dot(SPXW(order))>0);
		}
	//
	inline Z		SolveSimplex2(const Vector3& ao,const Vector3& ab)
		{
		if(ab.dot(ao)>=0)
			{
			const Vector3	cabo(cross(ab,ao));
			if(cabo.length2()>GJK_sqinsimplex_eps)
				{ ray=cross(cabo,ab); }
				else
				{ return(true); }
			}
			else
			{ order=0;SPX(0)=SPX(1);ray=ao;	}
		return(false);
		}
	//
	inline Z		SolveSimplex3(const Vector3& ao,const Vector3& ab,const Vector3& 
ac)
		{
		return(SolveSimplex3a(ao,ab,ac,cross(ab,ac)));
		}
	//
	inline Z		SolveSimplex3a(const Vector3& ao,const Vector3& ab,const Vector3& 
ac,const Vector3& cabc)
		{
				if((cross(cabc,ab)).dot(ao)<-GJK_insimplex_eps)
			{ order=1;SPX(0)=SPX(1);SPX(1)=SPX(2);return(SolveSimplex2(ao,ab));	}
		else	if((cross(cabc,ac)).dot(ao)>+GJK_insimplex_eps)
			{ order=1;SPX(1)=SPX(2);return(SolveSimplex2(ao,ac)); }
		else
			{
			const F			d(cabc.dot(ao));
			if(Abs(d)>GJK_insimplex_eps)
				{
				if(d>0)
					{ ray=cabc; }
					else
					{ ray=-cabc;Swap(SPX(0),SPX(1)); }
				return(false);
				} else return(true);
			}
		}
	//
	inline Z		SolveSimplex4(const Vector3& ao,const Vector3& ab,const Vector3& 
ac,const Vector3& ad)
		{
		Vector3			crs;
				if((crs=cross(ab,ac)).dot(ao)>GJK_insimplex_eps)
			{ 
order=2;SPX(0)=SPX(1);SPX(1)=SPX(2);SPX(2)=SPX(3);return(SolveSimplex3a(ao,ab,ac,crs)); 
}
		else	if((crs=cross(ac,ad)).dot(ao)>GJK_insimplex_eps)
			{ order=2;SPX(2)=SPX(3);return(SolveSimplex3a(ao,ac,ad,crs)); }
		else	if((crs=cross(ad,ab)).dot(ao)>GJK_insimplex_eps)
			{ 
order=2;SPX(1)=SPX(0);SPX(0)=SPX(2);SPX(2)=SPX(3);return(SolveSimplex3a(ao,ad,ab,crs)); 
}
		else	return(true);
		}
	//
	inline Z		SearchOrigin(const Vector3& initray=Vector3(1,0,0))
		{
		iterations	=	0;
		order		=	0;
		failed		=	false;
		Support(initray,simplex[0]);ray=-SPXW(0);
		ClearMemory(table,sizeof(void*)*hashsize);
		for(;iterations<GJK_maxiterations;++iterations)
			{
			const F		rl(ray.length());
			ray/=rl>0?rl:1;
			if(FetchSupport())
				{
				Z	found(false);
				switch(order)
					{
					case	1:	found=SolveSimplex2(-SPXW(1),SPXW(0)-SPXW(1));break;
					case	2:	found=SolveSimplex3(-SPXW(2),SPXW(1)-SPXW(2),SPXW(0)-SPXW(2));break;
					case	3:	found=SolveSimplex4(-SPXW(3),SPXW(2)-SPXW(3),SPXW(1)-SPXW(3),SPXW(0)-SPXW(3));break;
					}
				if(found) return(true);
				} else return(false);
			}
		failed=true;
		return(false);
		}
	//
	inline Z		EncloseOrigin()
		{
		switch(order)
			{
			/* Point		*/
			case	0:	break;
			/* Line			*/
			case	1:
				{
				const Vector3	ab(SPXW(1)-SPXW(0));
				const Vector3	b[]={	cross(ab,Vector3(1,0,0)),
										cross(ab,Vector3(0,1,0)),
										cross(ab,Vector3(0,0,1))};
				const F			m[]={b[0].length2(),b[1].length2(),b[2].length2()};
				const Rotation	r(btQuaternion(ab.normalized(),cst2Pi/3));
				Vector3			w(b[m[0]>m[1]?m[0]>m[2]?0:2:m[1]>m[2]?1:2]);
				Support(w.normalized(),simplex[4]);w=r*w;
				Support(w.normalized(),simplex[2]);w=r*w;
				Support(w.normalized(),simplex[3]);w=r*w;
				order=4;
				return(true);
				}
			break;
			/* Triangle		*/
			case	2:
				{
				const 
Vector3	n(cross((SPXW(1)-SPXW(0)),(SPXW(2)-SPXW(0))).normalized());
				Support( n,simplex[3]);
				Support(-n,simplex[4]);
				order=4;
				return(true);
				}
			break;
			/* Tetrahedron	*/
			case	3:	return(true);
			/* Hexahedron	*/
			case	4:	return(true);
			}
		return(false);
		}
	#undef SPX
	#undef SPXW
	};

//
// EPA
//
struct	EPA
	{
	//
	struct Face
		{
		const GJK::Mkv*	v[3];
		Face*			f[3];
		U				e[3];
		Vector3			n;
		F				d;
		U				mark;
		Face*			prev;
		Face*			next;
		Face()			{}
		};
	//
	GJK*			gjk;
	StackAlloc*		sa;
	Face*			root;
	U				nfaces;
	U				iterations;
	Vector3			features[2][3];
	Vector3			nearest[2];
	Vector3			normal;
	F				depth;
	Z				failed;
	//
					EPA(GJK* pgjk)
		{
		gjk		=	pgjk;
		sa		=	pgjk->sa;
		}
	//
					~EPA()
		{
		}
	//
	inline Vector3	GetCoordinates(const Face* face) const
		{
		const Vector3	o(face->n*-face->d);
		const F			a[]={	cross(face->v[0]->w-o,face->v[1]->w-o).length(),
								cross(face->v[1]->w-o,face->v[2]->w-o).length(),
								cross(face->v[2]->w-o,face->v[0]->w-o).length()};
		const F			sm(a[0]+a[1]+a[2]);
		return(Vector3(a[1],a[2],a[0])/(sm>0?sm:1));
		}
	//
	inline Face*	FindBest() const
		{
		Face*	bf(0);
		if(root)
			{
			Face*	cf(root);
			F		bd(cstInf);
			do	{
				if(cf->d<bd) { bd=cf->d;bf=cf; }
				} while(0!=(cf=cf->next));
			}
		return(bf);
		}
	//
	inline Z		Set(Face* f,const GJK::Mkv* a,const GJK::Mkv* b,const GJK::Mkv* 
c) const
		{
		const Vector3	nrm(cross(b->w-a->w,c->w-a->w));
		const F			len(nrm.length());
		const Z			valid(	(cross(a->w,b->w).dot(nrm)>=-EPA_inface_eps)&&
								(cross(b->w,c->w).dot(nrm)>=-EPA_inface_eps)&&
								(cross(c->w,a->w).dot(nrm)>=-EPA_inface_eps));
		f->v[0]	=	a;
		f->v[1]	=	b;
		f->v[2]	=	c;
		f->mark	=	0;
		f->n	=	nrm/(len>0?len:cstInf);
		f->d	=	Max<F>(0,-f->n.dot(a->w));
		return(valid);
		}
	//
	inline Face*	NewFace(const GJK::Mkv* a,const GJK::Mkv* b,const GJK::Mkv* c)
		{
		Face*	pf(sa->Allocate<Face>());
		if(Set(pf,a,b,c))
			{
			if(root) root->prev=pf;
			pf->prev=0;
			pf->next=root;
			root	=pf;
			++nfaces;
			}
			else
			{
			pf->prev=pf->next=0;
			}
		return(pf);
		}
	//
	inline void		Detach(Face* face)
		{
		if(face->prev||face->next)
			{
			--nfaces;
			if(face==root)
				{ root=face->next;root->prev=0; }
				else
				{
				if(face->next==0)
					{ face->prev->next=0; }
					else
					{ face->prev->next=face->next;face->next->prev=face->prev; }
				}
			face->prev=face->next=0;
			}
		}
	//
	inline void		Link(Face* f0,U e0,Face* f1,U e1) const
		{
		f0->f[e0]=f1;f1->e[e1]=e0;
		f1->f[e1]=f0;f0->e[e0]=e1;
		}
	//
	GJK::Mkv*		Support(const Vector3& w) const
		{
		GJK::Mkv*		v(sa->Allocate<GJK::Mkv>());
		gjk->Support(w,*v);
		return(v);
		}
	//
	U				BuildHorizon(U markid,const GJK::Mkv* w,Face& f,U e,Face*& cf,Face*& 
ff)
		{
		static const U	mod3[]={0,1,2,0,1};
		U				ne(0);
		if(f.mark!=markid)
			{
			const U	e1(mod3[e+1]);
			if((f.n.dot(w->w)+f.d)>0)
				{
				Face*	nf(NewFace(f.v[e1],f.v[e],w));
				Link(nf,0,&f,e);
				if(cf) Link(cf,1,nf,2); else ff=nf;
				cf=nf;ne=1;
				}
				else
				{
				const U	e2(mod3[e+2]);
				Detach(&f);
				f.mark	=	markid;
				ne		+=	BuildHorizon(markid,w,*f.f[e1],f.e[e1],cf,ff);
				ne		+=	BuildHorizon(markid,w,*f.f[e2],f.e[e2],cf,ff);
				}
			}
		return(ne);
		}
	//
	inline F		EvaluatePD(F accuracy=EPA_accuracy)
		{
		StackAlloc::Block*	sablock(sa->BeginBlock());
		Face*				bestface(0);
		U					markid(1);
		depth		=	-cstInf;
		normal		=	Vector3(0,0,0);
		root		=	0;
		nfaces		=	0;
		iterations	=	0;
		failed		=	false;
		/* Prepare hull		*/
		if(gjk->EncloseOrigin())
			{
			const U*		pfidx(0);
			U				nfidx(0);
			const U*		peidx(0);
			U				neidx(0);
			GJK::Mkv*		basemkv[5];
			Face*			basefaces[6];
			switch(gjk->order)
				{
				/* Tetrahedron		*/
				case	3:	{
							static const U	fidx[4][3]={{2,1,0},{3,0,1},{3,1,2},{3,2,0}};
							static const 
U	eidx[6][4]={{0,0,2,1},{0,1,1,1},{0,2,3,1},{1,0,3,2},{2,0,1,2},{3,0,2,2}};
							pfidx=(const U*)fidx;nfidx=4;peidx=(const U*)eidx;neidx=6;
							}	break;
				/* Hexahedron		*/
				case	4:	{
							static const 
U	fidx[6][3]={{2,0,4},{4,1,2},{1,4,0},{0,3,1},{0,2,3},{1,3,2}};
							static const 
U	eidx[9][4]={{0,0,4,0},{0,1,2,1},{0,2,1,2},{1,1,5,2},{1,0,2,0},{2,2,3,2},{3,1,5,0},{3,0,4,2},{5,1,4,1}};
							pfidx=(const U*)fidx;nfidx=6;peidx=(const U*)eidx;neidx=9;
							}	break;
				}
			for(U i=0;i<=gjk->order;++i)		{ 
basemkv[i]=sa->Allocate<GJK::Mkv>();*basemkv[i]=gjk->simplex[i]; }
			for(U i=0;i<nfidx;++i,pfidx+=3)		{ 
basefaces[i]=NewFace(basemkv[pfidx[0]],basemkv[pfidx[1]],basemkv[pfidx[2]]); 
}
			for(U i=0;i<neidx;++i,peidx+=4)		{ 
Link(basefaces[peidx[0]],peidx[1],basefaces[peidx[2]],peidx[3]); }
			}
		if(0==nfaces)
			{
			sa->EndBlock(sablock);
			return(depth);
			}
		/* Expand hull		*/
		for(;iterations<EPA_maxiterations;++iterations)
			{
			Face*		bf(FindBest());
			if(bf)
				{
				GJK::Mkv*	w(Support(-bf->n));
				const F		d(bf->n.dot(w->w)+bf->d);
				bestface	=	bf;
				if(d<-accuracy)
					{
					Face*	cf(0);
					Face*	ff(0);
					U		nf(0);
					Detach(bf);
					bf->mark=++markid;
					for(U i=0;i<3;++i)	{ 
nf+=BuildHorizon(markid,w,*bf->f[i],bf->e[i],cf,ff); }
					if(nf<=2)			{ break; }
					Link(cf,1,ff,2);
					} else break;
				} else break;
			}
		/* Extract contact	*/
		if(bestface)
			{
			const Vector3	b(GetCoordinates(bestface));
			normal			=	bestface->n;
			depth			=	Max<F>(0,bestface->d);
			for(U i=0;i<2;++i)
				{
				const F	s(F(i?-1:1));
				for(U j=0;j<3;++j)
					{
					features[i][j]=gjk->LocalSupport(s*bestface->v[j]->r,i);
					}
				}
			nearest[0]		=	features[0][0]*b.x()+features[0][1]*b.y()+features[0][2]*b.z();
			nearest[1]		=	features[1][0]*b.x()+features[1][1]*b.y()+features[1][2]*b.z();
			} else failed=true;
		sa->EndBlock(sablock);
		return(depth);
		}
	};
}

//
// Api
//

using namespace	gjkepa_impl;

/* Need some kind of stackalloc , create a static one till bullet provide
one.	*/
static const U		g_sasize((1024<<10)*2);
static StackAlloc	g_sa(g_sasize);

//
bool	btGjkEpaSolver::Collide(btConvexShape *shape0,const btTransform &wtrs0,
								btConvexShape *shape1,const btTransform &wtrs1,
								btScalar	radialmargin,
								sResults&	results)
{
/* Initialize					*/
results.witnesses[0]	=
results.witnesses[1]	=
results.normal			=	Vector3(0,0,0);
results.depth			=	0;
results.status			=	sResults::Separated;
results.epa_iterations	=	0;
results.gjk_iterations	=	0;
/* Use GJK to locate origin		*/
GJK			gjk(&g_sa,
				wtrs0.getBasis(),wtrs0.getOrigin(),shape0,
				wtrs1.getBasis(),wtrs1.getOrigin(),shape1,
				radialmargin+EPA_accuracy);
const Z		collide(gjk.SearchOrigin());
results.gjk_iterations	=	gjk.iterations+1;
if(collide)
	{
	/* Then EPA for penetration depth	*/
	EPA			epa(&gjk);
	const F		pd(epa.EvaluatePD());
	results.epa_iterations	=	epa.iterations+1;
	if(pd>0)
		{
		results.status			=	sResults::Penetrating;
		results.normal			=	epa.normal;
		results.depth			=	pd;
		results.witnesses[0]	=	epa.nearest[0];
		results.witnesses[1]	=	epa.nearest[1];
		return(true);
		} else { if(epa.failed) results.status=sResults::EPA_Failed; }
	} else { if(gjk.failed) results.status=sResults::GJK_Failed; }
return(false);
}



