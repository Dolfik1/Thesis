#define _CRT_SECURE_NO_WARNINGS
#define BUF_SIZE 2048

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <yajl/yajl_parse.h>

struct state_j
{
	FILE *file;

	int cur_key;

	unsigned char * qid;
	size_t qid_len;

	unsigned char * atext;
	size_t atext_len;

	unsigned char * qtext; 
	size_t qtext_len;
};


int escape_csv(
	unsigned char *input,
	size_t input_len,
	unsigned char **output);

void write_csv_line(struct state_j * state);
int j_null(void * ctx);

int j_string(void * ctx, const unsigned char * stringVal,
	size_t stringLen);

int j_map_key(void * ctx, const unsigned char * stringVal,
	size_t stringLen);

void process_file(char * path, void * ctx);
void process_files(int filesc, char * files[], char * output_file);