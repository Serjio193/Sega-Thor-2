/* Linker script for SET07.BIN lossless assembly container */
OUTPUT_FORMAT("elf32-sh")
OUTPUT_ARCH(sh:sh2)
ENTRY(_start)

SECTIONS
{
    . = 0x060D8000;

    .text : {
        _text_start = .;
        *(.text)
        *(.text.*)
        _text_end = .;
    }

    ASSERT(ADDR(.text) == 0x060D8000, "VMA of .text must be 0x060D8000")
    ASSERT(SIZEOF(.text) == 98304, "Size of .text must be exactly 98304 bytes")
    ASSERT(lit_060D8048 == 0x060D8048, "lit_060D8048 address mismatch")
    ASSERT(lit_060D8064 == 0x060D8064, "lit_060D8064 address mismatch")
    ASSERT(loc_060D8012 == 0x060D8012, "loc_060D8012 address mismatch")

    /DISCARD/ : {
        *(.comment)
        *(.note.*)
    }
}
