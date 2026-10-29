.syntax unified
.cpu arm946e-s
.thumb
.section .text.money_original,"ax",%progbits
.balign 4
.global OriginalMoneyRead
.type OriginalMoneyRead,%function
.thumb_func
OriginalMoneyRead:
    ldr r0, [r0, #20]
    bx lr
.size OriginalMoneyRead, .-OriginalMoneyRead

/* Exact original USA setter, including its PC-relative cap literal. Word
 * alignment preserves its original branch and literal-load encodings. */
.balign 4
.global OriginalMoneySet
.type OriginalMoneySet,%function
.thumb_func
OriginalMoneySet:
    ldr r2, .Lmax_money
    cmp r1, r2
    bls .Lmoney_in_range
    adds r1, r2, #0
.Lmoney_in_range:
    str r1, [r0, #20]
    adds r0, r1, #0
    bx lr
    mov r8, r8
.Lmax_money:
    .word 999999
.size OriginalMoneySet, .-OriginalMoneySet
