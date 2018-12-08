#include "process.h"
#include "tinydir.h"

char* get_cmd_opt(int argc, char * argv[], char * argn)
{
	for (int i = 0; i < argc; ++i)
	{
		if (strcmp(argv[i], argn) == 0 && i + 1 < argc)
		{
			return argv[i + 1];
		}
	}

	return NULL;
}

int cmd_opt_exists(int argc, char * argv[], char * argn)
{
	for (int i = 0; i < argc; ++i)
	{
		if (strcmp(argv[i], argn) == 0)
		{
			return 1;
		}
	}

	return 0;
}

char** get_all_files(char * path, int * count)
{
	tinydir_dir dir;
	tinydir_open(&dir, path);

	while (dir.has_next)
	{
		tinydir_file file;
		tinydir_readfile(&dir, &file);

		if (!file.is_dir)
		{
			(*count)++;
		}
		tinydir_next(&dir);
	}

	tinydir_close(&dir);
	tinydir_open(&dir, path);

	char** files = (char**)malloc((*count) * MAX_PATH);

	int idx = 0;
	while (dir.has_next)
	{
		tinydir_file file;
		tinydir_readfile(&dir, &file);

		if (!file.is_dir)
		{
			char * pstr = malloc(MAX_PATH);
			sprintf(pstr, "%s/%s\0", path, file.name);
			files[idx++] = pstr;
		}
		tinydir_next(&dir);
	}

	tinydir_close(&dir);
	return files;
}

int main(int argc, char * argv[])
{
	if (cmd_opt_exists(argc, argv, "--help") == 1)
	{
		printf("--help\t\t\tprint available args\n--data_dir\t\tsource data directory\n--output_file\t\toutput file path");
		return 0;
	}

	char * data_dir = get_cmd_opt(argc, argv, "--data_dir");
	char * output_file_path = get_cmd_opt(argc, argv, "--output_file");

	if (data_dir == NULL)
	{
		data_dir = "./data";
	}

	if (output_file_path == NULL)
	{
		output_file_path = "./output/output.csv";
	}

	int count = 0;
	char** f = get_all_files(data_dir, &count);
	printf("Total files count: %i\n", count);
	process_files(count, f, output_file_path);
	printf("Done!\n");

	return 0;
}