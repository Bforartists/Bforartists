/*
 * Copyright 2011, Blender Foundation.
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * Contributor:
 *		Jeroen Bakker
 *		Monique Dewanchand
 */

#include "COM_ScaleNode.h"

#include "COM_ScaleOperation.h"
#include "COM_ExecutionSystem.h"
#include "BKE_node.h"
#include "COM_SetValueOperation.h"

ScaleNode::ScaleNode(bNode *editorNode) : Node(editorNode)
{
	/* pass */
}

void ScaleNode::convertToOperations(ExecutionSystem *graph, CompositorContext *context)
{
	InputSocket *inputSocket = this->getInputSocket(0);
	InputSocket *inputXSocket = this->getInputSocket(1);
	InputSocket *inputYSocket = this->getInputSocket(2);
	OutputSocket *outputSocket = this->getOutputSocket(0);
	bNode *bnode = this->getbNode();
	switch (bnode->custom1) {
		case CMP_SCALE_RELATIVE: {
			ScaleOperation *operation = new ScaleOperation();

			inputSocket->relinkConnections(operation->getInputSocket(0), 0, graph);
			inputXSocket->relinkConnections(operation->getInputSocket(1), 1, graph);
			inputYSocket->relinkConnections(operation->getInputSocket(2), 2, graph);
			outputSocket->relinkConnections(operation->getOutputSocket(0));
			graph->addOperation(operation);
		}
		break;
		case CMP_SCALE_SCENEPERCENT: {
			SetValueOperation *scaleFactorOperation = new SetValueOperation();
			scaleFactorOperation->setValue(context->getRenderData()->size / 100.0f);
			ScaleOperation *operation = new ScaleOperation();
			inputSocket->relinkConnections(operation->getInputSocket(0), 0, graph);
			addLink(graph, scaleFactorOperation->getOutputSocket(), operation->getInputSocket(1));
			addLink(graph, scaleFactorOperation->getOutputSocket(), operation->getInputSocket(2));
			outputSocket->relinkConnections(operation->getOutputSocket(0));
			graph->addOperation(scaleFactorOperation);
			graph->addOperation(operation);
		}
		break;

		case CMP_SCALE_RENDERPERCENT: {
			const RenderData *rd = context->getRenderData();
			ScaleFixedSizeOperation *operation = new ScaleFixedSizeOperation();

			/* framing options */
			operation->setIsAspect((bnode->custom2 & CMP_SCALE_RENDERSIZE_FRAME_ASPECT) != 0);
			operation->setIsCrop((bnode->custom2 & CMP_SCALE_RENDERSIZE_FRAME_CROP) != 0);
			operation->setOffset(bnode->custom3, bnode->custom4);

			operation->setNewWidth(rd->xsch * rd->size / 100.0f);
			operation->setNewHeight(rd->ysch * rd->size / 100.0f);
			inputSocket->relinkConnections(operation->getInputSocket(0), 0, graph);
			outputSocket->relinkConnections(operation->getOutputSocket(0));
			operation->getInputSocket(0)->getConnection()->setIgnoreResizeCheck(true);
			graph->addOperation(operation);
		}
		break;

		case CMP_SCALE_ABSOLUTE: {
			ScaleAbsoluteOperation *operation = new ScaleAbsoluteOperation(); // TODO: what is the use of this one.... perhaps some issues when the ui was updated....

			inputSocket->relinkConnections(operation->getInputSocket(0), 0, graph);
			inputXSocket->relinkConnections(operation->getInputSocket(1), 1, graph);
			inputYSocket->relinkConnections(operation->getInputSocket(2), 2, graph);
			outputSocket->relinkConnections(operation->getOutputSocket(0));
			graph->addOperation(operation);
		}
		break;
	}
}
