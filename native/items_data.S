.section .rodata.item_pockets,"a",%progbits
.global gItemPocketTable
.type gItemPocketTable,%object
gItemPocketTable:
.incbin "item_pockets.bin"
.size gItemPocketTable, .-gItemPocketTable
