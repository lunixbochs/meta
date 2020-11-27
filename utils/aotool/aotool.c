#/*
echo "Building ./aotool"
gcc -arch x86_64 "$0" -o aotool
exit 0
*/

#include <dlfcn.h>
#include <libgen.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>

char *vmmap() {
    char *cmd = NULL;
    asprintf(&cmd, "vmmap %d", getpid());
    FILE *f = popen(cmd, "r");
    size_t size = 10240;
    char *buf = malloc(size);
    ssize_t off = 0;
    char tmp[1025];
    while (!feof(f) && !ferror(f)) {
        size_t n = fread(tmp, 1, sizeof(tmp), f);
        if (n == 0) {
            break;
        }
        if (n > size - off - 1) {
            size += 10240;
            char *nbuf = realloc(buf, size);
            if (!nbuf) {
                perror("realloc failed");
                abort();
            }
            buf = nbuf;
        }
        memcpy(&buf[off], tmp, n);
        off += n;
        buf[off] = '\0';
    }
    fclose(f);
    return buf;
}

void dump_aot(const char *match, const char *out) {
    fprintf(stderr, "[+] Dumping AOT (%s -> %s)\n", match, out);
    char *match_aot = NULL;
    asprintf(&match_aot, "%s.aot", match);

    char *map = vmmap();
    char *lasts = NULL;
    char *line = strtok_r(map, "\n", &map);

    FILE *f = fopen(out, "w");
    while (line) {
        if (strstr(line, ".aot")) {
            uint64_t start, end;
            sscanf(line, "%*s %*s %llx-%llx", &start, &end);

            char *name = strstr(line, ".aot");
            while (*name != ' ' && *name != '/') { name--; }
            name++;

            if (strcmp(basename(name), match_aot) == 0) {
                printf("%s\n", line);
                fwrite((uint8_t *)start, 1, end - start, f);
            }
        }
        line = strtok_r(map, "\n", &map);
    }
    fclose(f);
}

char *compile(const char *path) {
    fprintf(stderr, "[+] Compiling %s\n", path);
    char *name = NULL;
    pid_t pid = fork();
    if (pid) {
        int status = 0;
        waitpid(pid, &status, 0);
        if (status != 0) {
            fprintf(stderr, "failed to compile: %d\n", status);
        }
        asprintf(&name, ".%d.dylib", pid);
    } else {
        asprintf(&name, ".%d.dylib", getpid());
        unlink(name);
        execlp("gcc", "gcc", "-shared", "-arch", "x86_64", path, "-o", name, NULL);
        fprintf(stderr, "failed to exec compiler\n");
        exit(2);
    }
    return name;
}

void disas(const char *path) {
    fprintf(stderr, "[+] Disassembling %s\n", path);
    pid_t pid = fork();
    if (pid) {
        int status = 0;
        waitpid(pid, &status, 0);
        if (status != 0) {
            fprintf(stderr, "failed to disas: %d\n", status);
        }
    } else {
        execlp("otool", "otool", "-tv", path, NULL);
        fprintf(stderr, "failed to exec disassembler\n");
        exit(2);
    }
}

void *loadlib(const char *path) {
    void *addr = dlopen(path, RTLD_NOW|RTLD_LOCAL);
    if (addr == NULL) {
        fprintf(stderr, "failed to load: %s\n", path);
        exit(2);
    }
    return addr;
}

void usage() {
    fprintf(stderr, "Usage: aotool -l <exe or dylib> <out.aot>\n");
    fprintf(stderr, "       aotool -c <file.c> <out.aot>\n");
    fprintf(stderr, "       aotool -d <file.c>\n");
    exit(1);
}

int main(int argc, char **argv) {
    if (argc < 2) { usage(); }

    if (strcmp(argv[1], "-l") == 0) {
        if (argc != 4) { usage(); }
        loadlib(argv[2]);
        dump_aot(strdup(basename(argv[2])), argv[3]);

    } else if (strcmp(argv[1], "-c") == 0) {
        if (argc != 4) { usage(); }
        char *path = compile(argv[2]);
        void *addr = dlopen(path, RTLD_NOW|RTLD_LOCAL);
        unlink(path);
        if (addr == NULL) {
            fprintf(stderr, "failed to load: %s\n", path);
            exit(2);
        }
        dump_aot(strdup(basename(path)), argv[3]);

    } else if (strcmp(argv[1], "-d") == 0) {
        if (argc != 3) { usage(); }
        char *path = compile(argv[2]);
        loadlib(path);

        char *path_aot = NULL;
        asprintf(&path_aot, "%s.aot", path);
        dump_aot(path, path_aot);
        disas(path);
        disas(path_aot);
        unlink(path);
        unlink(path_aot);
    } else {
        usage();
    }
    return 0;
}
