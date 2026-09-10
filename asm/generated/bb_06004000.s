/* Mechanically generated SH-2 assembly for Thor 2 recovery */
/* Block: bb_06004000 | Base VMA: 0x06004000 | CPU: MASTER_SH2 */
/* Classification: CONFIRMED_CODE / EXECUTED */
/* Invariant: Real mnemonics only; raw opcode words forbidden */

    .text
    .global _start
    .global lit_06004064
    .global loc_06004012

_start:
    mov.w   @r1, r6              /* 0x06004000 [0x6611] MOV.W @R1, R6 */
    mov     r0, r15              /* 0x06004002 [0x6F03] MOV R0, R15 */
    mov.l   lit_06004064, r4     /* 0x06004004 [0xD417] MOV.L @(23,PC), R4 -> 0x06004064 */
    mov.l   @r4, r4              /* 0x06004006 [0x6442] MOV.L @R4, R4 */
    bra     loc_06004012         /* 0x06004008 [0xA003] BRA 0x06004012 */
    nop                          /* 0x0600400A [0x0009] NOP (delay slot) */

    /* Symbolic resolution relative to section origin */
    .equ lit_06004064, _start + 0x64
    .equ loc_06004012, _start + 0x12

