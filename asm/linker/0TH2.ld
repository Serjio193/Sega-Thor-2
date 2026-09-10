/* Linker script for 0TH2.BIN lossless assembly container */
OUTPUT_FORMAT("elf32-sh")
OUTPUT_ARCH(sh:sh2)
ENTRY(_start)

SECTIONS
{
    . = 0x06004000;

    .text : {
        _text_start = .;
        *(.text)
        *(.text.*)
        _text_end = .;
    }

    ASSERT(ADDR(.text) == 0x06004000, "VMA of .text must be 0x06004000")
    ASSERT(SIZEOF(.text) == 535552, "Size of .text must be exactly 535552 bytes")
    ASSERT(lit_06004064 == 0x06004064, "lit_06004064 address mismatch")
    ASSERT(loc_06004012 == 0x06004012, "loc_06004012 address mismatch")
    ASSERT(lit_0600435C == 0x0600435C, "lit_0600435C address mismatch")
    ASSERT(lit_06004360 == 0x06004360, "lit_06004360 address mismatch")
    ASSERT(lit_06004364 == 0x06004364, "lit_06004364 address mismatch")

    /DISCARD/ : {
        *(.comment)
        *(.note.*)
    }
}
