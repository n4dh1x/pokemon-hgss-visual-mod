.syntax unified
.cpu arm946e-s
.thumb
.section .evo_trampoline, "ax", %progbits
.balign 4
.global OriginalEvolution
.type OriginalEvolution, %function
.thumb_func
OriginalEvolution:
    /* Original GetMonEvolution's first sixteen bytes, relocated. There are
     * no PC-relative operands or branches in this audited prologue. */
    push {r4, r5, r6, r7, lr}
    sub sp, #0x44
    adds r7, r1, #0
    str r0, [sp, #0]
    str r2, [sp, #4]
    movs r6, #0
    adds r0, r7, #0
    movs r1, #5
    /* Preserve used_item in r3 and the wrapper's return address in lr. */
    push {r3}
    ldr r3, .Loriginal_resume
    mov r12, r3
    pop {r3}
    bx r12
    mov r8, r8
.Loriginal_resume:
    .word 0x02070E45
.size OriginalEvolution, .-OriginalEvolution
