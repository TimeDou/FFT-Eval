"""Validate the public JSON sample format and the legal FFT input domain."""
import numpy as np

def samples(value, low, high):
    if not isinstance(value, list) or len(value) != 64:
        raise ValueError('Expected 64 [real_integer, imaginary_integer] samples')
    for pair in value:
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError('Expected pairs of integer codes')
        if any(type(x) is not int or not low <= x <= high for x in pair):
            raise ValueError('Sample is not an integer code in the permitted range')
    return np.asarray(value, dtype=np.int64)

def input_frames(document):
    frames = document.get('frames')
    if not isinstance(frames, list) or not frames:
        raise ValueError('Expected a nonempty frames list')
    names, arrays = [], []
    for frame in frames:
        name = frame['id']
        if not isinstance(name, str) or name in names:
            raise ValueError('Frame IDs must be distinct strings')
        codes = samples(frame['inputs_iq'], -16384, 16384)
        energy = float(np.mean(np.sum((codes/32768.0)**2, axis=-1)))
        if energy != 0 and energy < (1/32)**2:
            raise ValueError('Nonzero frame is below the specified complex RMS')
        names.append(name)
        arrays.append(codes)
    return names, np.asarray(arrays)
