/* Linker script for bounded SH-2 recovery specimen */
ENTRY(_start)

SECTIONS
{
    . = 0x06004000;

    .text : {
        *(.text)
    }

    /DISCARD/ : {
        *(.comment)
        *(.note*)
    }
}

ASSERT(SIZEOF(.text) == 12, "Error: .text section length mismatch");
ASSERT(_start == 0x06004000, "Error: _start VMA mismatch");
ASSERT(lit_06004064 == 0x06004064, "Error: lit_06004064 VMA mismatch");
ASSERT(loc_06004012 == 0x06004012, "Error: loc_06004012 VMA mismatch");

