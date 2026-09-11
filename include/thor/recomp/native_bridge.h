#ifndef THOR_NATIVE_BRIDGE_H
#define THOR_NATIVE_BRIDGE_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    THOR_NATIVE_MODE_INTERPRETER = 0,
    THOR_NATIVE_MODE_SHADOW_VERIFY = 1,
    THOR_NATIVE_MODE_NATIVE_OVERRIDE = 2
} ThorNativeMode;

typedef struct {
    uint64_t dispatch_attempts;
    uint64_t native_executed_count;
    uint64_t fallback_count;
    uint64_t shadow_match_count;
    uint64_t shadow_divergence_count;
    uint64_t ineligible_count;
    uint64_t retirements_in_replaced_interval;
} ThorNativeStats;

typedef struct {
    uint8_t (*read8)(uint32_t addr, void* user_data);
    uint16_t (*read16)(uint32_t addr, void* user_data);
    uint32_t (*read32)(uint32_t addr, void* user_data);
    void (*write8)(uint32_t addr, uint8_t val, void* user_data);
    void (*write16)(uint32_t addr, uint16_t val, void* user_data);
    void (*write32)(uint32_t addr, uint32_t val, void* user_data);
    bool (*is_slave_active)(void* user_data);
    bool (*is_dma_active)(void* user_data);
    bool (*is_irq_pending)(void* user_data);
    void* user_data;
} ThorHardwareCallbacks;

typedef struct {
    uint32_t r[16];
    uint32_t pc;
    uint32_t sr;
    uint32_t pr;
    uint32_t gbr;
    uint32_t vbr;
    uint32_t mach;
    uint32_t macl;
} ThorCpuRegs;

#define THOR_BLOCK_MASK_NONE        0x00000000u
#define THOR_BLOCK_MASK_BB_06004000  0x00000001u
#define THOR_BLOCK_MASK_BB_06004280  0x00000002u
#define THOR_BLOCK_MASK_ALL          0xFFFFFFFFu

void thor_native_init(void);
void thor_native_set_mode(ThorNativeMode mode);
ThorNativeMode thor_native_get_mode(void);
void thor_native_set_block_mask(uint32_t mask);
uint32_t thor_native_get_block_mask(void);
void thor_native_get_stats(ThorNativeStats* out_stats);
void thor_native_reset_stats(void);
bool thor_native_get_block_stats(uint32_t pc, uint64_t* out_executed, uint64_t* out_fallback);

bool thor_native_dispatch_step(
    uint32_t pc,
    ThorCpuRegs* live_regs,
    uint32_t* out_target_pc,
    uint32_t* out_cycles_advanced,
    const ThorHardwareCallbacks* hw_cb
);

/* Scalable candidate block gating API */
void thor_native_enable_pc(uint32_t pc);
void thor_native_disable_pc(uint32_t pc);
bool thor_native_is_pc_enabled(uint32_t pc);
void thor_native_enable_all_proven(void);
void thor_native_disable_all(void);

#ifdef __cplusplus
}
#endif

#endif // THOR_NATIVE_BRIDGE_H
