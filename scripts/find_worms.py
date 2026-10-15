import csv, collections, statistics

tracks = collections.defaultdict(list)
for r in csv.DictReader(open("data/out_c02.csv")):
    if r["length"]:
        tracks[r["worm_index"]].append(
            (float(r["length"]), float(r["coord_x_body"]), float(r["coord_y_body"]))
        )

results = []
for worm, rows in tracks.items():
    length = statistics.median(row[0] for row in rows)
    xs = [row[1] for row in rows]
    ys = [row[2] for row in rows]
    moved = max(max(xs) - min(xs), max(ys) - min(ys))
    if 30 < length < 100 and moved > 20:
        results.append((len(rows), worm, round(length), round(moved)))

for frames, worm, length, moved in sorted(results, reverse=True)[:10]:
    print(f"worm {worm}: {frames} frames, length {length} px, moved {moved} px")

    print(len(tracks), "tracks total")
for worm, rows in sorted(tracks.items(), key=lambda t: -len(t[1]))[:10]:
    xs = [r[1] for r in rows]; ys = [r[2] for r in rows]
    print(worm, len(rows), "frames, length", round(statistics.median(r[0] for r in rows)),
          "moved", round(max(max(xs)-min(xs), max(ys)-min(ys))))