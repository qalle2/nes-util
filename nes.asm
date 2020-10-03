; NES assembly routines for asm6f (https://github.com/freem/asm6f). Used by many of my projects.
; For a summary of this file, try: grep "^macro" nes.asm

; --- Constants -----------------------------------------------------------------------------------

; memory-mapped registers
; see http://wiki.nesdev.com/w/index.php/PPU_registers
ppu_ctrl   equ $2000
ppu_mask   equ $2001
ppu_status equ $2002
oam_addr   equ $2003
oam_data   equ $2004
ppu_scroll equ $2005
ppu_addr   equ $2006
ppu_data   equ $2007
dmc_freq   equ $4010
oam_dma    equ $4014
snd_chn    equ $4015
joypad1    equ $4016
joypad2    equ $4017

; joypad bitmasks
button_a      equ %10000000
button_b      equ %01000000
button_select equ %00100000
button_start  equ %00010000
button_up     equ %00001000
button_down   equ %00000100
button_left   equ %00000010
button_right  equ %00000001

; --- Macros --------------------------------------------------------------------------------------

; Note: start comments at column 44 (for grep "^macro").

; PPU

macro wait_for_vblank                      ; wait until in VBlank
-   bit ppu_status
    bpl -
endm

macro wait_for_vblank_start                ; wait until next VBlank starts
    bit ppu_status
-   bit ppu_status
    bpl -
endm

macro reset_ppu_address_latch              ; reset ppu_addr/ppu_scroll latch
    bit ppu_status
endm

macro set_ppu_address _address             ; _address: 16 bits
    lda #>(_address)
    sta ppu_addr
    if (<_address) != (>_address)
        lda #<(_address)
    endif
    sta ppu_addr
endm

macro set_ppu_scroll _horz, _vert          ; _horz: 8 bits, _vert: 8 bits
    lda #_horz
    sta ppu_scroll
    if (_horz) != (_vert)
        lda #_vert
    endif
    sta ppu_scroll
endm

macro copy_sprite_data _source             ; sprite data: CPU -> PPU; _source: 16 bits, $xx00
    if <(_source) != 0
        error "invalid sprite data source address"
    endif
    lda #$00
    sta oam_addr
    lda #>_source
    sta oam_dma
endm

macro initialize_nes
    ; Afterwards, wait for VBlank before doing any PPU operations.
    ; In between, you have about 30,000 cycles to do non-PPU-related stuff.
    ; See http://wiki.nesdev.com/w/index.php/Init_code

    sei           ; ignore IRQs
    cld           ; disable decimal mode
    ldx #$40
    stx joypad2   ; disable APU frame IRQ
    ldx #$ff
    txs           ; initialize stack pointer
    inx
    stx ppu_ctrl  ; disable NMI
    stx ppu_mask  ; disable rendering
    stx dmc_freq  ; disable DMC IRQs
    stx snd_chn   ; disable sound channels

    wait_vblank_start
endm

; Flags

macro clear_flag _flag                     ; clear MSB of byte
    lsr _flag
endm

macro set_flag _flag                       ; set MSB of byte
    sec
    ror _flag
endm

macro branch_if_flag_clear _flag, _target  ; branch if MSB clear
    bit _flag
    bpl _target
endm

macro branch_if_flag_set _flag, _target    ; branch if MSB set
    bit _flag
    bmi _target
endm

macro copy_via_a _source, _target          ; _source -> A -> _target
    lda _source
    sta _target
endm

; Synthetic instructions; see http://wiki.nesdev.com/w/index.php/Synthetic_instructions

macro add _operand                         ; A + _operand -> A
    clc
    adc _operand
endm

macro sub _operand                         ; A - _operand -> A
    sec
    sbc _operand
endm

macro negate_a                             ; 0 - A -> A
    eor #$ff
    add #1
endm

macro reverse_subtract_a _operand          ; _operand - A -> A
    eor #$ff
    sec
    adc _operand
endm

macro asr_a                                ; ASR A
    cmp #$80
    ror
endm

macro rol8_a                               ; 8-bit ROL A
    cmp #$80
    rol
endm

macro ror8_a                               ; 8-bit ROR A
    pha
    lsr
    pla
    ror
endm

; Misc macros

macro push_registers                       ; push A, X, Y
    pha
    txa
    pha
    tya
    pha
endm

macro pull_registers                       ; pull Y, X, A
    pla
    tay
    pla
    tax
    pla
endm

macro identity_table_macro                 ; 256 bytes, value = index
    ; see http://wiki.nesdev.com/w/index.php/Identity_table
    hex 00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f
    hex 10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f
    hex 20 21 22 23 24 25 26 27 28 29 2a 2b 2c 2d 2e 2f
    hex 30 31 32 33 34 35 36 37 38 39 3a 3b 3c 3d 3e 3f
    hex 40 41 42 43 44 45 46 47 48 49 4a 4b 4c 4d 4e 4f
    hex 50 51 52 53 54 55 56 57 58 59 5a 5b 5c 5d 5e 5f
    hex 60 61 62 63 64 65 66 67 68 69 6a 6b 6c 6d 6e 6f
    hex 70 71 72 73 74 75 76 77 78 79 7a 7b 7c 7d 7e 7f
    hex 80 81 82 83 84 85 86 87 88 89 8a 8b 8c 8d 8e 8f
    hex 90 91 92 93 94 95 96 97 98 99 9a 9b 9c 9d 9e 9f
    hex a0 a1 a2 a3 a4 a5 a6 a7 a8 a9 aa ab ac ad ae af
    hex b0 b1 b2 b3 b4 b5 b6 b7 b8 b9 ba bb bc bd be bf
    hex c0 c1 c2 c3 c4 c5 c6 c7 c8 c9 ca cb cc cd ce cf
    hex d0 d1 d2 d3 d4 d5 d6 d7 d8 d9 da db dc dd de df
    hex e0 e1 e2 e3 e4 e5 e6 e7 e8 e9 ea eb ec ed ee ef
    hex f0 f1 f2 f3 f4 f5 f6 f7 f8 f9 fa fb fc fd fe ff
endm

