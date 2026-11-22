"""Exhaustive address checks of a radix-4 banking claim; no replacement FFT."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent


def bank(address):
    return (address & 3) ^ ((address >> 2) & 3) ^ ((address >> 4) & 3)


def butterfly(stage, index):
    if stage == 0:
        base, stride = index << 2, 1
    elif stage == 1:
        base, stride = ((index >> 2) << 4) | (index & 3), 4
    else:
        base, stride = index, 16
    return [base+i*stride for i in range(4)]


if __name__ == '__main__':
    allocation = [(bank(a), a & 15) for a in range(64)]
    assert len(set(allocation)) == 64
    rows = []
    for stage in range(3):
        for node in range(16):
            addresses = butterfly(stage, node)
            banks = [bank(a) for a in addresses]
            assert len(set(banks)) == 4
            rows.append(dict(stage=stage, butterfly=node, addresses=addresses, banks=banks))
    result = dict(status='PASS', original_claim='No fixed two-bit banking function can avoid conflicts across all three radix-4 stages',
        claim_supported=False, bank_function='a[1:0] XOR a[3:2] XOR a[5:4]', row_function='a[3:0]',
        unique_bank_row_pairs=len(set(allocation)), butterflies_checked=len(rows), checks=rows,
        scope='Exact combinational address-allocation counterexample only; no new RTL, synthesis, score or PPA claim')
    (ROOT/'architecture_claim_check.json').write_text(json.dumps(result, indent=2)+'\n')
    print('Claim counterexample verified: 64 unique slots, all 48 radix-4 butterflies use 4 distinct banks.')
