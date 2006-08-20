/*
** A simple Verse server.
*/

#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <string.h>

#include "v_cmd_gen.h"

#if !defined V_GENERATE_FUNC_MODE

#include "verse.h"
#include "v_network.h"
#include "v_util.h"
#include "vs_server.h"

#define	MASTER_SERVER_PERIOD	(1.0  * 60.0)

extern VNodeID	vs_node_create(VNodeID owner_id, unsigned int type);
extern void	callback_send_node_destroy(void *user_data, VNodeID node_id);
extern void	vs_reset_owner(VNodeID owner_id);

static void callback_send_ping(void *user, const char *address, const char *message)
{
	printf("Bouncing ping '%s' back to '%s'\n", message, address);
	verse_send_ping(address, message);
}

static void callback_send_connect(void *user, const char *name, const char *pass, const char *address, const uint8 *host_id)
{
	VNodeID avatar;
	VSession *session;

	printf("Connecting '%s'\n", name);
	if(TRUE)
	{
		avatar = vs_node_create(~0, V_NT_OBJECT);
		session = verse_send_connect_accept(avatar, address, NULL);
		vs_add_new_connection(session, name, pass, avatar);
/*		vs_avatar_init(avatar, name);*/
	}
	else
	{
		verse_send_connect_terminate(address, "I'm sorry but you are not welcome here.");
	}
}

static void callback_send_connect_terminate(void *user, char *address, char *bye)
{
	printf("callback_send_connect_terminate\n");
	vs_reset_owner(vs_get_avatar());
	callback_send_node_destroy(NULL, vs_get_avatar());
	verse_session_destroy(vs_get_session());
	vs_remove_connection();
}

static void vs_load_host_id(const char *file_name)
{
	FILE	*f;
	uint8	id[V_HOST_ID_SIZE];
	size_t	got;

	/* Attempt to read key from given filename. Fails silently. */
	if((f = fopen(file_name, "rb")) != NULL)
	{
		if((got = fread(id, 1, sizeof id, f)) > 0)
		{
			printf("Loaded %u-bit host ID key successfully\n", 8 * (got / 3));
			verse_host_id_set(id);
		}
		fclose(f);
		if(got)
			return;
	}
	/* If file didn't open, or reading failed, generate a new key and write it out. */
	verse_host_id_create(id);
	verse_host_id_set(id);
	if((f = fopen(file_name, "wb")) != NULL)
	{
		if(fwrite(id, sizeof id, 1, f) != 1)
			fprintf(stderr, "Warning: Couldn't write host ID to \"%s\"\n", file_name);
		fclose(f);
	}
	else
		fprintf(stderr, "Warning: Couldn't open \"%s\" for host ID writing\n", file_name);
}

static void cb_sigint_handler(int sig)
{
	if(sig == SIGINT)
	{
		printf("Verse server terminating\n");
		exit(EXIT_SUCCESS);
	}
}

static void master_server_update(VUtilTimer *timer, const char *master_server)
{
	if(master_server == NULL || v_timer_elapsed(timer) < MASTER_SERVER_PERIOD)
		return;
	verse_send_ping(master_server, "MS:ANNOUNCE");
	v_timer_start(timer);
	printf("MS:ANNOUNCE sent to %s\n", master_server);
}

int main(int argc, char **argv)
{
	const char	*ms_address = NULL;
	VUtilTimer	ms_timer;
	uint32		i, seconds, fractions, port = VERSE_STD_CONNECT_PORT;

	signal(SIGINT, cb_sigint_handler);

	for(i = 1; i < argc; i++)
	{
		if(strcmp(argv[i], "-Q") == 0)
			ms_address = NULL;
		else if(strncmp(argv[i], "-master=", 9) == 0)
			ms_address = argv[i] + 9;
		else if(strncmp(argv[i], "-port=", 6) == 0)
			port = strtoul(argv[i] + 6, NULL, 0);
		else
			fprintf(stderr, "Ignoring unknown argument \"%s\"\n", argv[i]);
	}

	printf("Verse Server r%up%u%s by Eskil Steenberg <http://www.blender.org/modules/verse/>\n", V_RELEASE_NUMBER, V_RELEASE_PATCH, V_RELEASE_LABEL);
	verse_set_port(port);	/* The Verse standard port. */
	printf(" Listening on port %d\n", port);

	/* Seed the random number generator. Still rather too weak for crypto, I guess. */
	v_n_get_current_time(&seconds, &fractions);
	srand(seconds ^ fractions);

	vs_load_host_id("host_id.rsa");
	vs_init_node_storage();
	vs_o_callback_init();
	vs_g_callback_init();
	vs_m_callback_init();
	vs_b_callback_init();
	vs_t_callback_init();
	vs_c_callback_init();
	vs_a_callback_init();
	vs_h_callback_init();
	init_callback_node_storage();
	verse_callback_set(verse_send_ping,		callback_send_ping, NULL);
	verse_callback_set(verse_send_connect,		callback_send_connect,		NULL);
	verse_callback_set(verse_send_connect_terminate, callback_send_connect_terminate, NULL);

	v_timer_start(&ms_timer);
	v_timer_advance(&ms_timer, MASTER_SERVER_PERIOD - 1.0);
	while(TRUE)
	{
		vs_set_next_session();
		verse_callback_update(1000000);
		master_server_update(&ms_timer, ms_address);
	}
	return EXIT_SUCCESS;
}

#endif		/* V_GENERATE_FUNC_MODE */
