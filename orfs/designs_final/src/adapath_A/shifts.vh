// AdaPath-NPU requantization shifts (auto-calibrated)
// bias files: 16-bit two-complement, accumulator domain
// requant: rounding right-shift (acc + 2^(k-1)) >> k
localparam SHIFT_CONV1 = 7;
localparam SHIFT_CONV2 = 8;
localparam SHIFT_FC_EARLY = 7;
localparam SHIFT_FC_LIGHT = 7;
localparam SHIFT_FC_FULL = 8;
