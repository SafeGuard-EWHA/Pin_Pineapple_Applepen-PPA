// AdaPath-NPU requantization shifts (auto-calibrated)
// bias files: 16-bit two-complement, accumulator domain
// requant: rounding right-shift (acc + 2^(k-1)) >> k
localparam SHIFT_CONV1 = 8;
localparam SHIFT_CONV2 = 8;
localparam SHIFT_FC_EARLY = 9;
localparam SHIFT_FC_LIGHT = 9;
localparam SHIFT_FC_FULL = 9;
