/**
 * blenlib/BKE_sca.h (mar-2001 nzc)
 *	
 * $Id$ 
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */
#ifndef BKE_SCA_H
#define BKE_SCA_H

struct Text;
struct bSensor;
struct Object;
struct bController;
struct bActuator;

void unlink_controller(struct bController *cont);
void unlink_controllers(struct ListBase *lb);
void free_controller(struct bController *cont);
void free_controllers(struct ListBase *lb);

void unlink_actuator(struct bActuator *act);
void unlink_actuators(struct ListBase *lb);
void free_actuator(struct bActuator *act);
void free_actuators(struct ListBase *lb);

void free_text_controllers(struct Text *txt);
void free_sensor(struct bSensor *sens);
void free_sensors(struct ListBase *lb);
struct bSensor *copy_sensor(struct bSensor *sens);
void copy_sensors(struct ListBase *lbn, struct ListBase *lbo);
void init_sensor(struct bSensor *sens);
struct bSensor *new_sensor(int type);
struct bController *copy_controller(struct bController *cont);
void copy_controllers(struct ListBase *lbn, struct ListBase *lbo);
void init_controller(struct bController *cont);
struct bController *new_controller(int type);
struct bActuator *copy_actuator(struct bActuator *act);
void copy_actuators(struct ListBase *lbn, struct ListBase *lbo);
void init_actuator(struct bActuator *act);
struct bActuator *new_actuator(int type);
void clear_sca_new_poins_ob(struct Object *ob);
void clear_sca_new_poins(void);
void set_sca_new_poins_ob(struct Object *ob);
void set_sca_new_poins(void);
void sca_remove_ob_poin(struct Object *obt, struct Object *ob);                    

#endif

