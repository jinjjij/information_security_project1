import cv2

BLOCK_SIZE = 8

img = cv2.imread('clue.png')
h, w, c = img.shape
print(h, w, c)

h = 80
# nearest neighbor resize
img = cv2.resize(img, (w, h), interpolation=cv2.INTER_NEAREST)

for i in range(0, h, BLOCK_SIZE):
    for j in range(0, w):
        sub = img[i:i+BLOCK_SIZE, j]
        # 최빈값으로 채우기
        cnts = {}
        for k in range(BLOCK_SIZE):
            v = tuple(sub[k])
            if v not in cnts:
                cnts[v] = 0
            cnts[v] += 1
        most_frequent = max(cnts.items(), key=lambda x: x[1])[0]
        for k in range(BLOCK_SIZE):
            img[i+k][j][0] = most_frequent[0]
            img[i+k][j][1] = most_frequent[1]
            img[i+k][j][2] = most_frequent[2]

cv2.imwrite('clue_80.png', img)

picked_colors = set()

for i in range(23, 55):
    picked_colors.add(tuple(img[8][i]))

for i in range(102, 133):
    picked_colors.add(tuple(img[8][i]))

for i in range(179, 210):
    picked_colors.add(tuple(img[8][i]))

for i in range(257, 288):
    picked_colors.add(tuple(img[8][i]))

for i in range(334, 366):
    picked_colors.add(tuple(img[8][i]))

for i in range(h):
    for j in range(w):
        if not tuple(img[i][j]) in picked_colors:
            img[i][j][0] = 0
            img[i][j][1] = 0
            img[i][j][2] = 0

cv2.imwrite('clue_80_hue.png', img)