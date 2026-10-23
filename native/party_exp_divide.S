.syntax unified
.cpu arm946e-s
.thumb
.section .text.EnhancedUnsignedDivide, "ax", %progbits
.balign 4
.global EnhancedUnsignedDivide
.type EnhancedUnsignedDivide, %function
.thumb_func
EnhancedUnsignedDivide:
    /* SDK division is ARM code. Explicit BLX preserves the Thumb caller. */
    push {r3, lr}
    ldr r3, .Lsdk_divide
    blx r3
    pop {r3, pc}
.balign 4
.Lsdk_divide:
    .word NativeUnsignedDivide
.size EnhancedUnsignedDivide, .-EnhancedUnsignedDivide
