// wescom-dpfix — 用 macOS 私有 SkyLight 接口在软件层“拔插”显示器
//
// 不用拔视频线: 把被 WindowServer 移出桌面/禁用的显示器重新接回,
// 或先 disconnect 再 connect, 强制一次显示管线重建 (软件拔插).
//
// 用法:
//   wescom-dpfix list           列出所有 CG 能看到的显示 (含 offline)
//   wescom-dpfix find           只列出 WSM 厂商的显示, 输出 "<cgid> online=<0|1>"
//   wescom-dpfix on <cgid>      把显示器接回桌面
//   wescom-dpfix off <cgid>     把显示器移出桌面 (不拔线)
//   wescom-dpfix replug <cgid>  off + 2 秒 + on (软件拔插)
//
// 私有符号: SLSConfigureDisplayIndependentOutput / SLSConfigureDisplayEnabled
// 思路来自开源项目 DisplayLatch (MIT), 本文件是精简实现.
//
// 退出码: 0 成功; 2 参数错误; 3/4/5 配置失败; 10 SkyLight 不可用.

#include <CoreGraphics/CoreGraphics.h>
#include <dlfcn.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

typedef CGError (*ConfigureBool)(CGDisplayConfigRef, CGDirectDisplayID, bool);

static ConfigureBool fIndependent = NULL;
static ConfigureBool fEnabled = NULL;

#define WSM_VENDOR 0x5E6Du

static int load_private(void) {
    void *h = dlopen("/System/Library/PrivateFrameworks/SkyLight.framework/SkyLight", RTLD_NOW);
    if (!h) return 0;
    fIndependent = (ConfigureBool)dlsym(h, "SLSConfigureDisplayIndependentOutput");
    fEnabled = (ConfigureBool)dlsym(h, "SLSConfigureDisplayEnabled");
    return fIndependent != NULL && fEnabled != NULL;
}

static int has_id(const CGDirectDisplayID *ids, int n, CGDirectDisplayID id) {
    for (int i = 0; i < n; i++) if (ids[i] == id) return 1;
    return 0;
}

// CG 在线列表 + 探测 1..64: 后者能找回被移出桌面但 CG 仍记得的显示器
static int all_ids(CGDirectDisplayID *ids) {
    int n = 0;
    uint32_t count = 0;
    CGGetOnlineDisplayList(0, NULL, &count);
    CGDirectDisplayID online[64];
    if (count > 64) count = 64;
    CGGetOnlineDisplayList(count, online, &count);
    for (uint32_t i = 0; i < count; i++) {
        if (!has_id(ids, n, online[i])) ids[n++] = online[i];
    }
    for (CGDirectDisplayID id = 1; id <= 64; id++) {
        uint32_t v = CGDisplayVendorNumber(id);
        if (v != 0 && v != 0xFFFFFFFFu && !has_id(ids, n, id)) ids[n++] = id;
    }
    return n;
}

static int cmd_list(void) {
    CGDirectDisplayID ids[128];
    int n = all_ids(ids);
    for (int i = 0; i < n; i++) {
        CGDirectDisplayID id = ids[i];
        printf("id=%u online=%d active=%d main=%d vendor=0x%08X model=0x%08X serial=%u\n",
               id, CGDisplayIsOnline(id) ? 1 : 0, CGDisplayIsActive(id) ? 1 : 0,
               CGDisplayIsMain(id) ? 1 : 0, CGDisplayVendorNumber(id),
               CGDisplayModelNumber(id), CGDisplaySerialNumber(id));
    }
    return 0;
}

static int cmd_find(void) {
    CGDirectDisplayID ids[128];
    int n = all_ids(ids);
    int found = 0;
    for (int i = 0; i < n; i++) {
        if (CGDisplayVendorNumber(ids[i]) == WSM_VENDOR) {
            printf("%u online=%d\n", ids[i], CGDisplayIsOnline(ids[i]) ? 1 : 0);
            found = 1;
        }
    }
    return found ? 0 : 1;
}

static int set_connected(CGDirectDisplayID id, bool on) {
    CGDisplayConfigRef cfg = NULL;
    if (CGBeginDisplayConfiguration(&cfg) != kCGErrorSuccess) return 3;

    bool ok = true;
    if (on) {
        // false = 不再作为独立输出 (重新加入桌面)
        if (fIndependent) ok = (fIndependent(cfg, id, false) == kCGErrorSuccess) && ok;
        if (fEnabled)     ok = (fEnabled(cfg, id, true) == kCGErrorSuccess) && ok;
    } else {
        // true = 作为独立输出 (移出桌面)
        ok = (fIndependent(cfg, id, true) == kCGErrorSuccess);
    }
    if (!ok) {
        CGCancelDisplayConfiguration(cfg);
        return 4;
    }

    // 用 session 级而不是 permanent: 万一 off 之后进程被打断(被杀/休眠),
    // 缺屏状态不会写进永久显示配置, 重新登录或重启即恢复.
    return CGCompleteDisplayConfiguration(cfg, kCGConfigureForSession) == kCGErrorSuccess ? 0 : 5;
}

int main(int argc, char **argv) {
    if (!load_private()) {
        fprintf(stderr, "SkyLight private symbols unavailable\n");
        return 10;
    }
    if (argc < 2) {
        fprintf(stderr, "usage: %s list|find|on <id>|off <id>|replug <id>\n", argv[0]);
        return 2;
    }
    if (strcmp(argv[1], "list") == 0) return cmd_list();
    if (strcmp(argv[1], "find") == 0) return cmd_find();

    if (argc < 3) {
        fprintf(stderr, "need display id\n");
        return 2;
    }
    CGDirectDisplayID id = (CGDirectDisplayID)strtoul(argv[2], NULL, 10);
    if (id == 0) return 2;

    if (strcmp(argv[1], "on") == 0) return set_connected(id, true);
    if (strcmp(argv[1], "off") == 0) return set_connected(id, false);
    if (strcmp(argv[1], "replug") == 0) {
        int r = set_connected(id, false);
        if (r != 0) return r;
        sleep(2);
        r = set_connected(id, true);
        if (r != 0) return r;
        sleep(2);
        return 0;
    }
    fprintf(stderr, "unknown command '%s'\n", argv[1]);
    return 2;
}
