/* Testing code for new animation system in 2.5 
 * Copyright 2009, Joshua Leung
 */

#ifndef BKE_ANIM_SYS_H
#define BKE_ANIM_SYS_H

struct ID;
struct ListBase;
struct Main;
struct AnimData;
struct KeyingSet;
struct KS_Path;

struct PointerRNA;
struct bAction;
struct bActionGroup;
struct AnimMapper;

/* ************************************* */
/* AnimData API */

/* Get AnimData from the given ID-block. */
struct AnimData *BKE_animdata_from_id(struct ID *id);

/* Add AnimData to the given ID-block */
struct AnimData *BKE_id_add_animdata(struct ID *id);

/* Free AnimData */
void BKE_free_animdata(struct ID *id);

/* Copy AnimData */
struct AnimData *BKE_copy_animdata(struct AnimData *adt);

/* ************************************* */
/* KeyingSets API */

/* Used to create a new 'custom' KeyingSet for the user, that will be automatically added to the stack */
struct KeyingSet *BKE_keyingset_add(struct ListBase *list, const char name[], short flag, short keyingflag);

/* Add a destination to a KeyingSet */
void BKE_keyingset_add_destination(struct KeyingSet *ks, struct ID *id, const char group_name[], const char rna_path[], int array_index, short flag, short groupmode);

struct KS_Path *BKE_keyingset_find_destination(struct KeyingSet *ks, struct ID *id, const char group_name[], const char rna_path[], int array_index, int group_mode);

/* Free data for KeyingSet but not set itself */
void BKE_keyingset_free(struct KeyingSet *ks);

/* Free all the KeyingSets in the given list */
void BKE_keyingsets_free(struct ListBase *list);

/* ************************************* */
// TODO: overrides, remapping, and path-finding api's

/* ************************************* */
/* Evaluation API */

/* ------------- Main API -------------------- */
/* In general, these ones should be called to do all animation evaluation */

/* Evaluation loop for evaluating animation data  */
void BKE_animsys_evaluate_animdata(struct ID *id, struct AnimData *adt, float ctime, short recalc);

/* Evaluation of all ID-blocks with Animation Data blocks - Animation Data Only */
void BKE_animsys_evaluate_all_animation(struct Main *main, float ctime);


/* ------------ Specialised API --------------- */
/* There are a few special tools which require these following functions. They are NOT to be used
 * for standard animation evaluation UNDER ANY CIRCUMSTANCES! 
 *
 * i.e. Pose Library (PoseLib) uses some of these for selectively applying poses, but 
 *	    Particles/Sequencer performing funky time manipulation is not ok.
 */

/* Evaluate Action (F-Curve Bag) */
void animsys_evaluate_action(struct PointerRNA *ptr, struct bAction *act, struct AnimMapper *remap, float ctime);

/* Evaluate Action Group */
void animsys_evaluate_action_group(struct PointerRNA *ptr, struct bAction *act, struct bActionGroup *agrp, struct AnimMapper *remap, float ctime);

/* ************************************* */

#endif /* BKE_ANIM_SYS_H*/
