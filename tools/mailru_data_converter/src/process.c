#include "process.h"


int escape_csv(
	unsigned char *input,
	size_t input_len,
	unsigned char **output)
{
	unsigned char * o = (unsigned char*)malloc(input_len * 2 + 3);

	int out_idx = 0;
	int in_idx = 0;

	o[out_idx++] = '"';
	for(in_idx = 0; in_idx < input_len; in_idx++)
	{
		if(input[in_idx] == '"')
		{
			o[out_idx++] = '"';
			o[out_idx++] = '"';
		}
		else
		{
			o[out_idx++] = input[in_idx];
		}
	}
	o[out_idx++] = '"';
	o[out_idx++] = '\0';
	*output = o;

	return out_idx;
}

void write_csv_line(struct state_j * state)
{
	if (state->qtext == NULL || state->atext == NULL ||  state->qid == NULL)
	{
		return;
	}

	unsigned char * qtext_escaped;
	unsigned char * atext_escaped;
	
	int qtext_escaped_len = escape_csv(
		state->qtext, state->qtext_len, &qtext_escaped);

	int atext_escaped_len = escape_csv(
		state->atext, state->atext_len, &atext_escaped);

	
	// 2 is separators (;)
	size_t cstr_len = 2 + atext_escaped_len + qtext_escaped_len + state->qid_len;
	unsigned char * cstr = malloc(cstr_len);
	
	
	int len = sprintf(cstr, "%s;%s;%s\n", state->qid, qtext_escaped, atext_escaped);
	
	fwrite(cstr , sizeof(unsigned char), len, state->file);

	free(qtext_escaped);
	free(atext_escaped);

	free(state->qtext);
	free(state->atext);
	free(state->qid);
	
	state->qtext = NULL;
	state->atext = NULL;
	state->qid = NULL;

	free(cstr);
}

int j_start_map(void * ctx)
{
	struct state_j *state = (struct state_j*) ctx;
	if (state->is_best == 1)
	{
		if (state->best_started == 0)
		{
			state->best_started = 1;
			state->best_nest = 0;
		}
		else
		{
			state->best_nest++;
		}
	}
	return 1;
}


int j_end_map(void * ctx)
{
	struct state_j *state = (struct state_j*) ctx;
	if (state->best_started == 1)
	{
		if (state->best_nest == 0)
		{
			state->best_started = 0;
			state->is_best = 0;
		}
		else
		{
			state->best_nest--;
		}
	}
	return 1;
}


int j_string(void * ctx, const unsigned char * stringVal,
	size_t stringLen)
{	
	struct state_j *state = (struct state_j*) ctx;
	
	if (state->cur_key == 0)
	{
		state->atext_len = stringLen;
		state->atext = malloc(stringLen+1);
		state->atext[stringLen] = '\0';
		strncpy(state->atext, stringVal, stringLen);
	}
	else if (state->cur_key == 1)
	{
		state->qtext_len = stringLen;
		state->qtext = malloc(stringLen+1);
		state->qtext[stringLen] = '\0';
		strncpy(state->qtext, stringVal, stringLen);
	}
	else if (state->cur_key == 2)
	{
		state->qid_len = stringLen;
		state->qid = malloc(stringLen+1);
		strncpy(state->qid, stringVal, stringLen);
		state->qid[stringLen] = '\0';
		write_csv_line(state);
	}
	return 1;
}

int j_map_key(void * ctx, const unsigned char * stringVal,
	size_t stringLen)
{
	struct state_j * state = (struct state_j*) ctx;

	if (strncmp("best", stringVal, stringLen) == 0)
	{
		state->is_best = 1;
	}
	else if (state->is_best == 1 && strncmp("atext", stringVal, stringLen) == 0)
	{
		state->cur_key = 0;
	}
	else if (strncmp("qtext", stringVal, stringLen) == 0)
	{
		state->cur_key = 1;
	}
	else if (strncmp("qid", stringVal, stringLen) == 0)
	{
		state->cur_key = 2;
	}
	else
	{
		state->cur_key = -1;
	}

	return 1;
}

void process_file(char * path, void * ctx)
{
	yajl_callbacks callbacks =
	{
		NULL,
		NULL,
		NULL,
		NULL,
		NULL,
		j_string,
		j_start_map,
		j_map_key,
		j_end_map,
		NULL,
		NULL,
	};

	yajl_status stat;
	size_t rd;
	size_t bufSize = BUF_SIZE;
	unsigned char * fileData = NULL;

	fileData = (unsigned char *) malloc(bufSize);

	if (fileData == NULL) 
	{
		fprintf(stderr,
				"failed to allocate read buffer of %zu bytes, exiting.",
				bufSize);
		exit(2);
	}

	FILE *file = fopen(path, "r");
	printf("Processing file %s...\n", path);


	yajl_handle hand = yajl_alloc(&callbacks, NULL, ctx);

	for (;;) 
	{
		rd = fread((void *) fileData, 1, bufSize, file);

		if (rd == 0) 
		{
			if (!feof(file)) 
			{
				fprintf(stderr, "error reading file '%s'\n", path);
			}
			break;
		}

		/* read file data, now pass to parser */
		stat = yajl_parse(hand, fileData, rd);
		if (stat != yajl_status_ok) break;
	}

	stat = yajl_complete_parse(hand);
	if (stat != yajl_status_ok)
	{
		unsigned char * str = yajl_get_error(hand, 0, fileData, rd);
		fprintf(stderr, "%s", (char *) str);
		yajl_free_error(hand, str);
	}

	free(fileData);
	fclose(file);
	yajl_free(hand);
}

void process_files(int filesc, char * files[], char * output_file)
{
	struct state_j *state = malloc(sizeof(struct state_j));

	state->cur_key = 0;
	state->is_best = 0;
	state->best_started = 0;
	state->best_nest = 0;
	state->qid = NULL;
	state->qtext = NULL;
	state->atext = NULL;

	state->file = fopen(output_file, "w");

	for (int i = 0; i < filesc; i++)
	{
		process_file(files[i], state);
	}

	fclose(state->file);
	free(state);
}