/* Linker script for TH2.LOW lossless assembly container */
OUTPUT_FORMAT("elf32-sh")
OUTPUT_ARCH(sh:sh2)
ENTRY(_start)

SECTIONS
{
    . = 0x002DA000;

    .text : {
        _text_start = .;
        *(.text)
        *(.text.*)
        _text_end = .;
    }

    ASSERT(ADDR(.text) == 0x002DA000, "VMA of .text must be 0x002DA000")
    ASSERT(SIZEOF(.text) == 149504, "Size of .text must be exactly 149504 bytes")
    ASSERT(entry_002E9910 == 0x002E9910, "entry_002E9910 address mismatch")

    /DISCARD/ : {
        *(.comment)
        *(.note.*)
    }
}
