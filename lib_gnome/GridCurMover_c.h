/*
 *  GridCurMover_c.h
 *  gnome
 *
 *  Created by Generic Programmer on 12/1/11.
 *  Copyright 2011 __MyCompanyName__. All rights reserved.
 *
 */

#ifndef __GridCurMover_c__
#define __GridCurMover_c__

#include "Basics.h"
#include "TypeDefs.h"
#include "GridCurMover_b.h"
#include "CATSMover_c.h"

class GridCurMover_c : virtual public GridCurMover_b, virtual public CATSMover_c {

public:
	virtual OSErr		AddUncertainty(long setIndex, long leIndex,VelocityRec *patVelocity,double timeStep,Boolean useEddyUncertainty);
	
	long 				GetVelocityIndex(WorldPoint p);
	VelocityRec			GetPatValue (WorldPoint p);
	VelocityRec 		GetScaledPatValue(WorldPoint p,Boolean * useEddyUncertainty);//JLM 5/12/99
	
	virtual OSErr		GetStartTime(Seconds *startTime);
	virtual OSErr		GetEndTime(Seconds *endTime);
	virtual double		GetStartUVelocity(long index);
	virtual double		GetStartVVelocity(long index);
	virtual double		GetEndUVelocity(long index);
	virtual double		GetEndVVelocity(long index);
	virtual Boolean 	VelocityStrAtPoint(WorldPoint3D wp, char *diagnosticStr);	
	virtual WorldPoint3D	GetMove (Seconds timeStep,long setIndex,long leIndex,LERec *thisLE,LETYPE leType);
	virtual OSErr 		PrepareForModelStep(const Seconds&, const Seconds&, const Seconds&, bool); // AH 04/16/12
	virtual void 		ModelStepIsDone();
	
};

#endif
