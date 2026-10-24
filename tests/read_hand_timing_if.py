"""Read the bounded IF diagnostic; does not infer rendered-hand motion."""
import argparse, json, math, struct
from pathlib import Path

ROW = struct.Struct('<7I4xQQq24f')

def decode(path):
    data = Path(path).read_bytes()
    if len(data) < 16:
        raise ValueError('Truncated header')
    magic, version, size, count = struct.unpack_from('<4I', data)
    if (magic, version, size) != (0x46494853, 1, ROW.size) or count > 8192:
        raise ValueError('Unsupported capture')
    if len(data) != 16 + size * count:
        raise ValueError('Truncated or trailing capture data')
    # dt is a float occupying the seventh header word.
    rows = []
    for offset in range(16, len(data), size):
        r = ROW.unpack_from(data, offset)
        dt = struct.unpack_from('<f', data, offset + 24)[0]
        if not math.isfinite(dt) or not all(map(math.isfinite, r[10:])):
            raise ValueError('Non-finite timing/position')
        rows.append((r, dt))
    result = {'rows': count, 'hand_samples': [],
              'limitations': 'Physics-body positions are not the rendered mesh. Contact and held-body error is not automatically a defect.'}
    for hand in range(2):
        for phase in range(2):
            subset = [(r, dt) for r, dt in rows if r[3] == hand and r[2] == phase]
            errors = [math.dist(r[22:25], r[25:28]) for r, _ in subset]
            result['hand_samples'].append({'hand': hand, 'phase': phase, 'count': len(subset),
                'servo_to_body_max_world_units': max(errors, default=0),
                'contact_samples': sum(bool(r[5] & 1) for r, _ in subset),
                'held_samples': sum(bool(r[8]) for r, _ in subset),
                'distinct_frames': len({r[0] for r, _ in subset}),
                'distinct_steps': len({r[1] for r, _ in subset})})
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('capture')
    args = parser.parse_args()
    print(json.dumps(decode(args.capture), indent=2))
