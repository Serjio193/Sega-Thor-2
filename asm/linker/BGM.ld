/* Linker script for BGM.BIN lossless assembly container */
OUTPUT_FORMAT("elf32-m68k")
OUTPUT_ARCH(m68k)
ENTRY(_start)

SECTIONS
{
    . = 0x00000000;

    .text : {
        _text_start = .;
        *(.text)
        *(.text.*)
        _text_end = .;
    }

    ASSERT(ADDR(.text) == 0x00000000, "VMA of .text must be 0x00000000")
    ASSERT(SIZEOF(.text) == 673792, "Size of .text must be exactly 673792 bytes")
    ASSERT(entry_m68k_00001000 == 0x00001000, "entry_m68k_00001000 address mismatch")

    /DISCARD/ : {
        *(.comment)
        *(.note.*)
    }
}
