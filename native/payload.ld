ENTRY(EnhancedEvolution)
SECTIONS {
    . = 0x01FF9000;
    .enhanced_config : { KEEP(*(.enhanced_config)) }
    ASSERT(SIZEOF(.enhanced_config) == 32, "Enhanced options ABI changed")
    . = 0x01FF9020;
    .trampoline : { KEEP(*(.evo_trampoline)) }
    ASSERT(SIZEOF(.trampoline) == 32, "Evolution trampoline ABI changed")
    . = 0x01FF9040;
    .text : { *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss : { *(.bss .bss.* COMMON) }
    . = ALIGN(4);
    __enhanced_end = .;
    ASSERT(__enhanced_end <= 0x02000000, "Enhanced payload exceeds ITCM")
    /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment) *(.note*) *(.eh_frame*) }
}
GetMonData = 0x0206E541;
GetItemAttr = 0x02077D89;
LoadMonEvolutionTable = 0x020725C9;
