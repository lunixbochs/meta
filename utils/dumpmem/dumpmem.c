#include <mach/mach.h>
#include <mach/mach_vm.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>

void prot_mask_fill(char out[4], vm_prot_t prot) {
    memset(out, '-', 3);
    if (prot & VM_PROT_READ)    out[0] = 'r';
    if (prot & VM_PROT_WRITE)   out[1] = 'w';
    if (prot & VM_PROT_EXECUTE) out[2] = 'x';
}

void dump_mem(int pid, const char *out_path) {
    mach_port_t port;
    kern_return_t err = task_for_pid(mach_task_self(), pid, &port);
    if (err != KERN_SUCCESS) {
        // TODO: print string error
        printf("task_for_pid error\n");
        return;
    }

    mach_msg_type_number_t count;
    mach_port_t object_name;
    mach_vm_address_t address = 1, prev_address = 1;
    mach_vm_size_t vm_size;
    vm_region_basic_info_data_64_t info;

    while (1) {
        count = VM_REGION_BASIC_INFO_COUNT_64;
        err = mach_vm_region(port, &address, &vm_size, VM_REGION_BASIC_INFO_64, (vm_region_info_t)&info, &count, &object_name);
        if (err != KERN_SUCCESS) {
            printf("mach_vm_region error\n");
            return;
        }
        char prot_mask[4] = {0};
        prot_mask_fill(prot_mask, info.protection);

        prev_address = address;
        address += vm_size;

        // stop on wrap
        if (address < prev_address) {
            break;
        }

        vm_offset_t ptr;
        uint32_t size;
        if (vm_read(port, prev_address, vm_size, &ptr, &size)) {
            printf("vm_read error\n");
            return;
        }
        char *name;
        asprintf(&name, "%s/0x%llx+0x%llx.%s", out_path, prev_address, vm_size, prot_mask);
        printf("%s\n", name);

        FILE *f = fopen(name, "w");
        fwrite((void *)ptr, size, 1, f);
        fclose(f);

        vm_deallocate(port, ptr, size);
    }
    return;
}

void usage(const char *name) {
    printf("Usage: %s <pid> <output path>\n", name);
}

int main(int argc, char **argv) {
    if (argc != 3) {
        usage(argv[0]);
        return 1;
    }
    int pid = atol(argv[1]);
    if (pid <= 0) {
        usage(argv[0]);
        return 1;
    }
    if (mkdir(argv[2], 0755)) {
        fprintf(stderr, "mkdir '%s': ", argv[2]);
        perror("");
        return 1;
    };
    dump_mem(pid, argv[2]);
}
